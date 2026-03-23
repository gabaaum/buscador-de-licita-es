#!/usr/bin/env python3
"""CLI YouTube downloader usando yt-dlp (sem Tkinter)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yt_dlp

DEFAULT_URL = "https://www.youtube.com/watch?v=S9uPNppGsGo&list=PLHz_AreHm4dlKP6QQCekuIPky1CiwmdI6"
DEFAULT_OUTPUT = "/home/gabriel/Downloads"

TOKENS_USED = 2000
ESTIMATED_COST_USD = 0.015


def estimate_cost(tokens: int = TOKENS_USED, cost: float = ESTIMATED_COST_USD) -> str:
    return f"Est. geração: {tokens} tokens ≈ ${cost:.3f}"


def _progress_hook(data: dict) -> None:
    status = data.get("status")
    if status == "downloading":
        pct = data.get("_percent_str", "0% ").strip()
        speed = data.get("_speed_str", "").strip()
        eta = data.get("_eta_str", "").strip()
        parts = [f"Baixando {pct}"]
        if speed:
            parts.append(f"@ {speed}")
        if eta:
            parts.append(f"ETA {eta}")
        print(" • ".join(parts), end="\r", flush=True)
    elif status == "finished":
        print("\nFinalizando (ffmpeg)...", flush=True)


def download(url: str, folder: Path, fmt: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    outtmpl = str(folder / "%(title)s.%(ext)s")
    opts = {
        "format": fmt,
        "outtmpl": outtmpl,
        "postprocessors": [
            {
                "key": "FFmpegVideoRemuxer",
                "preferedformat": "mp4",
            }
        ],
        "progress_hooks": [_progress_hook],
        "quiet": True,
        "ignoreerrors": True,
        "overwrites": "continue",
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Baixar vídeos do YouTube com yt-dlp (CLI)")
    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help=f"URL do vídeo ou playlist (padrão: {DEFAULT_URL})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Pasta de destino (padrão: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "-f",
        "--format",
        default="bestvideo+bestaudio/best",
        help="Formato yt-dlp (padrão: bestvideo+bestaudio/best)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    url = (args.url or DEFAULT_URL).strip()
    if not url:
        print("Erro: informe uma URL.", file=sys.stderr)
        return 1

    folder = Path(args.output).expanduser().resolve()
    try:
        download(url, folder, args.format)
    except Exception as exc:  # pragma: no cover
        print(f"Erro ao baixar: {exc}", file=sys.stderr)
        return 1
    else:
        print("\nConcluído.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
