#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ffmpeg -y -v error -i audio/narration_master.flac -ac 1 -ar 48000 -c:a pcm_s16le audio/narration_master.wav
