---
title: SGP Calibration
---

```js
import * as d3 from "npm:d3";
```

```js
const C = {
  bg:  "#faf9f5",
  txt: "#2d2d2d",
  mid: "#666",
  lit: "#999",
  grd: "#ededeb",
  pri: "#3A6EA5",
  sec: "#C1666B",
  acc: "#2A9D8F",
};
```

```js
// ── Calibration data ──────────────────────────────────────────────────────────
// Team HR totals per year (primary calibration window: 2019, 2021–2025)
const HR_HISTORY = [
  [2019,346,0],[2019,327,1],[2019,325,2],[2019,311,3],[2019,282,4],
  [2019,274,5],[2019,272,6],[2019,266,7],[2019,259,8],[2019,238,9],[2019,204,10],
  [2021,357,0],[2021,301,1],[2021,286,2],[2021,275,3],[2021,246,4],
  [2021,222,5],[2021,220,6],[2021,216,7],[2021,209,8],[2021,196,9],[2021,164,10],
  [2022,251,0],[2022,241,1],[2022,229,2],[2022,227,3],[2022,217,4],
  [2022,190,5],[2022,186,6],[2022,185,7],[2022,176,8],[2022,170,9],[2022,151,10],
  [2023,289,0],[2023,280,1],[2023,273,2],[2023,271,3],[2023,259,4],
  [2023,257,5],[2023,255,6],[2023,210,7],[2023,200,8],[2023,195,9],
  [2024,285,0],[2024,276,1],[2024,254,2],[2024,248,3],[2024,247,4],
  [2024,230,5],[2024,215,6],[2024,210,7],[2024,201,8],[2024,191,9],
  [2025,315,0],[2025,294,1],[2025,285,2],[2025,278,3],[2025,278,4],
  [2025,260,5],[2025,257,6],[2025,246,7],[2025,195,8],[2025,193,9],
].map(([year, hr, i]) => ({ year, hr, jitter: (i % 5 - 2) * 4.5 }));

// Pairwise gap illustration: 2024 HR, 10 teams sorted by HR desc
const GAPS_2024 = [
  {team: "Dancing W/ Dingos", hr: 285},
  {team: "Kerry & Mitch",     hr: 276},
  {team: "Gusteroids",        hr: 254},
  {team: "Mean Machine",      hr: 248},
  {team: "Thunder & Lightning",hr: 247},
  {team: "On a Bender",       hr: 230},
  {team: "R&R",               hr: 215},
  {team: "Shrooms",           hr: 210},
  {team: "HAMMERHEADS",       hr: 201},
  {team: "Ayal Feinberg",     hr: 191},
].map((d, i) => ({...d, rank: i + 1}));

const GAPS_2024_ADJ = GAPS_2024.slice(0, -1).map((d, i) => ({
  gap:     d.hr - GAPS_2024[i + 1].hr,
  rankMid: d.rank + 0.5,
}));
const MEAN_GAP_2024 = d3.mean(GAPS_2024_ADJ, d => d.gap); // 10.44

// Method comparison: best rank_correlation per estimation method (from 320-config sweep)
const METHODS = [
  {label: "Robust regression",  rank_corr: 0.9677, nrmse: 0.292},
  {label: "Pairwise median",    rank_corr: 0.9655, nrmse: 0.323},
  {label: "OLS regression",     rank_corr: 0.9649, nrmse: 0.263},
  {label: "Pairwise mean",      rank_corr: 0.9604, nrmse: 0.300},
];

// Per-category nRMSE — baseline config (pairwise_mean, primary_only, no decay)
const NRMSE = [
  {cat: "SV",   nrmse: 0.156, type: "pit"},
  {cat: "AVG",  nrmse: 0.180, type: "bat"},
  {cat: "R",    nrmse: 0.208, type: "bat"},
  {cat: "WHIP", nrmse: 0.222, type: "pit"},
  {cat: "RBI",  nrmse: 0.243, type: "bat"},
  {cat: "ERA",  nrmse: 0.244, type: "pit"},
  {cat: "SO",   nrmse: 0.259, type: "pit"},
  {cat: "HR",   nrmse: 0.309, type: "bat"},
  {cat: "SB",   nrmse: 0.523, type: "bat"},
  {cat: "W",    nrmse: 0.560, type: "pit"},
].sort((a, b) => a.nrmse - b.nrmse);

// Final calibrated denominators (primary_only, pairwise_mean, no decay)
// Counting stats on shared scale; rate stats shown separately
const DENOMS_COUNTING = [
  {cat: "W",   val: 3.73,  type: "pit"},
  {cat: "SV",  val: 6.36,  type: "pit"},
  {cat: "SB",  val: 10.05, type: "bat"},
  {cat: "HR",  val: 12.07, type: "bat"},
  {cat: "RBI", val: 31.85, type: "bat"},
  {cat: "R",   val: 32.39, type: "bat"},
  {cat: "SO",  val: 41.09, type: "pit"},
].sort((a, b) => a.val - b.val);

const DENOMS_RATE = [
  {cat: "WHIP", val: 0.01936, display: ".019", type: "pit"},
  {cat: "AVG",  val: 0.00319, display: ".003", type: "bat"},
  {cat: "ERA",  val: 0.09853, display: ".099", type: "pit"},
];
```

