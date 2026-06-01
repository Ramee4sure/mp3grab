from __future__ import annotations

import os
import sys
from pathlib import Path

import ffmpeg

VIDEO_EXTS = {".mp4", ".mkv", ".webm"}


def configure_ffmpeg_binary() -> None:
    """
    If ffmpeg.exe is bundled (PyInstaller --add-binary), point ffmpeg-python to it.
    """
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    ffmpeg_exe = base / "ffmpeg.exe"
    if ffmpeg_exe.exists():
        os.environ["FFMPEG_BINARY"] = str(ffmpeg_exe)


def next_available_path(path: Path) -> Path:
    """
    If the output exists, generate 'name (1).ext', 'name (2).ext', ...
    """
    if not path.exists():
        return path

    stem, suffix = path.stem, path.suffix
    i = 1
    while True:
        candidate = path.with_name(f"{stem} ({i}){suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def convert_one(video_path: Path, out_mp3_path: Path) -> None:
    out_mp3_path.parent.mkdir(parents=True, exist_ok=True)

    (
        ffmpeg
        .input(str(video_path))
        .output(
            str(out_mp3_path),
            vn=None,
            acodec="libmp3lame",
            **{"q:a": 2},  # VBR quality (0 best, 2 very good)
        )
        .overwrite_output()
        .run(quiet=True)
    )


def convert_folder_to_subfolder(in_dir: Path, out_subfolder_name: str = "audio") -> None:
    out_dir = in_dir / out_subfolder_name
    out_dir.mkdir(parents=True, exist_ok=True)

    for p in in_dir.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in VIDEO_EXTS:
            continue

        # Avoid processing files inside the output folder itself
        if out_dir in p.parents:
            continue

        desired = out_dir / f"{p.stem}.mp3"
        out_mp3 = next_available_path(desired)  # auto-rename always on

        print(f"Converting: {p.name} -> {out_mp3.name}")
        try:
            convert_one(p, out_mp3)
        except ffmpeg.Error:
            # Keep going on errors; show a simple message
            print(f"FAILED: {p}")

    print(f"\nDone. MP3 files are in: {out_dir}")


def main() -> None:
    configure_ffmpeg_binary()

    # Drag-and-drop provides argv[1] = dropped path (folder)
    if len(sys.argv) < 2:
        print("Drag and drop a FOLDER onto this app to convert videos to MP3.")
        input("Press Enter to exit...")
        return

    dropped = Path(sys.argv[1]).expanduser()

    if not dropped.exists():
        print(f"Path not found: {dropped}")
        input("Press Enter to exit...")
        return

    if dropped.is_file():
        print("You dropped a file. Please drop a FOLDER.")
        print(f"File: {dropped}")
        input("Press Enter to exit...")
        return

    convert_folder_to_subfolder(dropped, out_subfolder_name="audio")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
    