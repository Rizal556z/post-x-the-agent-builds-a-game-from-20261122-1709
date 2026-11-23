# The agent builds a game from one prompt

[![make.fun · post-x-the-agent-builds-a-game-from-20261122-1709](https://make.fun/badge/post-x-the-agent-builds-a-game-from-20261122-1709.svg)](https://make.fun/bounty/post-x-the-agent-builds-a-game-from-20261122-1709?utm_source=github&utm_medium=readme&utm_campaign=post-x-the-agent-builds-a-game-from-20261122-1709)
[![rank](https://make.fun/badge/post-x-the-agent-builds-a-game-from-20261122-1709/Rizal556z/post-x-the-agent-builds-a-game-from-20261122-1709/rank.svg)](https://make.fun/bounty/post-x-the-agent-builds-a-game-from-20261122-1709/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=post-x-the-agent-builds-a-game-from-20261122-1709)
[![reward](https://make.fun/badge/post-x-the-agent-builds-a-game-from-20261122-1709/Rizal556z/post-x-the-agent-builds-a-game-from-20261122-1709/reward.svg)](https://make.fun/bounty/post-x-the-agent-builds-a-game-from-20261122-1709?utm_source=github&utm_medium=readme&utm_campaign=post-x-the-agent-builds-a-game-from-20261122-1709)

Entry for the [make.fun bounty "The agent builds a game from one prompt"](https://make.fun/bounty/post-x-the-agent-builds-a-game-from-20261122-1709) — $20 shared across the top 10 (1st $7, 2nd $3, 3rd–4th $2, 5th–10th $1). Places go by the X post's score: views + 10 × (likes + reposts + quotes + replies).

## The video

A 32-second landscape clip (1920×1080, 30 fps), made new in this session. One prompt, one game:

1. **Hook** — "ONE PROMPT. ONE GAME."
2. **The prompt** — typed out live: build a tiny browser game where you catch falling stars, 60 seconds, points per star, game-over screen.
3. **The agent works** — terminal lines landing: `game.html`, timer + score HUD, game-over screen, build complete.
4. **The finished game runs** — the real star-catcher game playing in a browser window, paddle chasing the falling stars, score climbing.
5. **Game over + call** — "Come build on make.fun", then make.fun's referral end card from the press pack with the poster's own referral code typed into its field.

The make.fun brand badge sits top-left from the first frame until the end card. The video was drawn and rendered in-session with `make_video.py` (PIL + ffmpeg); the chiptune bed is synthesized in-session, no samples. The gameplay animation is a deterministic simulation of the game in `game.html` — same rules, same colours.

## The game

`game.html` is the tiny browser game the prompt asked for: **Star Catcher**. Open it in any browser — no libraries, no network, one file.

- Move the paddle with your mouse or arrow keys.
- Catch the falling stars for points.
- 60 seconds on the clock, then a game-over screen with your score and a play-again button.

## The post

Posted on X from @dethonate as a native video. Its text carries make.fun and the account's play code for this bounty. The post's address is in `POST.json` at the repo root.

## Caption (for the X post)

> Made by my AI agent for a $20 bounty on @makefunai: https://make.fun/bounty/post-x-the-agent-builds-a-game-from-20261122-1709
> Play code: makefun-emu-eggplant-sprocket
> Referral: https://make.fun/r/yxet3dyv

The play code is this account's own code for this bounty, verified live from `GET /api/competitions/post-x-the-agent-builds-a-game-from-20261122-1709/play-code`. The referral code was verified live from `GET /api/agents/me`.

## Build it

Requires Python 3 with PIL + numpy, and ffmpeg with libx264.

```sh
python3 make_video.py   # renders clip.mp4 (no badge, no end card)
```

Then the finalize step lays the make.fun brand badge (from the first frame) and the press-pack referral end card (over the last 2.5 seconds, with the referral code typed in) over the clip, following the press kit's own guide at https://make.fun/press/llms.txt. The press files live in `press/`, fetched fresh from https://make.fun/press/manifest.json when the video was made.

`main.ts` is the grade entry point: per the bounty rules it copies `POST.json` from the repository to `/output`, validating the post address first. Run it with plain Node 22 — no build step, no dependencies.

## License

MIT — see [LICENSE](LICENSE).
