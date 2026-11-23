#!/usr/bin/env python3
"""Render the X video for post-x-the-agent-builds-a-game-from-20261122-1709.

A 32 s, 1920x1080, 30 fps clip, drawn frame by frame with PIL and piped
straight into ffmpeg (no intermediate PNGs). Five scenes:

  0-3 s    hook: ONE PROMPT. ONE GAME.
  3-8 s    the prompt, typed out in a chat bubble
  8-16 s   the agent working: terminal, code lines landing, build complete
  16-27 s  the finished game running in a browser window (star catcher)
  27-32 s  game over + "Come build on make.fun" (the press-pack referral
           end card is laid over the last 2.5 s by ffmpeg afterwards)

The gameplay is a deterministic simulation of the real game in game.html:
same rules (stars fall, paddle catches them, score counts), same colours.
Audio is a small synthesized chiptune loop (numpy, no samples).

Usage: python3 make_video.py   -> writes clip.mp4 (no badge, no end card)
Then finalize.sh lays the badge + press-pack end card over it -> video.mp4
"""
import math
import random
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
DUR = 32.0
NFRAMES = int(DUR * FPS)

BG = (14, 10, 19)
PANEL = (27, 20, 38)
PANEL2 = (38, 28, 56)
MAGENTA = (196, 28, 131)
WHITE = (255, 255, 255)
MUTED = (185, 168, 201)
YELLOW = (255, 210, 63)
CYAN = (53, 224, 210)
GREEN = (61, 220, 132)
INK = (25, 20, 25)

FONT = "press/JetBrainsMono-Bold.ttf"


def font(size):
    return ImageFont.truetype(FONT, size)


def text(draw, xy, s, f, fill, anchor="la"):
    draw.text(xy, s, font=font(f), fill=fill, anchor=anchor)


def centre(draw, y, s, size, fill, x=W // 2):
    draw.text((x, y), s, font=font(size), fill=fill, anchor="ma")


def rrect(draw, box, rad, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=rad, fill=fill, outline=outline, width=width)


def fade_in(frame, t0, span=0.5):
    """Alpha 0..1 ramp for an element that appears at t0 (seconds)."""
    return max(0.0, min(1.0, (frame / FPS - t0) / span))


def blend(base, colour, alpha):
    return tuple(int(base[i] * (1 - alpha) + colour[i] * alpha) for i in range(3))


# ---------------------------------------------------------------- prompt scene
PROMPT = ("Build me a tiny browser game: catch the falling stars. "
          "60 seconds on the clock, points for every star, "
          "game-over screen at the end.")


def wrap(draw, s, f, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font(f)) <= maxw:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------- gameplay simulation
# Deterministic: same seed every run, same stars, same score.
rng = random.Random(7)
GAME_T0 = 16.0          # gameplay scene starts (s)
GAME_FRAMES = int(11 * FPS)
PADDLE_Y = 960
PADDLE_W = 220
stars = []              # dicts: x, y, v, r, born(frame), caught(frame|None)
bursts = []             # dicts: x, y, frame
snapshots = []          # per frame: {"paddle": x, "stars": [(x, y, r, state)]}
paddle_x = (W - PADDLE_W) / 2
score = 4
score_at = {}           # frame -> score after that frame
time_at = {}            # frame -> seconds left on the clock
for f in range(GAME_FRAMES):
    if f % 24 == 0:
        stars.append({"x": rng.uniform(120, W - 120), "y": 90,
                      "v": rng.uniform(10.5, 14.5), "r": rng.uniform(22, 34),
                      "born": f, "caught": None, "missed": False})
    # Paddle chases the live star nearest the paddle (largest y).
    live = [s for s in stars if s["caught"] is None and not s["missed"]]
    if live:
        target = max(live, key=lambda s: s["y"])["x"] - PADDLE_W / 2
        paddle_x += (target - paddle_x) * 0.20
        paddle_x = max(0, min(W - PADDLE_W, paddle_x))
    for s in stars:
        if s["caught"] is not None:
            continue
        s["y"] += s["v"]
        if s["y"] >= PADDLE_Y and not s["missed"]:
            cx = paddle_x + PADDLE_W / 2
            if abs(s["x"] - cx) < PADDLE_W / 2 + 30:
                s["caught"] = f
                score += 1
                bursts.append({"x": s["x"], "y": PADDLE_Y, "frame": f})
            else:
                s["missed"] = True
    score_at[f] = score
    time_at[f] = 52 - f // FPS
    snapshots.append({
        "paddle": paddle_x,
        "stars": [(s["x"], s["y"], s["r"],
                   "caught" if s["caught"] is not None and f - s["caught"] <= 2
                   else "gone" if s["caught"] is not None
                   else "missed" if s["missed"] and s["y"] > H + 40
                   else "live")
                  for s in stars if s["born"] <= f],
    })
FINAL_SCORE = score
FINAL_CAUGHT = sum(1 for s in stars if s["caught"] is not None)
print(f"sim: final score {FINAL_SCORE}, stars caught {FINAL_CAUGHT}, "
      f"spawned {len(stars)}", flush=True)


def draw_star(draw, x, y, r, rot=0.0, fill=YELLOW):
    pts = []
    for i in range(8):
        ang = rot + i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.32
        pts.append((x + rr * math.cos(ang - math.pi / 2),
                    y + rr * math.sin(ang - math.pi / 2)))
    draw.polygon(pts, fill=fill)


# ------------------------------------------------------------------- scenes
def scene_hook(f):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=MAGENTA)
    a1 = fade_in(f, 0.15)
    if a1 > 0:
        centre(d, 300, "ONE PROMPT.", 170, blend(BG, WHITE, a1))
    a2 = fade_in(f, 1.15)
    if a2 > 0:
        centre(d, 500, "ONE GAME.", 170, blend(BG, MAGENTA, a2))
    a3 = fade_in(f, 2.0)
    if a3 > 0:
        centre(d, 760, "watch my AI agent build it — live",
               54, blend(BG, MUTED, a3))
    return img