# How the SGP Model Was Calibrated

*Moonlight Graham League · AL-only keeper league · March 2026 · [← 2026 Auction Analysis](.)*

<div class="narrative">
Rotisserie fantasy baseball scores each team 1–10 points per category: 10 for the most of a stat, 1 for the least. The challenge for player valuation is translating a raw statistical projection — say, 30 home runs — into those standings positions. <strong>Standings Gain Points (SGP)</strong> are the bridge. One SGP represents one additional place in one category's standings. A player's value is how many SGP they add above what a freely available replacement could produce.
</div>

<div class="narrative">
The core question is: <em>how many home runs, runs, or strikeouts does it actually take to move one place in the standings?</em> That answer depends entirely on this specific league — 10 teams, AL players only, a deep keeper pool. A standard public SGP table from a 12-team mixed league is miscalibrated for our context. So we build our own from ten years of league history.
</div>

## The SGP Formula

The denominator for each statistical category is the quantity of that stat associated with a one-place improvement in standings. For a player projected to produce **x** units of a counting stat, their SGP contribution is:

<div class="callout">
<strong>Counting stat SGP</strong> = (player production − replacement level) ÷ category denominator<br><br>
<strong>Rate stat SGP</strong> = (player rate − replacement rate) × (player PA or IP ÷ team PA or IP) ÷ category denominator
</div>

<div class="narrative">
The denominator is what this document is about — how it's computed, validated, and what it ultimately is. Replacement level is set as the statistical output of the marginal player at each roster position (roughly the 150th hitter and 110th pitcher in terms of value).
</div>

---

## Calibration Data: Ten Years of AL-Only History

<div class="narrative">
The primary calibration window uses six full seasons: 2019 and 2021–2025. The 2020 COVID-shortened season is excluded (60 games introduces noise that would distort the denominators). The 2015–2018 seasons are available as supplemental data but used selectively — those years had only eight scoring categories and variable team counts.
</div>

<div class="narrative">
Below is the distribution of team home run totals across the six primary years. Each dot is one team's season. The horizontal bar marks the per-year mean. The distribution's consistency — the spread looks similar year to year — is what makes pooling across years defensible.
</div>

```js
{
  const W = 700, H = 260;
  const M = {top: 36, right: 24, bottom: 42, left: 48};
  const iw = W - M.left - M.right;
  const ih = H - M.top - M.bottom;

  const years = [2019, 2021, 2022, 2023, 2024, 2025];
  const yearMeans = d3.rollup(HR_HISTORY, v => d3.mean(v, d => d.hr), d => d.year);

  const x = d3.scalePoint()
    .domain(years.map(String))
    .range([0, iw])
    .padding(0.5);

  const y = d3.scaleLinear()
    .domain([130, 385])
    .range([ih, 0]);

  const svg = d3.create("svg")
    .attr("width", W).attr("height", H)
    .style("background", C.bg)
    .style("display", "block");

  const g = svg.append("g")
    .attr("transform", `translate(${M.left},${M.top})`);

  // Grid
  [150, 200, 250, 300, 350].forEach(v => {
    g.append("line")
      .attr("x1", 0).attr("x2", iw)
      .attr("y1", y(v)).attr("y2", y(v))
      .attr("stroke", C.grd).attr("stroke-width", 0.5);
    g.append("text")
      .attr("x", -7).attr("y", y(v)).attr("dy", "0.32em")
      .attr("text-anchor", "end").attr("fill", C.lit).attr("font-size", 10)
      .text(v);
  });

  // Year labels
  years.forEach(yr => {
    g.append("text")
      .attr("x", x(String(yr))).attr("y", ih + 22)
      .attr("text-anchor", "middle").attr("fill", C.lit).attr("font-size", 11)
      .text(yr);
  });

  // Dots
  g.append("g").selectAll("circle")
    .data(HR_HISTORY)
    .join("circle")
    .attr("cx", d => x(String(d.year)) + d.jitter)
    .attr("cy", d => y(d.hr))
    .attr("r", 3.5)
    .attr("fill", C.pri)
    .attr("fill-opacity", 0.42);

  // Per-year mean lines
  [...yearMeans.entries()].forEach(([yr, m]) => {
    g.append("line")
      .attr("x1", x(String(yr)) - 20).attr("x2", x(String(yr)) + 20)
      .attr("y1", y(m)).attr("y2", y(m))
      .attr("stroke", C.pri).attr("stroke-width", 2.5);
  });

  // Y-axis label
  g.append("text")
    .attr("x", -M.left + 4).attr("y", -16)
    .attr("fill", C.mid).attr("font-size", 11)
    .text("Team home runs (full season)");

  // Legend
  g.append("circle").attr("cx", iw - 116).attr("cy", -14).attr("r", 3.5)
    .attr("fill", C.pri).attr("fill-opacity", 0.42);
  g.append("text").attr("x", iw - 107).attr("y", -11)
    .attr("fill", C.lit).attr("font-size", 10).text("team season");

  g.append("line")
    .attr("x1", iw - 40).attr("x2", iw - 18)
    .attr("y1", -14).attr("y2", -14)
    .attr("stroke", C.pri).attr("stroke-width", 2.5);
  g.append("text").attr("x", iw - 10).attr("y", -11)
    .attr("fill", C.lit).attr("font-size", 10).text("mean");

  return svg.node();
}
```

