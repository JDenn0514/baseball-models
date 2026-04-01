# Moonlight Graham 2026 Auction Analysis — Observable Framework

Interactive D3.js auction report built with [Observable Framework](https://observablehq.com/framework/).

## Project structure

```
reports/auction-observable/
├── observablehq.config.js   # Site title, theme, base path
├── package.json
├── src/
│   ├── index.md             # Page source — edit narrative here
│   ├── custom.css           # Chart and component styles
│   └── data/
│       └── auction.json.py  # Python data loader (extracts DATA from HTML report)
└── dist/                    # Build output (git-ignored)
```

## Local development

```bash
cd reports/auction-observable
npm install
npm run dev
# → http://localhost:3000
```

The dev server watches all source files and hot-reloads on changes. Editing `src/index.md` updates the page instantly. The Python data loader runs automatically when needed and is cached in `src/.observablehq/cache/`.

## Build

```bash
npm run build
# → dist/  (self-contained static site)
```

## GitHub Pages deployment

The workflow at `.github/workflows/observable-deploy.yml` builds and deploys automatically on push to `main` when files under `reports/auction-observable/` or `reports/auction_analysis_2026_d3.html` change.

**One-time setup:**

1. In your GitHub repo Settings → Pages → Source: select **"GitHub Actions"**
2. If your Pages URL is `https://USERNAME.github.io/roto-models/` (not root), uncomment and set the `base` field in `observablehq.config.js`:
   ```js
   base: "/roto-models/",
   ```
3. Push to `main` — the workflow deploys automatically

## Data refresh

The data loader (`src/data/auction.json.py`) extracts the embedded `DATA` object from `reports/auction_analysis_2026_d3.html`. To update the data:

1. Regenerate `reports/auction_analysis_2026_d3.html` (via `targeting/analyze_auction.py`)
2. Delete `src/.observablehq/cache/data/auction.json` (or run `npm run build` — it re-runs loaders whose sources changed)
3. `npm run build` picks up the fresh data

## How to edit narrative

Open **`src/index.md`** in any text editor. Narrative text lives directly in the markdown between the code blocks. Edit it as plain prose — headings, paragraphs, bold/italic, and `<div class="narrative">` or `<span class="callout">` blocks for styled callouts.

Code blocks (` ```js `) contain chart logic and should not be touched for text-only edits. The glossary and synthesis sections at the bottom are plain `<dl>/<dt>/<dd>` HTML directly in the markdown and can be edited freely.