def scene_prompt(f):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=MAGENTA)
    centre(d, 90, "THE PROMPT", 64, MUTED)
    # Chat window.
    rrect(d, [260, 220, 1660, 880], 28, fill=PANEL)
    d.rectangle([260, 220, 1660, 300], fill=PANEL2)
    text(d, (310, 245), "Sir  →  Muse", 40, WHITE)
    # Typed prompt: 4.2 s of typing over the 5 s scene.
    lf = f - int(3 * FPS)
    shown = int(max(0, lf) / (4.2 * FPS) * len(PROMPT))
    lines = wrap(d, PROMPT[:shown], 46, 1240)
    y = 350
    for ln in lines:
        text(d, (320, y), ln, 46, WHITE)
        y += 68
    if lf > 0 and (lf // 15) % 2 == 0 and shown < len(PROMPT):
        # Blinking caret at the end of the typed text.
        last = lines[-1] if lines else ""
        cx = 320 + d.textlength(last, font=font(46))
        d.rectangle([cx + 8, y - 68 + 6, cx + 14, y - 6], fill=CYAN)
    if shown >= len(PROMPT):
        text(d, (320, 790), "✓ sent — now watch it build",
             40, GREEN)
    return img


TERM_LINES = [
    ("$ muse build star-catcher", WHITE, 0.0),
    ("✓ game.html — canvas, paddle, falling stars", GREEN, 1.1),
    ("✓ 60-second timer + score HUD", GREEN, 2.2),
    ("✓ game-over screen + play again", GREEN, 3.3),
    ("$ open star-catcher.html", WHITE, 4.4),
    ("✓ BUILD COMPLETE — 1 file, 0 dependencies", CYAN, 5.6),
]


def scene_terminal(f):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=MAGENTA)
    centre(d, 90, "THE AGENT WORKS", 64, MUTED)
    rrect(d, [180, 220, 1740, 860], 28, fill=(10, 8, 14))
    d.ellipse([220, 252, 248, 280], fill=(255, 95, 86))
    d.ellipse([262, 252, 290, 280], fill=(255, 189, 46))
    d.ellipse([304, 252, 332, 280], fill=(39, 201, 63))
    lf = f - int(8 * FPS)
    t = lf / FPS
    y = 330
    for s, col, at in TERM_LINES:
        if t >= at:
            a = fade_in(lf, at, 0.3)
            text(d, (230, y), s, 42, blend((10, 8, 14), col, a))
        y += 78
    # Progress bar.
    prog = max(0.0, min(1.0, (t - 5.6) / 1.6))
    rrect(d, [230, 800, 1690, 824], 12, fill=PANEL2)
    if prog > 0:
        rrect(d, [230, 800, 230 + int(1460 * prog), 824], 12, fill=MAGENTA)
    return img


