#!/usr/bin/env bash
# Lay the make.fun brand badge + press-pack referral end card over clip.mp4.
# Follows the press kit's own guide (https://make.fun/press/llms.txt):
#  - badge from frame 0 until the end card comes in
#  - transparent 16:9 card over the last 2.5 s, clip blurring ~28 px and
#    desaturating over ~0.8 s as the card arrives
#  - referral code typed into the field once it rests (1.433 s into the card),
#    JetBrains Mono Bold 62 px, ink #191419, caret covered white first
# Numbers are the manifest's 16:9 field (1920x1080): field x373 y637,
# caret x432 y694 5x77, code centred on y733.
set -euo pipefail
cd "$(dirname "$0")"
CLIP=clip.mp4
CARD=press/makefun-card-16x9-transparent.webm
BADGE=press/makefun-badge-16x9.png
FONT=press/JetBrainsMono-Bold.ttf
CODE=yxet3dyv
LEN=2.5
REST=1.433
CX=432 CY=694 CW=5 CH=77 MID=733 SIZE=62
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$CLIP")
T=$(awk "BEGIN{print $D-$LEN}")
echo "clip duration $D s, card starts at $T s"
ffmpeg -y -v error \
  -i "$CLIP" -c:v libvpx-vp9 -i "$CARD" -loop 1 -t "$D" -i "$BADGE" \
  -filter_complex "\
[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps=60,format=yuva420p,split[clip][soft];\
[soft]gblur=sigma=28,eq=saturation=0.35,fade=t=in:st=$T:d=0.8:alpha=1[soft];\
[clip][soft]overlay[bg];\
[1:v]format=yuva420p,setpts=PTS-STARTPTS+$T/TB[card];\
[bg][card]overlay=eof_action=pass,\
drawbox=x=$CX-2:y=$CY-2:w=$CW+4:h=$CH+4:color=white:t=fill:enable='gte(t,$T+$REST)',\
drawtext=fontfile=$FONT:text=$CODE:fontsize=$SIZE:fontcolor=0x191419:x=$CX:y=$MID-(ascent-descent)/2:enable='gte(t,$T+$REST)'[v0];\
[2:v]format=yuva420p[badge];\
[v0][badge]overlay=enable='lt(t,$T)'[v]" \
  -map '[v]' -map '0:a' -c:v libx264 -pix_fmt yuv420p -crf 18 \
  -c:a aac -movflags +faststart video.mp4
echo "video.mp4 done"
ffprobe -v error -show_entries format=duration,size \
  -show_entries stream=width,height,r_frame_rate,codec_name \
  -of default=noprint_wrappers=1 video.mp4
