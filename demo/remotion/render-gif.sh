#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
input_file="$project_dir/../../assets/ip-strategist-demo.mp4"
output_file="$project_dir/../../assets/ip-strategist-demo.gif"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required to generate the README GIF." >&2
  exit 1
fi

ffmpeg -y -i "$input_file" \
  -vf "fps=12,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" \
  -loop 0 "$output_file"