def scene_game(f):
    gf = f - int(GAME_T0 * FPS)
    img = Image.new("RGB", (W, H), (20, 16, 42))
    d = ImageDraw.Draw(img)
    # Browser chrome.
    d.rectangle([0, 0, W, 64], fill=PANEL)
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([28 + i * 44, 20, 56 + i * 44, 48], fill=col)
    rrect(d, [560, 12, 1360, 52], 20, fill=PANEL2)
    centre(d, 17, "★  Star Catcher — star-catcher.html", 30, MUTED)
    # HUD — kept clear of the make.fun badge (top-left, y 96-224).
    text(d, (60, 250), f"SCORE {score_at[gf]}", 46, WHITE)
    secs = time_at[gf]
    text(d, (W - 60, 250), f"TIME 0:{secs:02d}", 46, WHITE, anchor="ra")
    # Stars (positions from the recorded snapshot for this frame).
    snap = snapshots[min(gf, GAME_FRAMES - 1)]
    for (sx, sy, sr, state) in snap["stars"]:
        if state == "gone":
            continue
        draw_star(d, sx, sy, sr, rot=gf * 0.02)
    # Bursts on catch.
    for b in bursts:
        age = gf - b["frame"]
        if 0 <= age <= 10:
            for k in range(6):
                ang = k * math.pi / 3
                rr = age * 9
                draw_star(d, b["x"] + rr * math.cos(ang),
                          b["y"] - 10 + rr * math.sin(ang) * 0.6,
                          10, fill=CYAN)
    # Paddle.
    px = snap["paddle"]
    rrect(d, [px, PADDLE_Y, px + PADDLE_W, PADDLE_Y + 26], 13,
          fill=MAGENTA, outline=WHITE, width=3)
    return img


def scene_end(f):
    img = scene_game(int(GAME_T0 * FPS) + GAME_FRAMES - 1)
    d = ImageDraw.Draw(img)
    overlay = Image.new("RGB", (W, H), (14, 10, 19))
    img = Image.blend(img, overlay, 0.82)
    d = ImageDraw.Draw(img)
    a1 = fade_in(f, 27.0, 0.4)
    if a1 > 0:
        centre(d, 300, "GAME OVER", 150, blend(BG, WHITE, a1))
        centre(d, 500, f"SCORE {FINAL_SCORE}  •  "
               f"{FINAL_CAUGHT} STARS CAUGHT", 56,
               blend(BG, YELLOW, a1))
        rrect(d, [810, 640, 1110, 720], 40, fill=MAGENTA)
        centre(d, 658, "PLAY AGAIN", 40, WHITE)
    a2 = fade_in(f, 28.3, 0.4)
    if a2 > 0:
        centre(d, 830, "Come build on make.fun  →", 64,
               blend(BG, CYAN, a2))
    return img


def frame_at(f):
    t = f / FPS
    if t < 3:
        return scene_hook(f)
    if t < 8:
        return scene_prompt(f)
    if t < 16:
        return scene_terminal(f)
    if t < 27:
        return scene_game(f)
    return scene_end(f)


# -------------------------------------------------------------------- audio
def make_audio(path):
    sr = 22050
    notes = [523.25, 659.25, 783.99, 880.00, 783.99, 659.25,
             587.33, 659.25]  # C5 E5 G5 A5 G5 E5 D5 E5
    step = int(sr * 0.22)
    total = int(sr * DUR)
    out = np.zeros(total, dtype=np.float32)
    tt = np.arange(step) / sr
    for i, freq in enumerate(notes * 20):
        start = i * step
        if start >= total:
            break
        env = np.minimum(1.0, np.arange(step) / (sr * 0.02)) * \
            np.exp(-np.arange(step) / (sr * 0.09))
        tone = (np.sin(2 * np.pi * freq * tt)
                + 0.3 * np.sin(2 * np.pi * freq * 3 * tt))
        n = min(step, total - start)
        out[start:start + n] += 0.12 * tone[:n] * env[:n]
    # Fade out over the last second.
    fade = np.ones(total, dtype=np.float32)
    fade[-sr:] = np.linspace(1, 0, sr)
    out *= fade
    pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    print("audio written:", path, flush=True)


def main():
    make_audio("audio.wav")
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", "audio.wav",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           "-c:a", "aac", "-b:a", "96k", "-shortest",
           "-movflags", "+faststart", "clip.mp4"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(NFRAMES):
        img = frame_at(f)
        try:
            proc.stdin.write(img.tobytes())
        except BrokenPipeError:
            print("ffmpeg pipe broke at frame", f, file=sys.stderr)
            sys.exit(1)
        if f % 150 == 0:
            print(f"frame {f}/{NFRAMES}", flush=True)
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        print("ffmpeg failed", proc.returncode, file=sys.stderr)
        sys.exit(1)
    print("clip.mp4 done", flush=True)


if __name__ == "__main__":
    main()
