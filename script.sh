#!/bin/bash

AUDIO_FILE="/home/vedsaga/Downloads/amazon-ai-agent-hackathon.mp3"
VIDEO_FILE="/home/vedsaga/Downloads/screen-recorder-thu-oct-23-2025-05-22-52.webm"
OUTPUT_FILE="/home/vedsaga/Downloads/output_synced.mp4"

# Get audio duration
AUDIO_DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$AUDIO_FILE")

# Get video duration - use stream duration for WebM files
VIDEO_DURATION=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 "$VIDEO_FILE")

# If still N/A, decode the video to get duration
if [ "$VIDEO_DURATION" == "N/A" ] || [ -z "$VIDEO_DURATION" ]; then
    echo "Calculating video duration by decoding..."
    VIDEO_DURATION=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,r_frame_rate -of default=noprint_wrappers=1 "$VIDEO_FILE" | awk -F= '{if($1=="nb_read_frames") frames=$2; if($1=="r_frame_rate") {split($2,a,"/"); fps=a[1]/a[2]}} END {print frames/fps}')
fi

# Calculate gap duration using awk (instead of bc)
GAP_DURATION=$(awk "BEGIN {print $AUDIO_DURATION - $VIDEO_DURATION}")

echo "Audio Duration: $AUDIO_DURATION seconds"
echo "Video Duration: $VIDEO_DURATION seconds"
echo "Gap Duration: $GAP_DURATION seconds"

# Extract a frame with actual content (trying frame at 1 second to avoid blank frames)
ffmpeg -ss 1 -i "$VIDEO_FILE" -vframes 1 -update 1 -y /tmp/freeze_frame.png

# Create the synchronized video with frozen frame at the beginning
ffmpeg -loop 1 -framerate 30 -t "$GAP_DURATION" -i /tmp/freeze_frame.png \
       -i "$VIDEO_FILE" \
       -i "$AUDIO_FILE" \
       -filter_complex "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[frozen]; \
                        [1:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[video]; \
                        [frozen][video]concat=n=2:v=1:a=0[outv]" \
       -map "[outv]" -map 2:a \
       -c:v libx264 -preset medium -crf 23 \
       -c:a aac -b:a 192k \
       -shortest \
       -y "$OUTPUT_FILE"

# Clean up temporary frame
rm /tmp/freeze_frame.png

echo "Output saved to: $OUTPUT_FILE"