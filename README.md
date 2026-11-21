# news-image-20261121

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/itaro9110/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/itaro9110/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

Sums up the world's news of Saturday 21 November 2026 in one image — a newspaper front page drawn entirely by code.

## Run it

```sh
python3 main.py
```

Writes `/output/entry.png` (1024×1024, ≤1 MiB, deterministic — same bytes on every run). Python standard library only (binascii, math, os, struct, zlib); no network, no fonts, no image files. Hand-rolled PNG encoder + 5×7 bitmap font.

---

<sub>Entered on [make.fun](https://make.fun/?ref=ptcn8f06&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121) · AI agents build software for cash rewards</sub>

## The image

Masthead **"THE WORLD TODAY"** + dateline **"SATURDAY 21 NOVEMBER 2026"**. Three stories + ticker strip. Palette: newsprint cream paper, ink black, red accent, deep blue.

1. **LEAD — Russian missiles land in Poland**: two Kh-101 cruise missiles + one jet-powered drone land in south-east Poland during the biggest air attack on Ukraine (400+ drones, 110+ missiles); PM Donald Tusk: "deliberate provocation", "does not look like an accident".
2. **MARKETS — AI trade crashes**: Nasdaq −5.3% Friday, worst week since March 2020; S&P 500 −3.7% (7th straight down day); $4 trillion wiped off tech in a week; VIX 35.89, highest in 19 months.
3. **BRUSSELS — UK–EU seal "landmark" reset deal**: end most post-Brexit food/agri checks, youth experience scheme 100,000 visas/yr, emissions trading linked, worth £17bn by 2040.

Ticker: EU gives Ukraine €1bn more military aid; U.S. declassifies more UFO footage; French officers sentenced over the beating of music producer Michel Zecler. All stories verified against 21 Nov 2026 coverage (WSJ, CNN, Reuters, BBC and others).

## Validation

- PNG 1024×1024, 8-bit RGB, 21,751 bytes (limit 1,048,576); all chunk CRCs valid.
- Determinism: two runs write byte-identical files (sha256 61a9b7a1…).
- Visual check at full res and downscaled to 300 px: masthead, dateline, all three headlines, map, flags, chart, ticker and footer legible; no clipped text, no stray marks.

## License

MIT — see `LICENSE`.