<p class="section-meta">2020 excluded (60-game COVID season). 2019 and 2021–2022 had 11 teams; gaps are normalized to a 10-team scale before pooling.</p>

---

## Computing the Denominator: Pairwise Gaps

<div class="narrative">
The most direct approach to calibration is the <strong>pairwise gap method</strong>. Within each year, sort all teams by their total in a given category. The "pairwise gap" for a single adjacent pair is simply the difference in the stat between the team ranked one place higher and the team ranked one place lower. Average those gaps across all adjacent pairs, pool across all calibration years (weighting more recent seasons more heavily when time decay is enabled), and the result is the SGP denominator.
</div>

<div class="narrative">
The 2024 home run standings below illustrate the calculation. Nine gaps separate ten teams. Their mean is the single-year denominator estimate for home runs. Pooled across six years, this stabilizes to the final calibrated value.
</div>

```js
{
  const W = 660, H = 366;
  const M = {top: 32, right: 148, bottom: 44, left: 168};
  const iw = W - M.left - M.right;  // 344
  const ih = H - M.top - M.bottom;  // 290

  const x = d3.scaleLinear().domain([178, 298]).range([0, iw]);
  const y = d3.scaleLinear().domain([1, 10]).range([0, ih]);

  const svg = d3.create("svg")
    .attr("width", W).attr("height", H)
    .style("background", C.bg)
    .style("display", "block");

  const g = svg.append("g")
    .attr("transform", `translate(${M.left},${M.top})`);

  // Vertical grid
  [200, 220, 240, 260, 280].forEach(v => {
    g.append("line")
      .attr("x1", x(v)).attr("x2", x(v))
      .attr("y1", 0).attr("y2", ih)
      .attr("stroke", C.grd).attr("stroke-width", 0.5);
    g.append("text")
      .attr("x", x(v)).attr("y", ih + 18)
      .attr("text-anchor", "middle").attr("fill", C.lit).attr("font-size", 10)
      .text(v);
  });

  // X-axis label
  g.append("text")
    .attr("x", iw / 2).attr("y", ih + 34)
    .attr("text-anchor", "middle").attr("fill", C.mid).attr("font-size", 11)
    .text("Home runs (2024 team total)");

  // Lollipop lines from left baseline
  GAPS_2024.forEach(d => {
    g.append("line")
      .attr("x1", x(178)).attr("x2", x(d.hr))
      .attr("y1", y(d.rank)).attr("y2", y(d.rank))
      .attr("stroke", C.grd).attr("stroke-width", 1);
  });

  // Dots
  GAPS_2024.forEach(d => {
    g.append("circle")
      .attr("cx", x(d.hr)).attr("cy", y(d.rank))
      .attr("r", 4.5).attr("fill", C.pri);
  });

  // HR value labels right of dots
  GAPS_2024.forEach(d => {
    g.append("text")
      .attr("x", x(d.hr) + 8).attr("y", y(d.rank))
      .attr("dy", "0.32em").attr("fill", C.mid).attr("font-size", 10)
      .text(d.hr);
  });

  // Team name labels
  GAPS_2024.forEach(d => {
    g.append("text")
      .attr("x", -10).attr("y", y(d.rank))
      .attr("dy", "0.32em").attr("text-anchor", "end")
      .attr("fill", C.mid).attr("font-size", 10)
      .text(d.team);
  });

  // Rank labels
  GAPS_2024.forEach(d => {
    g.append("text")
      .attr("x", -96).attr("y", y(d.rank))
      .attr("dy", "0.32em").attr("text-anchor", "end")
      .attr("fill", C.lit).attr("font-size", 9)
      .text(`#${d.rank}`);
  });

  // Gap annotations: right side
  const gx = iw + 22;
  GAPS_2024_ADJ.forEach(gap => {
    const y1 = y(gap.rankMid - 0.5);
    const y2 = y(gap.rankMid + 0.5);
    const isLarge = gap.gap > MEAN_GAP_2024;

    // Bracket ticks
    [-4, 4].forEach(dx => {
      [y1, y2].forEach(yv => {
        g.append("line")
          .attr("x1", gx + dx).attr("x2", gx)
          .attr("y1", yv).attr("y2", yv)
          .attr("stroke", isLarge ? C.sec : C.lit).attr("stroke-width", 1);
      });
    });

    // Vertical connector
    g.append("line")
      .attr("x1", gx).attr("x2", gx)
      .attr("y1", y1).attr("y2", y2)
      .attr("stroke", isLarge ? C.sec : C.lit).attr("stroke-width", 1);

    // Gap label
    g.append("text")
      .attr("x", gx + 9).attr("y", (y1 + y2) / 2)
      .attr("dy", "0.32em")
      .attr("fill", isLarge ? C.sec : C.lit).attr("font-size", 9)
      .attr("font-weight", isLarge ? 600 : 400)
      .text(gap.gap);
  });

  // Mean gap annotation
  g.append("text")
    .attr("x", gx + 9).attr("y", ih + 14)
    .attr("fill", C.mid).attr("font-size", 10).attr("font-weight", 600)
    .text(`Mean: ${MEAN_GAP_2024.toFixed(1)}`);
  g.append("text")
    .attr("x", gx + 9).attr("y", ih + 26)
    .attr("fill", C.lit).attr("font-size", 9)
    .text("(2024 only)");

  // Chart subtitle
  g.append("text")
    .attr("x", 0).attr("y", -14)
    .attr("fill", C.mid).attr("font-size", 10).attr("font-style", "italic")
    .text("2024 season · teams sorted by home runs · highlighted gaps exceed the mean");

  return svg.node();
}
```

<p class="section-meta">Gaps above the mean are highlighted in rose. The 2024-only mean (10.4) is a single-year estimate. Pooling all six primary years with time-decay weighting (recent years weighted more) produces the final denominator of <strong>12.1</strong> for home runs.</p>

---

## Four Estimation Methods

<div class="narrative">
The pairwise gap approach has a natural extension problem: punting. A team that intentionally ignores saves or stolen bases will have an outlier-level 1.0 points in that category — a perfectly legitimate strategy, not a data point that should anchor the denominator. Four methods handle this differently.
</div>

<dl class="glossary-grid" style="margin-top: 0; margin-bottom: 28px;">
  <div class="glossary-item">
    <dt>Pairwise mean</dt>
    <dd>Average of all adjacent-rank gaps, pooled across years. Simple, interpretable, sensitive to punters in small samples.</dd>
  </div>
  <div class="glossary-item">
    <dt>Pairwise median</dt>
    <dd>Median instead of mean — naturally resistant to outlier gaps. Tends to produce smaller denominators (tighter perceived spread).</dd>
  </div>
  <div class="glossary-item">
    <dt>OLS regression</dt>
    <dd>Regress the stat on standings points across all team-years. The slope is the denominator. Pools more information but assumes linearity.</dd>
  </div>
  <div class="glossary-item">
    <dt>Robust regression</dt>
    <dd>Huber loss function down-weights outlier teams (punters, penalty years). Best rank correlation in the sweep — at the cost of interpretability.</dd>
  </div>
</dl>

<div class="narrative">
A 320-configuration sweep tested all four methods across combinations of data window (primary vs. supplemental), time decay (none, 0.80, 0.85, 0.90 decay rates), punt detection, and replacement buffers. The primary validation metric was <strong>rank correlation</strong>: Spearman ρ between each team's SGP-implied rank and their actual final standings position, evaluated out-of-sample using leave-one-year-out cross-validation.
</div>

```js
{
  const W = 560, H = 210;
  const M = {top: 28, right: 90, bottom: 36, left: 168};
  const iw = W - M.left - M.right;  // 302
  const ih = H - M.top - M.bottom;  // 146

  const sorted = [...METHODS].sort((a, b) => a.rank_corr - b.rank_corr);
  const xMin = 0.955, xMax = 0.972;

  const x = d3.scaleLinear().domain([xMin, xMax]).range([0, iw]);
  const y = d3.scaleBand()
    .domain(sorted.map(d => d.label))
    .range([ih, 0])
    .padding(0.38);

  const svg = d3.create("svg")
    .attr("width", W).attr("height", H)
    .style("background", C.bg)
    .style("display", "block");

  const g = svg.append("g")
    .attr("transform", `translate(${M.left},${M.top})`);

  // Grid
  [0.957, 0.960, 0.963, 0.966, 0.969].forEach(v => {
    g.append("line")
      .attr("x1", x(v)).attr("x2", x(v))
      .attr("y1", 0).attr("y2", ih)
      .attr("stroke", C.grd).attr("stroke-width", 0.5);
    g.append("text")
      .attr("x", x(v)).attr("y", ih + 18)
      .attr("text-anchor", "middle").attr("fill", C.lit).attr("font-size", 9)
      .text(v.toFixed(3));
  });

  // Lollipop lines
  sorted.forEach(d => {
    const cy = y(d.label) + y.bandwidth() / 2;
    g.append("line")
      .attr("x1", x(xMin)).attr("x2", x(d.rank_corr))
      .attr("y1", cy).attr("y2", cy)
      .attr("stroke", C.grd).attr("stroke-width", 1);
    g.append("circle")
      .attr("cx", x(d.rank_corr)).attr("cy", cy)
      .attr("r", 5)
      .attr("fill", d.label === "Robust regression" ? C.acc : C.pri)
      .attr("fill-opacity", d.label === "Robust regression" ? 1 : 0.55);
    g.append("text")
      .attr("x", x(d.rank_corr) + 8).attr("y", cy)
      .attr("dy", "0.32em").attr("fill", C.mid).attr("font-size", 10)
      .text(d.rank_corr.toFixed(4));
    g.append("text")
      .attr("x", -10).attr("y", cy)
      .attr("dy", "0.32em").attr("text-anchor", "end")
      .attr("fill", d.label === "Robust regression" ? C.txt : C.mid)
      .attr("font-size", 11)
      .attr("font-weight", d.label === "Robust regression" ? 600 : 400)
      .text(d.label);
  });

  // X-axis label
  g.append("text")
    .attr("x", iw / 2).attr("y", ih + 34)
    .attr("text-anchor", "middle").attr("fill", C.mid).attr("font-size", 11)
    .text("Rank correlation (Spearman ρ, leave-one-year-out)");

  // Annotation
  g.append("text")
    .attr("x", iw + 4).attr("y", y("Robust regression") + y.bandwidth() / 2)
    .attr("dy", "0.32em").attr("fill", C.acc).attr("font-size", 9)
    .attr("font-weight", 600).text("← selected");

  return svg.node();
}
```

<p class="section-meta">All four methods produce rank correlations above 0.96 — strong evidence that the league's historical data is consistent enough to calibrate regardless of method. The sweep selected <strong>robust regression</strong> as the global best, but the composite configuration uses per-category winners.</p>

---

## Composite Configuration

<div class="narrative">
Rather than applying one method uniformly across all ten categories, the sweep also tested a <strong>composite model</strong> where each category independently selects its best method, data window, and time decay setting. The per-category winners differ meaningfully: saves (high variance due to closer usage) benefits from robust regression; wins benefits from punt detection; home runs and WHIP prefer pairwise mean on supplemental data.
</div>

<table style="width:100%; border-collapse:collapse; font-size:12px; margin-bottom:28px;">
  <thead>
    <tr style="border-bottom:2px solid #ededeb;">
      <th style="text-align:left; padding:7px 10px; color:#2d2d2d; font-weight:700;">Category</th>
      <th style="text-align:left; padding:7px 10px; color:#2d2d2d; font-weight:700;">Method</th>
      <th style="text-align:left; padding:7px 10px; color:#2d2d2d; font-weight:700;">Data</th>
      <th style="text-align:left; padding:7px 10px; color:#2d2d2d; font-weight:700;">Time decay</th>
      <th style="text-align:left; padding:7px 10px; color:#2d2d2d; font-weight:700;">Punt detect</th>
    </tr>
  </thead>
  <tbody style="color:#555;">
    <tr style="border-bottom:1px solid #ededeb; background:#faf9f5;">
      <td style="padding:6px 10px; font-weight:600; color:#2d2d2d;">R</td>
      <td style="padding:6px 10px;">OLS</td>
      <td style="padding:6px 10px;">Primary</td>
      <td style="padding:6px 10px;">Yes (0.80)</td>
      <td style="padding:6px 10px;">No</td>
    </tr>
    <tr style="border-bottom:1px solid #ededeb;">
      <td style="padding:6px 10px; font-weight:600; color:#2d2d2d;">HR</td>
      <td style="padding:6px 10px;">Pairwise mean</td>
      <td style="padding:6px 10px;">+ Supplemental</td>
      <td style="padding:6px 10px;">No</td>
      <td style="padding:6px 10px;">No</td>
    </tr>
    <tr style="border-bottom:1px solid #ededeb; background:#faf9f5;">
      <td style="padding:6px 10px; font-weight:600; color:#2d2d2d;">RBI</td>
      <td style="padding:6px 10px;">OLS</td>
      <td style="padding:6px 10px;">+ Supplemental</td>
      <td style="padding:6px 10px;">No</td>
      <td style="padding:6px 10px;">No</td>
    </tr>
    <tr style="border-bottom:1px solid #ededeb;">
      <td style="padding:6px 10px; font-weight:600; color:#2d2d2d;">SB</td>
      <td style="padding:6px 10px;">Pairwise mean</td>
      <td style="padding:6px 10px;">+ Supplemental</td>
      <td style="padding:6px 10px;">Yes (0.90)</td>
      <td style="padding:6px 10px;">No</td>
    </tr>
    <tr style="border-bottom:1px solid #ededeb; background:#faf9f5;">
      <td style="padding:6px 10px; font-weight:600; color:#2d2d2d;">AVG</td>
      <td style="padding:6px 10px;">Pairwise mean</td>
      <td style="padding:6px 10px;">Primary</td>
      <td style="padding:6px 10px;">No</td>
      <td style="padding:6px 10px;">No</td>
    </tr>
    <tr style="border-bottom:1px solid #ededeb;">
      <td style="padding:6px 10px; font-weight:600; color:#2d2d2d;">W</td>
      <td style="padding:6px 10px;">Pairwise median</td>
      <td style="padding:6px 10px;">Primary</td>
      <td style="padding:6px 10px;">Yes (0.80)</td>
      <td style="padding:6px 10px;"><strong style="color:#C1666B;">Yes</strong></td>
    </tr>
    <tr style="border-bottom:1px solid #ededeb; background:#faf9f5;">
      <td style="padding:6px 10px; font-weight:600; color:#2d2d2d;">SV</td>
      <td style="padding:6px 10px;">Robust regression</td>
      <td style="padding:6px 10px;">+ Supplemental</td>
      <td style="padding:6px 10px;">No</td>
      <td style="padding:6px 10px;">No</td>
    </tr>
    <tr style="border-bottom:1px solid #ededeb;">
      <td style="padding:6px 10px; font-weight:600; color:#2d2d2d;">SO</td>
      <td style="padding:6px 10px;">Pairwise mean</td>
      <td style="padding:6px 10px;">Primary</td>
      <td style="padding:6px 10px;">No</td>
      <td style="padding:6px 10px;"><strong style="color:#C1666B;">Yes</strong></td>
    </tr>
    <tr style="border-bottom:1px solid #ededeb; background:#faf9f5;">
      <td style="padding:6px 10px; font-weight:600; color:#2d2d2d;">ERA</td>
      <td style="padding:6px 10px;">OLS</td>
      <td style="padding:6px 10px;">+ Supplemental</td>
      <td style="padding:6px 10px;">Yes (0.80)</td>
      <td style="padding:6px 10px;">No</td>
    </tr>
    <tr>
      <td style="padding:6px 10px; font-weight:600; color:#2d2d2d;">WHIP</td>
      <td style="padding:6px 10px;">Pairwise mean</td>
      <td style="padding:6px 10px;">+ Supplemental</td>
      <td style="padding:6px 10px;">No</td>
      <td style="padding:6px 10px;">No</td>
    </tr>
  </tbody>
</table>

<div class="callout">
<strong>Punt detection</strong> is enabled only for W and SO — the two categories where teams most commonly adopt a punt strategy. When enabled, teams whose category z-score falls below −1.5 are excluded from the gap computation. Saves were initially a candidate too, but the robust regression method already down-weights closer-deprived outliers without explicit exclusion.
</div>

---

## Validation: Leave-One-Year-Out Cross-Validation

<div class="narrative">
Each configuration was validated using leave-one-year-out (LOYO) cross-validation across the six primary seasons. In each fold, five years train the denominator and the held-out year tests prediction quality. Two metrics matter most:
</div>

<div class="mode-callout">
  <div class="mode-callout-box mc-single">
    <div class="mct">Rank Correlation (primary)</div>
    Spearman ρ between each team's SGP-implied ranking and their actual final standings position in the held-out year. A value of 0.95+ means the model consistently identifies which teams performed well — the core goal.
  </div>
  <div class="mode-callout-box mc-split">
    <div class="mct">Normalized RMSE (secondary)</div>
    RMSE of the predicted vs. actual denominator in the held-out year, normalized by each category's mean to prevent large-scale stats (R, SO) from dominating the aggregate. Lower is better; 0.30 means ±30% error on average.
  </div>
</div>

<div class="narrative">
The chart below shows per-category normalized RMSE for the baseline configuration. SV and AVG are well-predicted — their distributions are consistent year to year. W and SB are noisy — manager decisions, bullpen composition, and roster turnover create legitimate year-to-year volatility that no historical model can fully capture.
</div>

```js
{
  const W = 560, H = 310;
  const M = {top: 28, right: 90, bottom: 40, left: 80};
  const iw = W - M.left - M.right;  // 390
  const ih = H - M.top - M.bottom;  // 242

  const x = d3.scaleLinear().domain([0, 0.62]).range([0, iw]);
  const y = d3.scaleBand()
    .domain(NRMSE.map(d => d.cat))
    .range([ih, 0])
    .padding(0.32);

  const svg = d3.create("svg")
    .attr("width", W).attr("height", H)
    .style("background", C.bg)
    .style("display", "block");

  const g = svg.append("g")
    .attr("transform", `translate(${M.left},${M.top})`);

  // Grid
  [0.1, 0.2, 0.3, 0.4, 0.5, 0.6].forEach(v => {
    g.append("line")
      .attr("x1", x(v)).attr("x2", x(v))
      .attr("y1", 0).attr("y2", ih)
      .attr("stroke", C.grd).attr("stroke-width", 0.5);
    g.append("text")
      .attr("x", x(v)).attr("y", ih + 18)
      .attr("text-anchor", "middle").attr("fill", C.lit).attr("font-size", 9)
      .text(v.toFixed(1));
  });

  // Reference line at 0.30
  g.append("line")
    .attr("x1", x(0.30)).attr("x2", x(0.30))
    .attr("y1", 0).attr("y2", ih)
    .attr("stroke", C.mid).attr("stroke-width", 0.8).attr("stroke-dasharray", "3,3");
  g.append("text")
    .attr("x", x(0.30) + 4).attr("y", -8)
    .attr("fill", C.mid).attr("font-size", 9).attr("font-style", "italic")
    .text("overall avg");

  NRMSE.forEach(d => {
    const cy = y(d.cat) + y.bandwidth() / 2;
    const fill = d.type === "bat" ? C.pri : C.sec;

    g.append("line")
      .attr("x1", 0).attr("x2", x(d.nrmse))
      .attr("y1", cy).attr("y2", cy)
      .attr("stroke", C.grd).attr("stroke-width", 1);

    g.append("circle")
      .attr("cx", x(d.nrmse)).attr("cy", cy)
      .attr("r", 5).attr("fill", fill).attr("fill-opacity", 0.75);

    g.append("text")
      .attr("x", -8).attr("y", cy)
      .attr("dy", "0.32em").attr("text-anchor", "end")
      .attr("fill", C.mid).attr("font-size", 11)
      .text(d.cat);

    g.append("text")
      .attr("x", x(d.nrmse) + 8).attr("y", cy)
      .attr("dy", "0.32em").attr("fill", C.mid).attr("font-size", 10)
      .text(d.nrmse.toFixed(2) + "×");
  });

  // X label
  g.append("text")
    .attr("x", iw / 2).attr("y", ih + 34)
    .attr("text-anchor", "middle").attr("fill", C.mid).attr("font-size", 11)
    .text("Normalized RMSE (held-out year prediction error)");

  // Color legend
  g.append("circle").attr("cx", iw + 10).attr("cy", ih - 30).attr("r", 5)
    .attr("fill", C.pri).attr("fill-opacity", 0.75);
  g.append("text").attr("x", iw + 20).attr("y", ih - 27)
    .attr("fill", C.lit).attr("font-size", 9).text("batting");
  g.append("circle").attr("cx", iw + 10).attr("cy", ih - 14).attr("r", 5)
    .attr("fill", C.sec).attr("fill-opacity", 0.75);
  g.append("text").attr("x", iw + 20).attr("y", ih - 11)
    .attr("fill", C.lit).attr("font-size", 9).text("pitching");

  return svg.node();
}
```

<p class="section-meta">Rank correlation (0.954 Spearman ρ) is the more important metric: even if the model overestimates the W denominator by 30%, it still ranks teams correctly because W errors are consistent across teams. SB and W remain noisy at the denominator level but less so at the team-rank level.</p>

---

## The Final Denominators

<div class="narrative">
The calibrated denominators below represent how much of each counting stat separates adjacent standings positions, pooled across six seasons of this specific league. They are the numbers the model divides by when converting projected stats to SGP.
</div>

```js
{
  const W = 640, H = 280;
  const M = {top: 36, right: 100, bottom: 44, left: 72};
  const iw = W - M.left - M.right;  // 468
  const ih = H - M.top - M.bottom;  // 200

  const sorted = [...DENOMS_COUNTING].sort((a, b) => a.val - b.val);

  const x = d3.scaleLinear().domain([0, 46]).range([0, iw]);
  const y = d3.scaleBand()
    .domain(sorted.map(d => d.cat))
    .range([ih, 0])
    .padding(0.32);

  const svg = d3.create("svg")
    .attr("width", W).attr("height", H)
    .style("background", C.bg)
    .style("display", "block");

  const g = svg.append("g")
    .attr("transform", `translate(${M.left},${M.top})`);

  // Grid
  [10, 20, 30, 40].forEach(v => {
    g.append("line")
      .attr("x1", x(v)).attr("x2", x(v))
      .attr("y1", 0).attr("y2", ih)
      .attr("stroke", C.grd).attr("stroke-width", 0.5);
    g.append("text")
      .attr("x", x(v)).attr("y", ih + 18)
      .attr("text-anchor", "middle").attr("fill", C.lit).attr("font-size", 10)
      .text(v);
  });

  sorted.forEach(d => {
    const cy = y(d.cat) + y.bandwidth() / 2;
    const fill = d.type === "bat" ? C.pri : C.sec;

    g.append("line")
      .attr("x1", 0).attr("x2", x(d.val))
      .attr("y1", cy).attr("y2", cy)
      .attr("stroke", C.grd).attr("stroke-width", 1.2);

    g.append("circle")
      .attr("cx", x(d.val)).attr("cy", cy)
      .attr("r", 5.5).attr("fill", fill).attr("fill-opacity", 0.8);

    g.append("text")
      .attr("x", -8).attr("y", cy)
      .attr("dy", "0.32em").attr("text-anchor", "end")
      .attr("fill", C.mid).attr("font-size", 12).attr("font-weight", 600)
      .text(d.cat);

    g.append("text")
      .attr("x", x(d.val) + 9).attr("y", cy)
      .attr("dy", "0.32em").attr("fill", C.mid).attr("font-size", 11)
      .text(d.val.toFixed(1));
  });

  // X label
  g.append("text")
    .attr("x", iw / 2).attr("y", ih + 36)
    .attr("text-anchor", "middle").attr("fill", C.mid).attr("font-size", 11)
    .text("Stat units per one standings place");

  // Y label
  g.append("text")
    .attr("x", -M.left + 4).attr("y", -16)
    .attr("fill", C.mid).attr("font-size", 11)
    .text("Counting stat denominators");

  // Color legend
  g.append("circle").attr("cx", iw - 40).attr("cy", -14).attr("r", 5)
    .attr("fill", C.pri).attr("fill-opacity", 0.8);
  g.append("text").attr("x", iw - 30).attr("y", -11)
    .attr("fill", C.lit).attr("font-size", 10).text("batting");
  g.append("circle").attr("cx", iw + 12).attr("cy", -14).attr("r", 5)
    .attr("fill", C.sec).attr("fill-opacity", 0.8);
  g.append("text").attr("x", iw + 22).attr("y", -11)
    .attr("fill", C.lit).attr("font-size", 10).text("pitching");

  return svg.node();
}
```

<div class="mode-callout" style="margin-top: 14px;">
  <div class="mode-callout-box mc-single">
    <div class="mct">Rate stat denominators</div>
    <strong>AVG: .003</strong> — a .003 team batting average difference per place (teams cluster tightly in AVG)<br>
    <strong>ERA: .099</strong> — roughly 0.10 ERA per place<br>
    <strong>WHIP: .019</strong> — about 0.02 WHIP per place
  </div>
  <div class="mode-callout-box mc-split">
    <div class="mct">Reading the counting chart</div>
    <strong>W (3.7)</strong> is the tightest counting category — one extra win flips standings places regularly. <strong>SO (41)</strong> is the most spread — strikeouts range from ~950 to ~1,550 across teams, creating large gaps between adjacent ranks.
  </div>
</div>

---

## From Denominators to Dollars

<div class="narrative">
The denominators are the engine, but auction values require one more conversion. Each player's <strong>Points Above Replacement (PAR)</strong> sums their SGP contributions across all relevant categories. Total PAR for all rostered players is computed, then the total auction budget ($2,600 across ten teams) minus minimum bids is allocated proportionally. A player generating twice as much PAR as another player is worth twice as much money.
</div>

<div class="callout">
<strong>Dollar value</strong> = player PAR ÷ total positive PAR × spendable pool
<br><br>
In the <em>split-pool</em> variant, hitters and pitchers are valued from separate budgets (63% hitting / 37% pitching by default, calibrated to historical spending patterns), which prevents pitching and hitting markets from cross-subsidizing each other.
</div>

<div class="narrative">
For keeper leagues, an additional inflation factor is applied: keepers remove players and their salaries from the open market, leaving a smaller pool with more money chasing it. The remaining open-market players are inflated by the ratio of available money to baseline value of available players.
</div>

---

<div class="synthesis">
  <h2>Calibration Summary</h2>
  <dl class="synthesis-grid">
    <div class="synthesis-item">
      <dt>Primary calibration window</dt>
      <dd>2019, 2021–2025 (6 seasons · 60–66 team-years). 2020 excluded (60-game COVID season).</dd>
    </div>
    <div class="synthesis-item">
      <dt>Validation result</dt>
      <dd>0.954 Spearman rank correlation on held-out seasons — the model correctly identifies the top half of the standings ~95% of the time.</dd>
    </div>
    <div class="synthesis-item">
      <dt>Method</dt>
      <dd>Composite per-category configuration: pairwise mean, OLS, pairwise median, or robust regression selected independently for each of 10 categories.</dd>
    </div>
    <div class="synthesis-item">
      <dt>Key design choices</dt>
      <dd>Time decay (recent seasons weighted more). Punt detection for W and SO only. 2015–2018 supplemental data used selectively by category.</dd>
    </div>
    <div class="synthesis-item">
      <dt>Most stable categories</dt>
      <dd>SV (NRMSE 0.16) and AVG (0.18) — consistent distributions year to year make these denominators very predictable.</dd>
    </div>
    <div class="synthesis-item">
      <dt>Noisiest categories</dt>
      <dd>W (NRMSE 0.56) and SB (0.52) — volatile due to manager decisions, roster construction, and team-level factors outside historical patterns.</dd>
    </div>
  </dl>
</div>
