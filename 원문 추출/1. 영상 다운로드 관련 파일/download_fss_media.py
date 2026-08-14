#!/usr/bin/env python3
"""금융감독원 보이스피싱 체험관의 공개 MP3/MP4 일괄 다운로드 도구."""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen


BASE_URL = "https://www.fss.or.kr"
BOARDS = (
    ("바로 이 목소리", "B0000203", "200686"),
    ("그놈 목소리 - 대출사기형", "B0000206", "200690"),
    ("그놈 목소리 - 수사기관형", "B0000207", "200691"),
)
MEDIA_EXTENSIONS = {".mp3", ".mp4"}
USER_AGENT = "Mozilla/5.0 (compatible; FSS-public-media-archiver/1.0)"


@dataclass(frozen=True)
class Post:
    category: str
    board_id: str
    menu_no: str
    post_id: str
    title: str
    url: str


def request(url: str, *, retries: int = 3, timeout: int = 60):
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=timeout)
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(attempt * 2)
    assert last_error is not None
    raise last_error


def fetch_html(url: str) -> str:
    with request(url) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def plain_text(fragment: str) -> str:
    value = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def safe_name(value: str, limit: int = 110) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return (value or "제목없음")[:limit].rstrip(" .")


def list_url(board_id: str, menu_no: str, page: int) -> str:
    return f"{BASE_URL}/fss/bbs/{board_id}/list.do?menuNo={menu_no}&pageIndex={page}"


def find_posts(category: str, board_id: str, menu_no: str, page: int) -> list[Post]:
    source_url = list_url(board_id, menu_no, page)
    source = fetch_html(source_url)
    pattern = re.compile(
        rf'<a\b[^>]*href=["\'](?P<href>[^"\']*/{board_id}/view\.do\?[^"\']*nttId=(?P<id>\d+)[^"\']*)["\'][^>]*>(?P<title>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    found: list[Post] = []
    seen: set[str] = set()
    for match in pattern.finditer(source):
        post_id = match.group("id")
        if post_id in seen:
            continue
        seen.add(post_id)
        found.append(
            Post(
                category=category,
                board_id=board_id,
                menu_no=menu_no,
                post_id=post_id,
                title=plain_text(match.group("title")),
                url=urljoin(BASE_URL, html.unescape(match.group("href"))),
            )
        )
    return found


def media_urls(detail_html: str) -> list[str]:
    attrs = re.findall(
        r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', detail_html, re.IGNORECASE
    )
    values = [html.unescape(value.strip()) for value in attrs]
    endpoint = [
        value
        for value in values
        if "apiVodDownload.do" in value or "fileDown.do" in value
    ]
    if endpoint:
        return list(dict.fromkeys(urljoin(BASE_URL, value) for value in endpoint))

    direct = [
        value
        for value in values
        if Path(urlparse(value).path).suffix.lower() in MEDIA_EXTENSIONS
    ]
    return list(dict.fromkeys(urljoin(BASE_URL, value) for value in direct))


def disposition_filename(header: str | None) -> str | None:
    if not header:
        return None
    encoded = re.search(r"filename\*\s*=\s*UTF-8''([^;]+)", header, re.IGNORECASE)
    if encoded:
        return unquote(encoded.group(1).strip().strip('"'))
    basic = re.search(r'filename\s*=\s*(?:"([^"]+)"|([^;]+))', header, re.IGNORECASE)
    if basic:
        raw = (basic.group(1) or basic.group(2)).strip()
        try:
            return raw.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return raw
    return None


def download_media(url: str, folder: Path, post: Post, index: int) -> tuple[str, str]:
    with request(url) as response:
        header_name = disposition_filename(response.headers.get("Content-Disposition"))
        url_name = Path(unquote(urlparse(response.geturl()).path)).name
        original = header_name or url_name or f"media_{index}"
        extension = Path(original).suffix.lower()
        content_type = response.headers.get_content_type().lower()
        if extension not in MEDIA_EXTENSIONS:
            inferred = ".mp4" if content_type == "video/mp4" else ".mp3" if content_type in {
                "audio/mpeg", "audio/mp3"
            } else ""
            if not inferred:
                return "건너뜀", f"MP3/MP4 아님: {original} ({content_type})"
            extension = inferred

        destination = folder / (
            f"{post.post_id}_{safe_name(post.title)}"
            f"{f'_{index}' if index > 1 else ''}{extension}"
        )
        if destination.exists() and destination.stat().st_size > 0:
            return "기존파일", str(destination)

        temporary = destination.with_suffix(destination.suffix + ".part")
        with temporary.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
        temporary.replace(destination)
        return "다운로드", str(destination)


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["분류", "게시글ID", "제목", "게시글URL", "미디어URL", "상태", "파일", "오류"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="금융감독원 보이스피싱 공개 음원·영상 일괄 다운로드")
    parser.add_argument("--output", type=Path, default=Path("원본 영상 및 음원"))
    parser.add_argument("--delay", type=float, default=0.6, help="요청 사이 대기시간(초)")
    parser.add_argument("--max-pages", type=int, default=0, help="게시판별 최대 페이지(0=끝까지)")
    parser.add_argument("--dry-run", action="store_true", help="목록만 확인하고 파일은 받지 않음")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    total_posts = 0

    for category, board_id, menu_no in BOARDS:
        folder = args.output / safe_name(category)
        folder.mkdir(parents=True, exist_ok=True)
        seen_posts: set[str] = set()
        page = 1
        print(f"\n[{category}]")

        while not args.max_pages or page <= args.max_pages:
            try:
                posts = find_posts(category, board_id, menu_no, page)
            except Exception as exc:  # 개별 게시판 오류를 기록하고 다음 게시판 진행
                print(f"  목록 {page}페이지 오류: {exc}", file=sys.stderr)
                break
            new_posts = [post for post in posts if post.post_id not in seen_posts]
            if not new_posts:
                break
            print(f"  {page}페이지: 게시글 {len(new_posts)}개")

            for post in new_posts:
                seen_posts.add(post.post_id)
                total_posts += 1
                base_row = {
                    "분류": category,
                    "게시글ID": post.post_id,
                    "제목": post.title,
                    "게시글URL": post.url,
                    "미디어URL": "",
                    "상태": "",
                    "파일": "",
                    "오류": "",
                }
                try:
                    detail = fetch_html(post.url)
                    urls = media_urls(detail)
                    if not urls:
                        rows.append({**base_row, "상태": "미디어없음"})
                    for index, media_url in enumerate(urls, 1):
                        row = {**base_row, "미디어URL": media_url}
                        if args.dry_run:
                            rows.append({**row, "상태": "확인"})
                        else:
                            status, result = download_media(media_url, folder, post, index)
                            if status == "건너뜀":
                                rows.append({**row, "상태": status, "오류": result})
                            else:
                                rows.append({**row, "상태": status, "파일": result})
                except Exception as exc:
                    rows.append({**base_row, "상태": "오류", "오류": str(exc)})
                    print(f"    오류 {post.post_id}: {exc}", file=sys.stderr)
                write_manifest(args.output / "다운로드_목록.csv", rows)
                time.sleep(max(0.0, args.delay))
            page += 1
            time.sleep(max(0.0, args.delay))

    write_manifest(args.output / "다운로드_목록.csv", rows)
    print(f"\n완료: 게시글 {total_posts}개, 기록 {len(rows)}건")
    print(f"목록: {args.output / '다운로드_목록.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
