#!/usr/bin/env python3
"""로컬 CPU 기반 보이스피싱 사건 분할·전사·화자 역할 구조화."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
import wave
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


MEDIA_EXTENSIONS = {".mp3", ".mp4"}
OPENING_RE = re.compile(
    r"(여보세요|안녕하세요|고객님.{0,12}(맞으|되시|본인)|(?:검찰|경찰|금융감독원|은행|캐피탈).{0,18}(입니다|인데요)|성함.{0,8}(확인|맞으))"
)
OFFENDER_TERMS = {
    "수사": 2.0, "검찰": 2.5, "경찰": 2.0, "사건": 1.2, "명의도용": 2.2,
    "대출": 1.5, "상환": 1.5, "신용등급": 2.0, "저금리": 2.0, "대환": 2.0,
    "계좌": 0.8, "비밀번호": 2.5, "보안카드": 2.5, "인증번호": 2.5,
    "송금": 2.0, "이체": 1.5, "현금": 1.2, "ATM": 2.0, "어플": 1.2,
    "통장": 2.0, "임대": 2.2, "대포통장": 3.0, "고객님": 0.8,
    "의향": 1.0, "접수": 0.8, "심사": 1.0,
    "확인해드": 1.0, "진행해드": 1.0, "안내해드": 1.0, "녹취": 1.0,
}
VICTIM_TERMS = {
    "왜요": 1.4, "무슨": 1.0, "모르겠": 1.5, "없는데": 1.2, "안 했": 1.2,
    "못 믿": 2.0, "사기": 1.0, "싫어요": 1.5, "어떻게": 0.8, "정말요": 0.8,
}


@dataclass
class Turn:
    start: float
    end: float
    text: str
    speaker_id: str = ""
    role: str = ""
    role_confidence: float = 0.0
    voice_modified: bool | None = None
    avg_logprob: float | None = None


def locate_ffmpeg() -> str:
    direct = shutil.which("ffmpeg")
    if direct:
        return direct
    roots = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    matches = sorted(roots.glob("Gyan.FFmpeg_*/*/bin/ffmpeg.exe")) if roots.exists() else []
    if matches:
        return str(matches[-1])
    raise FileNotFoundError("ffmpeg를 찾을 수 없습니다. 새 PowerShell을 열거나 FFmpeg 경로를 확인하세요.")


def media_files(root: Path) -> list[Path]:
    return sorted(
        (p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in MEDIA_EXTENSIONS),
        key=lambda p: str(p).lower(),
    )


def convert_audio(source: Path, target: Path, ffmpeg: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
         "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(target)],
        check=True,
    )


def load_waveform(path: Path):
    import numpy as np
    import torch
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        rate = handle.getframerate()
        width = handle.getsampwidth()
        raw = handle.readframes(handle.getnframes())
    if channels != 1 or rate != 16000 or width != 2:
        raise ValueError(f"예상하지 못한 WAV 형식: channels={channels}, rate={rate}, width={width}")
    samples = np.frombuffer(raw, dtype="<i2").astype("float32") / 32768.0
    return {"waveform": torch.from_numpy(samples).unsqueeze(0), "sample_rate": rate}


def transcribe(model: Any, wav_path: Path) -> tuple[list[Turn], dict[str, Any]]:
    segments, info = model.transcribe(
        str(wav_path), language="ko", task="transcribe", beam_size=5,
        vad_filter=True, vad_parameters={"min_silence_duration_ms": 500},
        word_timestamps=True, condition_on_previous_text=True,
    )
    turns = [
        Turn(
            start=round(float(seg.start), 3), end=round(float(seg.end), 3),
            text=seg.text.strip(), avg_logprob=round(float(seg.avg_logprob), 4),
        )
        for seg in segments if seg.text.strip()
    ]
    meta = {
        "language": info.language,
        "language_probability": round(float(info.language_probability), 4),
        "duration": round(float(info.duration), 3),
    }
    return turns, meta


def detect_case_ranges(turns: list[Turn], duration: float) -> list[tuple[float, float, str]]:
    """긴 무음과 재도입 문구를 보수적으로 사용해 사건 후보 경계를 만든다."""
    if not turns:
        return [(0.0, duration, "no_speech")]
    cuts = [0.0]
    reasons: dict[float, str] = {0.0: "file_start"}
    last_cut = 0.0
    for previous, current in zip(turns, turns[1:]):
        gap = current.start - previous.end
        elapsed = current.start - last_cut
        reason = ""
        if gap >= 6.0 and elapsed >= 20.0:
            reason = "long_silence"
        elif gap >= 1.2 and elapsed >= 45.0 and OPENING_RE.search(current.text):
            reason = "new_call_opening"
        if reason:
            cut = round((previous.end + current.start) / 2, 3)
            cuts.append(cut)
            reasons[cut] = reason
            last_cut = cut
    cuts.append(duration)
    return [(cuts[i], cuts[i + 1], reasons.get(cuts[i], "detected")) for i in range(len(cuts) - 1)]


def diarize(pipeline: Any, wav_path: Path) -> list[tuple[float, float, str]]:
    output = pipeline(load_waveform(wav_path), min_speakers=1, max_speakers=5)
    annotation = getattr(output, "speaker_diarization", output)
    return [
        (float(segment.start), float(segment.end), str(label))
        for segment, _, label in annotation.itertracks(yield_label=True)
    ]


def assign_speakers(turns: list[Turn], diarization: list[tuple[float, float, str]]) -> None:
    for turn in turns:
        overlap: dict[str, float] = defaultdict(float)
        for start, end, speaker in diarization:
            amount = max(0.0, min(turn.end, end) - max(turn.start, start))
            overlap[speaker] += amount
        if overlap:
            turn.speaker_id = max(overlap, key=overlap.get)


def term_score(text: str, terms: dict[str, float]) -> float:
    return sum(weight * text.count(term) for term, weight in terms.items())


def assign_roles(case_turns: list[Turn]) -> dict[str, dict[str, Any]]:
    texts: dict[str, str] = defaultdict(str)
    for turn in case_turns:
        texts[turn.speaker_id] += " " + turn.text
    speakers = [speaker for speaker in texts if speaker]
    scores = {
        speaker: {
            "offender": term_score(texts[speaker], OFFENDER_TERMS),
            "victim": term_score(texts[speaker], VICTIM_TERMS),
        }
        for speaker in speakers
    }
    offender = max(speakers, key=lambda s: scores[s]["offender"] - scores[s]["victim"], default=None)
    offender_margin = (
        scores[offender]["offender"] - scores[offender]["victim"] if offender else 0.0
    )
    mapping: dict[str, dict[str, Any]] = {}
    for speaker in speakers:
        if speaker == offender and offender_margin >= 2.0:
            role, confidence = "OFFENDER", min(0.95, 0.55 + offender_margin / 20)
        elif speaker != offender and offender_margin >= 2.0 and len(speakers) == 2:
            role, confidence = "VICTIM", min(0.9, 0.5 + offender_margin / 25)
        else:
            role, confidence = "", 0.0
        mapping[speaker] = {"role": role, "confidence": round(confidence, 3), **scores[speaker]}
    for turn in case_turns:
        value = mapping.get(turn.speaker_id, {"role": "", "confidence": 0.0})
        turn.role = value["role"]
        turn.role_confidence = value["confidence"]
    return mapping


def stamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"


def save_result(source: Path, root: Path, output_root: Path, turns: list[Turn], meta: dict[str, Any], ranges):
    relative = source.relative_to(root)
    result_dir = output_root / relative.parent / source.stem
    result_dir.mkdir(parents=True, exist_ok=True)
    cases = []
    training_rows = []
    review_rows = []
    for index, (start, end, reason) in enumerate(ranges, 1):
        case_turns = [turn for turn in turns if turn.end > start and turn.start < end]
        roles = assign_roles(case_turns)
        case_id = f"case_{index:03d}"
        needs_review = reason != "file_start" or any(not t.role for t in case_turns)
        cases.append({
            "case_id": case_id, "start": start, "end": end,
            "boundary_reason": reason, "needs_review": needs_review,
            "speaker_roles": roles, "turns": [asdict(turn) for turn in case_turns],
        })
        for number, turn in enumerate(case_turns, 1):
            row = {
                "source_file": str(relative), "case_id": case_id, "turn_id": number,
                "start": turn.start, "end": turn.end, "speaker_id": turn.speaker_id,
                "role": turn.role, "role_confidence": turn.role_confidence,
                "voice_modified": "" if turn.voice_modified is None else turn.voice_modified,
                "text_verbatim": turn.text, "avg_logprob": turn.avg_logprob,
                "needs_review": needs_review or not turn.role or turn.role_confidence < 0.6,
            }
            if row["role"] in {"OFFENDER", "VICTIM"} and row["role_confidence"] >= 0.6:
                training_rows.append(row)
            else:
                review_rows.append(row)
    payload = {
        "schema_version": "1.0", "source_file": str(relative), "metadata": meta,
        "case_count": len(cases), "cases": cases,
        "notes": {"voice_modified": "자동 확정하지 않음. 검수 시 true/false 입력"},
    }
    (result_dir / "cases.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    all_rows = training_rows + review_rows
    fields = list(all_rows[0]) if all_rows else ["source_file", "case_id"]
    with (result_dir / "turns.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(training_rows)
    with (result_dir / "검수필요.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(review_rows)
    with (result_dir / "review.txt").open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(f"\n## {case['case_id']} {stamp(case['start'])} ~ {stamp(case['end'])} [{case['boundary_reason']}]\n")
            for turn in case["turns"]:
                role_label = turn["role"] or "검수필요"
                speaker_label = turn["speaker_id"] or "화자미분리"
                handle.write(f"[{stamp(turn['start'])}] {role_label}({speaker_label}): {turn['text']}\n")
    return result_dir


def parse_args():
    parser = argparse.ArgumentParser(description="보이스피싱 사건 단위 전사·화자분리")
    parser.add_argument("--input", type=Path, default=Path("원본 영상 및 음원"))
    parser.add_argument("--output", type=Path, default=Path("분석 결과"))
    parser.add_argument("--model", default="large-v3-turbo")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--compute-type", default="auto", help="auto, int8, float16 등")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--match", default="", help="파일 경로에 포함될 문자열(쉼표로 여러 개 지정)")
    parser.add_argument("--no-diarization", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    # CLI 로그인 토큰은 기본 Hugging Face 위치에서 먼저 읽는다. 모델 캐시만 프로젝트에 격리한다.
    from huggingface_hub import get_token
    auth_token = os.environ.get("HF_TOKEN") or get_token()
    os.environ.setdefault("MPLCONFIGDIR", str((Path.cwd() / ".cache" / "matplotlib").resolve()))
    os.environ.setdefault("HF_HOME", str((Path.cwd() / ".cache" / "huggingface").resolve()))
    from faster_whisper import WhisperModel
    import torch

    files = media_files(args.input)
    if args.match:
        needles = [value.strip().lower() for value in args.match.split(",") if value.strip()]
        files = [path for path in files if any(value in str(path).lower() for value in needles)]
    if args.limit:
        files = files[:args.limit]
    if not files:
        print("처리할 미디어 파일이 없습니다.", file=sys.stderr); return 2

    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else (
        "cpu" if args.device == "auto" else args.device
    )
    compute_type = (
        "float16" if args.compute_type == "auto" and device == "cuda"
        else "int8" if args.compute_type == "auto"
        else args.compute_type
    )
    print(f"실행 장치: {device}, compute_type: {compute_type}", flush=True)
    model = WhisperModel(
        args.model, device=device, compute_type=compute_type,
        cpu_threads=max(1, (os.cpu_count() or 4) - 1),
    )
    diarization_pipeline = None
    if not args.no_diarization:
        if not auth_token:
            print("Hugging Face 로그인이 없어 화자분리를 생략합니다. 전사는 계속 진행합니다.", file=sys.stderr)
        else:
            from pyannote.audio import Pipeline
            diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-community-1", token=auth_token
            )
            diarization_pipeline.to(torch.device(device))

    ffmpeg = locate_ffmpeg()
    run_manifest = []
    for number, source in enumerate(files, 1):
        relative = source.relative_to(args.input)
        final_json = args.output / relative.parent / source.stem / "cases.json"
        if final_json.exists() and not args.force:
            print(f"[{number}/{len(files)}] 기존 결과: {relative}")
            continue
        wav = args.output / ".cache_audio" / relative.with_suffix(".wav")
        started = time.time()
        try:
            print(f"[{number}/{len(files)}] 변환/전사: {relative}", flush=True)
            convert_audio(source, wav, ffmpeg)
            turns, meta = transcribe(model, wav)
            ranges = detect_case_ranges(turns, meta["duration"])
            if diarization_pipeline:
                assign_speakers(turns, diarize(diarization_pipeline, wav))
            result_dir = save_result(source, args.input, args.output, turns, meta, ranges)
            status, error = "success", ""
            print(f"  사건 후보 {len(ranges)}개, 발화 {len(turns)}개, {time.time()-started:.1f}초", flush=True)
        except Exception as exc:
            status, error, result_dir = "error", repr(exc), ""
            print(f"  오류: {exc}", file=sys.stderr, flush=True)
        finally:
            wav.unlink(missing_ok=True)
        run_manifest.append({"source_file": str(relative), "status": status, "result_dir": str(result_dir), "error": error})
        args.output.mkdir(parents=True, exist_ok=True)
        with (args.output / "run_manifest.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(run_manifest[-1], ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
