import subprocess
from pathlib import Path
import argparse

def merge_video_clips(input_folder, output_folder):
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True)

    for video_folder in sorted(input_path.iterdir()):
        if not video_folder.is_dir():
            continue

        clip_files = sorted(
            [f for f in video_folder.iterdir() if f.name.endswith(".mp4")],
            key=lambda x: x.name
        )

        if not clip_files:
            print(f"No valid clips found in {video_folder.name}, skipping.")
            continue

        list_file = video_folder / "file_list.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for clip in clip_files:
                f.write(f"file '{clip.resolve()}'\n")

        output_file = output_path / f"{video_folder.name}.mp4"

        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_file)
        ]

        print(f"🎬 Merging {video_folder.name} using ffmpeg...")
        try:
            subprocess.run(cmd, check=True)
            print(f"Saved merged video to {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error merging {video_folder.name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge sequential video clips into full videos.")
    parser.add_argument("--input", required=True, help="Input root directory containing video subfolders.")
    parser.add_argument("--output", required=True, help="Output directory for merged videos.")

    args = parser.parse_args()

    merge_video_clips(args.input, args.output)