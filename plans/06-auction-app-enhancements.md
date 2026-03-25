# Plan 06: Auction App Enhancements — Live Strategic Decision Support ✅

## Overview

**What:** Ten new features for the live auction Streamlit app (`auction/app.py`) that transform
it from a targeting tool ("who should I bid on?") into a full strategic decision system
("how should I build my roster category by category?").

**Why:** The current app shows a composite Targeting Score and bid ceiling per player, but lacks:
- Category-level visibility (which categories does each player help?)
- Competitive awareness (what are rival teams' strengths/weaknesses?)
- Market adaptation (are prices running hot or cold?)
- Roster construction guidance (which positions are hardest to fill?)
- Error recovery (can't undo a mislogged result)

**Goal:** A Gusteroids auction manager can glance at the app and know: what place they're
projected to finish, which categories to target, which players fill those gaps, what the
market is doing, and whether to bid or nominate.

---

## Current Architecture

### Data Pipeline

```
load_base_data() [cached — ATC valuations + split-pool auction values]
  → compute_live_msp(draft_key) [cached on draft state — re-runs targeting.model.run_msp()]
    → (players_df, live_standings)
      → score_players(players, taken_names, budget_cap) → scored
        → render_right_column(scored)    [right: filters + targeting table]
        → render_left_column(standings, ...) [left: budget, lineup, category ranks, log]
```

### Key DataFrames

**`players` (from `compute_live_msp`):** One row per available FA. Columns include:
- Identity: `player_name`, `position`, `pos_type`, `fg_id`, `mlbam_id`
- Stats: `PA`, `AB`, `IP`, `R`, `HR`, `RBI`, `SB`, `AVG`, `W`, `SV`, `ERA`, `WHIP`, `SO`
- SGP: `sgp_R`, `sgp_HR`, `sgp_RBI`, `sgp_SB`, `sgp_AVG`, `sgp_W`, `sgp_SV`, `sgp_SO`, `sgp_ERA`, `sgp_WHIP`, `total_sgp`
- Values: `production_value` (what player is worth), `auction_value` (market price), `mi` (market inefficiency)
- MSP: `msp`, `msp_per_dollar`, `team_baseline_pts`
- Per-category deltas: `delta_rank_R`, `delta_rank_HR`, ..., `delta_rank_WHIP` (rank change if player added to Gusteroids)
- Team baseline ranks: `team_rank_R`, `team_rank_HR`, ..., `team_rank_WHIP`
- Derived: `is_pitcher`, `tier`, `profile`

**`scored` (from `score_players`):** Same as `players` plus:
- `sp_raw`, `pvp_raw` (raw dollar values)
- `pvp`, `sp`, `mi_sc` (rescaled 0–10)
- `ts` (Targeting Score = avg of three 0–10 components)
- `bid_ceil` (max bid = Mkt$ + 0.5×PVP_raw + 0.5×SP_raw, capped at budget)

**`live_standings`:** One row per team (10 rows). Columns:
- `team`, `R`, `HR`, `RBI`, `SB`, `AVG`, `W`, `SV`, `SO`, `ERA`, `WHIP`
- `rank_R`, `rank_HR`, ..., `rank_WHIP`, `total_pts`
- `keeper_AB`, `keeper_IP`, `n_keeper_hitters`, `n_keeper_pitchers`, `keeper_salary`, `team_AB`, `team_IP`

### Session State

| Key | Type | Description |
|-----|------|-------------|
| `taken` | `dict[str, dict]` | player_name → {team, price, nom_order} |
| `auction_log` | `list[dict]` | [{nom, player, winner, price, timestamp}, ...] |
| `nom_counter` | `int` | Sequential nomination number |
| `budget_spent` | `int` | Total $ spent by Gusteroids |
| `hitters_won` | `int` | Hitters drafted by Gusteroids |
| `pitchers_won` | `int` | Pitchers drafted by Gusteroids |
| `salary_committed` | `int` | Pre-auction keeper salary total |
| `act_hitters` | `int` | Active keeper hitter count |
| `act_pitchers` | `int` | Active keeper pitcher count |
| `roster_slots` | `list[dict]` | 26-slot roster (15H + 11P), each: {slot, player, salary, eligibility, is_keeper, is_farm} |
| `farm_players` | `list[dict]` | Farm/reserve players [{player, slot, salary, eligibility}] |

### Constants

```python
MY_TEAM = "Gusteroids"
TOTAL_BUDGET = 360
HITTER_SLOTS = 15
PITCHER_SLOTS = 11
DOLLARS_PER_STANDINGS_PT = 6.55
BID_CEIL_DAMPEN = 0.5
CATEGORIES = ["R", "HR", "RBI", "SB", "AVG", "W", "SV", "ERA", "WHIP", "SO"]
INVERSE_CATS = {"ERA", "WHIP"}
```

### Teams (10)

Dancing With Dingos, Gusteroids, HAMMERHEADS, Kerry & Mitch, Kosher Hogs,
Mean Machine, On a Bender, R&R, Shrooms, Thunder & Lightning

### CSS Conventions

Custom properties: `--primary` (#3A6EA5 blue), `--secondary` (#C1666B red), `--accent` (#2A9D8F teal),
`--bg` (#faf9f5), `--bg-card` (#f4f3ef), `--grid` (#ededeb), `--border` (#e0dfdb),
`--text` (#2d2d2d), `--mid` (#666), `--light` (#999).

Fonts: Source Serif 4 (headings), DM Sans (body), JetBrains Mono (data/labels/monospace).

Section headers use class `sec-hdr` (JetBrains Mono, 9px, uppercase, letter-spacing 1.8px).
Cards use white bg, 1px border, 6px radius.
Data values use JetBrains Mono.

---

## Features (Build Order)

### Phase A — Foundation

#### Feature 1: Category Breakdown Panel

**What:** When a player is selected, show which of the 10 categories they help, with
current rank → new rank and delta for each.

**Data source:** `delta_rank_{cat}` and `team_rank_{cat}` columns already exist in `scored`.
No new computation needed — just surface existing data.

**UI approach:** Add a selectbox below the targeting table in `render_right_column`. On
selection, render an HTML panel with a 2×5 grid (batting row, pitching row).

**New function:**

```python
def _category_breakdown_html(player_row: pd.Series) -> str:
    """Build HTML grid showing per-category rank deltas for a selected player.

    For each of 10 categories, shows:
      - Category name (e.g., "HR")
      - Current rank → new rank (e.g., "4 → 6")
      - Delta with color (green=improvement, gray=flat, red=decrease)

    Groups: batting (R, HR, RBI, SB, AVG) top row, pitching (W, SV, ERA, WHIP, SO) bottom row.
    """
```

**HTML structure per cell:**
```html
<div class="cb-cell">
  <div class="cb-cat">HR</div>
  <div class="cb-rank">4 → 6</div>
  <div class="cb-delta cb-up">+2</div>
</div>
```

Grid has a `cat-break-hdr` label for "Batting" spanning 5 columns, then 5 cells,
then "Pitching" label, then 5 cells. Note: for ERA/WHIP, a positive `delta_rank` still
means improvement (rank going up = good), so color logic is the same for all categories.

**Placement in `render_right_column`:** After the `st.dataframe` call:

```python
visible_players = view["player_name"].tolist()
if visible_players:
    detail_player = st.selectbox(
        "Player Detail", options=[""] + visible_players,
        placeholder="Select player for category breakdown…",
        label_visibility="collapsed", key="detail_player",
    )
    if detail_player:
        player_row = scored[scored["player_name"] == detail_player].iloc[0]
        st.html(_category_breakdown_html(player_row))
```

**New CSS classes:** `.cat-break` (grid, 5 cols), `.cat-break-hdr` (section label),
`.cb-cell` (white card), `.cb-cat` (9px mono), `.cb-rank` (14px mono),
`.cb-delta` (10px mono), `.cb-up` (accent green), `.cb-flat` (light gray), `.cb-down` (secondary red).

---

#### Feature 4: Undo Last Logged Result

**What:** Button to reverse the most recent auction log entry, restoring all session state.

**New function:**

```python
def _undo_last_result():
    """Reverse the most recent auction log entry.

    Mutates session state:
    - Pops last entry from auction_log
    - Removes player from taken dict
    - Decrements nom_counter
    - If winner was MY_TEAM: reverses budget_spent, hitters_won/pitchers_won,
      removes player from roster_slots
    """
```

**Implementation details:**
- Pop from `auction_log`, remove from `taken` dict, decrement `nom_counter`
- If winner == MY_TEAM: subtract price from `budget_spent`, decrement hitters/pitchers_won,
  find the player in `roster_slots` (where `is_keeper == False`) and clear that slot
- For pitcher detection: look up in `load_base_data()` (cached, always has all players):
  `is_p = base[base["player_name"] == player].iloc[0].get("pos_type") == "pitcher"`

**Cache invalidation:** Popping from `auction_log` changes `draft_key`, so `compute_live_msp`
naturally recomputes (or hits a previous cache entry from before the undone pick).

**Roster undo edge case:** If `try_place_player` displaced another player during placement,
the undo only removes the last-placed player. The displaced player stays in their new slot.
This is acceptable — the freed slot is available for the next placement.

**Placement in `render_nomination_bar`:** After the ticker HTML, add:

```python
if st.session_state.auction_log:
    undo_col, spacer = st.columns([1, 5])
    with undo_col:
        if st.button("↩ Undo Last", key="undo_btn", use_container_width=True):
            _undo_last_result()
            st.rerun()
```

---

### Phase B — Situational Awareness

#### Feature 3: Inflation Tracking

**What:** Track the gap between actual prices paid vs. Mkt $ (auction_value) to show
whether the room is running hot or cold.

**New function:**

```python
def compute_inflation(auction_log: list, base_data: pd.DataFrame) -> dict:
    """Compute market inflation/deflation from auction results.

    For each logged entry, looks up the player's auction_value (pre-computed market price)
    and computes the percentage premium/discount.

    Returns dict:
        overall_pct: float — mean (actual - mkt) / mkt
        hitter_pct: float — inflation for hitters only
        pitcher_pct: float — inflation for pitchers only
        total_surplus: float — sum of (actual - mkt)
        n_players: int — number of logged results with valid market prices
    """
```

**Implementation:** For each entry in `auction_log`, look up `auction_value` from `base_data`
(which is `load_base_data()`, cached). Compute `pct = (actual_price - mkt) / mkt`.
Split by `pos_type == "pitcher"` for hitter/pitcher breakdown. Return means.

Returns `{overall_pct: 0.0, ...}` when log is empty.

**New HTML builder:**

```python
def _inflation_html(inflation: dict) -> str:
    """Render inflation tracker card. Shows overall %, H/P split.
    Color: red if inflated (positive), green if deflated (negative)."""
```

HTML structure:
```html
<div class="inf-card">
  <div class="inf-val inf-hot">+14%</div>
  <div class="inf-lbl">Market Inflation</div>
  <div class="inf-split">
    <span class="inf-h">H: +18%</span>
    <span class="inf-p">P: +6%</span>
  </div>
</div>
```

**Placement:** In `render_left_column`, between Budget & Spots and Lineup Card.

**Signature change:** `render_left_column` gains `inflation: dict` parameter.
Computed in `main()`: `inflation = compute_inflation(st.session_state.auction_log, load_base_data())`

**New CSS classes:** `.inf-card` (white card), `.inf-val` (21px mono), `.inf-hot` (secondary red),
`.inf-cool` (accent green), `.inf-flat` (text color), `.inf-lbl` (9px uppercase),
`.inf-split` (flex row, 10px mono, mid color).

---

#### Feature 5: Field Standings Heatmap

**What:** Show all 10 teams' category ranks in a compact 10×10 grid with color-coded cells.

**New function:**

```python
def _standings_heatmap_html(standings: pd.DataFrame) -> str:
    """Build 10-team × 10-category heatmap HTML table.

    Rows = teams (sorted by total_pts descending).
    Columns = 10 categories + total pts.
    Cells colored by rank (green for high, red for low).
    MY_TEAM row highlighted with accent border.
    """
```

**Cell color helper:**

```python
def _rank_bg(rank: float) -> str:
    """Background-color CSS for a rank 1-10. Green (8-10), amber (4-7), red (1-3)."""
    if rank >= 8:
        return f"rgba(42, 157, 143, {0.15 + (rank - 8) * 0.1})"
    elif rank >= 4:
        return f"rgba(244, 162, 97, {0.08 + (rank - 4) * 0.04})"
    else:
        return f"rgba(193, 102, 107, {0.15 + (3 - rank) * 0.1})"
```

**Team name abbreviation constant:**

```python
TEAM_SHORT = {
    "Dancing With Dingos": "Dingos",
    "Gusteroids": "Gusteroids",
    "HAMMERHEADS": "Hammers",
    "Kerry & Mitch": "K&M",
    "Kosher Hogs": "K. Hogs",
    "Mean Machine": "Mean Mach",
    "On a Bender": "Bender",
    "R&R": "R&R",
    "Shrooms": "Shrooms",
    "Thunder & Lightning": "T&L",
}
```

**Placement:** In `render_left_column`, inside a collapsible expander below Category Ranks:

```python
with st.expander("Field Standings", expanded=False):
    st.html(_standings_heatmap_html(standings))
```

**Data source:** Uses `live_standings` already passed to `render_left_column`.

**New CSS classes:** `.hm-wrap` (bordered container), `table.hm-tbl` (10px mono),
`table.hm-tbl th` (8px uppercase), `tr.hm-mine` (light blue bg + left accent border),
`.hm-team` (left-aligned, truncated), `.hm-pts` (bold, border-left).

---

### Phase C — Scoring Refinements

#### Feature 9: Category Punt Detection

**What:** Detect categories where Gusteroids are too far behind to compete, and allow
toggling them as "punted" — which zeroes out their PVP contribution in TS.

**Design:** Hybrid approach. Auto-detect punt candidates, user confirms via multiselect.

**New session state:** `"punted_categories": set()` added to `init_state` defaults.

**New function:**

```python
def detect_punt_candidates(standings: pd.DataFrame, scored: pd.DataFrame) -> list[str]:
    """Identify categories that are punt candidates.

    A category is a punt candidate if:
    - Gusteroids' current rank <= 2 (bottom 20%)
    - AND the best available player for that category would improve rank by <= 1

    Returns list of category name strings.
    """
```

**Implementation:** For each category, check `rank_{cat}` from standings. If ≤ 2,
check `scored[f"delta_rank_{cat}"].max()`. If best delta ≤ 1, it's a punt candidate.

**Scoring pipeline modification — `score_players` gains `punted_cats` parameter:**

```python
def score_players(players, taken_names, budget_cap, punted_cats=None, ...):
    ...
    if punted_cats:
        # Use per-category delta_ranks instead of total msp
        adjusted_msp = sum(available[f"delta_rank_{cat}"] for cat in CATEGORIES if cat not in punted_cats)
        available["pvp_raw"] = (adjusted_msp * DOLLARS_PER_STANDINGS_PT).round(1)
    else:
        available["pvp_raw"] = (available["msp"] * DOLLARS_PER_STANDINGS_PT).round(1)
```

This works because `msp = sum(delta_rank_{cat})` — verified in `targeting/model.py` lines 401-410.
By summing only non-punted categories, we get adjusted MSP.

**UI placement:** In `render_left_column`, below Category Ranks. Compact multiselect:

```python
st.html('<div class="sec-hdr">Punt Categories</div>')
punt_suggestions = detect_punt_candidates(standings, scored)
punted = st.multiselect(
    "Punt categories", options=CATEGORIES,
    default=list(st.session_state.punted_categories),
    label_visibility="collapsed", key="punt_select",
    placeholder=f"Suggested: {', '.join(punt_suggestions)}" if punt_suggestions else "None suggested",
)
st.session_state.punted_categories = set(punted)
```

**Ordering note:** `score_players` reads `punted_categories` from session state (set by previous
interaction). On toggle, Streamlit reruns with updated punt set → scoring updates.

**Signature changes:**
- `score_players(... punted_cats=None)` — new parameter
- `render_left_column(... scored)` — needs `scored` for punt detection
- `main()` passes `punted_cats=st.session_state.get("punted_categories", set())` to `score_players`

---

#### Feature 6: Market-Adjusted MI

**What:** Adjust the MI component based on observed inflation from Feature 3, so MI
reflects revealed market preferences rather than pre-computed projections.

**Implementation:** In `score_players`, after computing `available`, before rescaling MI:

```python
def score_players(players, taken_names, budget_cap, punted_cats=None, inflation=None):
    ...
    # Market-adjusted MI (Feature 6)
    if inflation and inflation.get("n_players", 0) >= 3:
        hitter_inf = 1.0 + inflation.get("hitter_pct", 0.0)
        pitcher_inf = 1.0 + inflation.get("pitcher_pct", 0.0)
        adjusted_mkt = available["auction_value"].copy()
        is_p = available["is_pitcher"]
        adjusted_mkt[~is_p] *= hitter_inf
        adjusted_mkt[is_p] *= pitcher_inf
        available["mi"] = available["production_value"] - adjusted_mkt
    # else: use unadjusted MI from compute_live_msp
```

**Threshold:** Require ≥ 3 logged results before adjusting. Prevents wild swings from outliers.

**Interaction with bid_ceil:** Bid ceiling still uses unadjusted `auction_value`. MI adjusts
*which target to pursue* (scoring), not *how much to pay* (ceiling). This is intentional.

**Signature change:** `score_players(... inflation=None)` — new parameter.
Called in `main()`: `scored = score_players(players, taken_names, budget_cap, punted_cats=punted, inflation=inflation)`

---

### Phase D — Roster Construction Guidance

#### Feature 2: Positional Roster Balance

**What:** For each unfilled roster slot, show how many quality players can still fill it.
Flag critical slots (few options remaining).

**New function:**

```python
def compute_slot_scarcity(roster_slots: list, scored: pd.DataFrame, taken_names: set) -> list[dict]:
    """For each unfilled active slot, count eligible available players.

    Returns list of dicts:
        slot: str (e.g., "C", "SS", "P")
        slot_index: int (index in roster_slots)
        n_quality: int (available players in Solid tier or above)
        severity: str ("critical" if n_quality == 0, "tight" if <= 3, else "ok")
    """
```

**Implementation:** For each unfilled slot, use existing `is_eligible_for_slot()` and
`parse_eligibility()` to count how many `scored` rows can fill it. Quality = tier in
{Elite, Premium, Solid}.

**UI:** Enhance `_lineup_section_html` to show scarcity badges on empty slots. Change:
```html
<td class="lt-empty" colspan="2">—</td>
```
to:
```html
<td class="lt-empty">—</td>
<td class="lt-scar lt-scar-critical">2 left</td>
```

**Signature changes:**
- `_lineup_section_html(title, slots, slot_scarcity=None)` — new parameter
- `_lineup_html(slots, farm_players, slot_scarcity=None)` — passes through
- `render_left_column(... slot_scarcity)` — new parameter
- `main()` computes and passes: `slot_scarcity = compute_slot_scarcity(st.session_state.roster_slots, scored, taken_names)`

Internally, convert the list to a dict mapping `slot_index → scarcity_dict` for lookup.

**New CSS classes:** `.lt-scar` (8px mono, right-aligned), `.lt-scar-critical` (secondary red, bold),
`.lt-scar-tight` (amber), `.lt-scar-ok` (light gray).

---

#### Feature 11: Bid Target vs. Bid Ceiling

**What:** Add a recommended opening bid ("target") alongside the existing max bid ("ceiling").

**Implementation in `score_players`:** After computing `bid_ceil`:

```python
# Bid target: sweet spot price. Mkt$ + 25% of positive PVP premium.
target_pvp_boost = 0.25 * available["pvp_raw"].clip(lower=0)
available["bid_target"] = (auc + target_pvp_boost).clip(lower=1).round(0).astype(int)
available["bid_target"] = available[["bid_target", "bid_ceil"]].min(axis=1)  # target <= ceil
```

**UI change in `render_right_column`:** Replace single "Bid $" column with two columns:

```python
display = view[[
    "player_name", "position", "tier",
    "production_value", "auction_value",
    "pvp", "sp", "mi_sc", "ts",
    "bid_target", "bid_ceil",   # two bid columns
]].copy().rename(columns={
    ...
    "bid_target": "Tgt $",
    "bid_ceil":   "Ceil $",
})
```

Column configs:
```python
"Tgt $": st.column_config.NumberColumn("Tgt $", format="$%d",
    help="Bid target = Mkt$ + 25% of PVP premium. The recommended opening bid."),
"Ceil $": st.column_config.NumberColumn("Ceil $", format="$%d",
    help="Bid ceiling = Mkt$ + 50% × (PVP$ + SP$), capped at budget. Walk-away price."),
```

---

### Phase E — Strategic Tools

#### Feature 8: End-Game Projection Card

**What:** Surface projected final standings prominently at the top of the left column.

**New functions:**

```python
def _projections_html(standings: pd.DataFrame) -> str:
    """Render projected finish card for Gusteroids.

    Shows: projected place (1st-10th), total points, gap to next place up,
    and per-category rank badges.
    """

def _ordinal(n: int) -> str:
    """1 → '1st', 2 → '2nd', 3 → '3rd', etc."""
```

**Implementation:** From `live_standings`:
- `total_pts = standings[team == MY_TEAM]["total_pts"]`
- `place = rank of Gusteroids in standings sorted by total_pts descending`
- `gap = pts of team one place above - your pts`
- Per-category badges: compact inline badges showing `CAT:RANK` with rank coloring

**HTML structure:**
```html
<div class="proj-card">
  <div class="proj-place">3rd</div>
  <div class="proj-pts">62.0 pts</div>
  <div class="proj-gap">4.0 pts to 2nd</div>
  <div class="proj-cats">
    <span class="proj-badge rk-hi">R:8</span>
    <span class="proj-badge rk-lo">W:1</span>
    ...
  </div>
</div>
```

**Placement:** Top of `render_left_column`, before Budget & Spots.

**New CSS classes:** `.proj-card` (white card, centered), `.proj-place` (Source Serif 4, 28px, primary blue),
`.proj-pts` (14px mono), `.proj-gap` (10px, mid color), `.proj-cats` (flex wrap),
`.proj-badge` (8px mono, bg-card background).

---

#### Feature 7: Nomination Strategy Support

**What:** Identify players that are good to nominate (force rivals to spend) but you don't want.

**New function:**

```python
def compute_nomination_scores(scored: pd.DataFrame, standings: pd.DataFrame) -> pd.Series:
    """Compute nomination score for each available player.

    A good nomination target:
    - Has high overall value (rivals will bid)
    - Fills category weaknesses for rival teams (not for Gusteroids)
    - Low/negative MSP for Gusteroids (we don't need them)

    Logic:
    1. For each rival team, identify weak categories (rank <= 4)
    2. For each player, check which categories they help (sgp > 0.3 threshold)
    3. Count how many rivals need what this player provides
    4. rival_need_factor = count / n_rivals
    5. nom_score = production_value × rival_need_factor × (1 - normalized_msp)

    For ERA/WHIP (inverse): player helps if sgp < -0.3 (negative sgp = good pitcher).

    Returns pd.Series of nomination scores, indexed like scored.
    """
```

**UI integration:** Add a sort mode toggle in `render_right_column` filter row:

```python
fc1, fc2, fc3, fc4 = st.columns([3, 2, 4, 3])
# ... existing filters in fc1, fc2, fc3 ...
sort_mode = fc4.selectbox(
    "Sort by", options=["Targeting (TS)", "Nomination"],
    label_visibility="collapsed", key="sort_mode",
)
```

When "Nomination" is selected:
- Compute `nom_scores` and add as column
- Sort by nom_score descending instead of ts
- Show nom_score in the table (rename to "Nom")

**Signature change:** `render_right_column(scored, standings)` — needs `standings` for
rival weakness analysis.

**Data source:** Uses `live_standings` for rival team ranks. Uses `sgp_*` columns in `scored`
for category help detection (these are player-level, not team-specific).

---

## Implementation Summary

### New Functions (12 total)

| # | Function | Feature | Section |
|---|----------|---------|---------|
| 1 | `_category_breakdown_html(player_row)` | F1 | HTML builders |
| 2 | `_undo_last_result()` | F4 | After `_log_result` |
| 3 | `compute_inflation(auction_log, base_data)` | F3 | Scoring |
| 4 | `_inflation_html(inflation)` | F3 | HTML builders |
| 5 | `_standings_heatmap_html(standings)` | F5 | HTML builders |
| 6 | `_rank_bg(rank)` | F5 | Helper |
| 7 | `detect_punt_candidates(standings, scored)` | F9 | Scoring |
| 8 | `compute_slot_scarcity(roster_slots, scored, taken_names)` | F2 | Roster |
| 9 | `_projections_html(standings)` | F8 | HTML builders |
| 10 | `_ordinal(n)` | F8 | Helper |
| 11 | `compute_nomination_scores(scored, standings)` | F7 | Scoring |
| 12 | `TEAM_SHORT` dict | F5 | Constants |

### New Session State Keys

| Key | Type | Default | Feature |
|-----|------|---------|---------|
| `punted_categories` | `set` | `set()` | F9 |

### Modified Function Signatures

**`score_players`:**
```python
def score_players(players, taken_names, budget_cap,
                  punted_cats=None, inflation=None) -> pd.DataFrame
```

**`render_left_column`:**
```python
def render_left_column(standings, budget_left, eff_budget, h_open, p_open,
                       inflation, scored, slot_scarcity)
```

**`render_right_column`:**
```python
def render_right_column(scored, standings)
```

**`_lineup_html`:**
```python
def _lineup_html(slots, farm_players, slot_scarcity=None)
```

**`_lineup_section_html`:**
```python
def _lineup_section_html(title, slots, slot_scarcity=None)
```

### Revised `main()` Flow

```python
def main():
    inject_css()
    keepers = load_keepers()
    all_teams = sorted(keepers["team"].unique().tolist())
    init_state(keepers)

    # Live MSP (cached on draft state)
    draft_key = tuple(
        (e["player"], e["winner"], e["price"])
        for e in st.session_state.auction_log
    )
    players, live_standings = compute_live_msp(draft_key)

    # Budget calculations (unchanged)
    total_spent = st.session_state.salary_committed + st.session_state.budget_spent
    budget_left = TOTAL_BUDGET - total_spent
    h_open = HITTER_SLOTS - st.session_state.act_hitters - st.session_state.hitters_won
    p_open = PITCHER_SLOTS - st.session_state.act_pitchers - st.session_state.pitchers_won
    spots = h_open + p_open
    eff_budget = max(0, budget_left - spots)
    budget_cap = max(1, budget_left - max(0, spots - 1))

    # Inflation tracking (F3)
    base_data = load_base_data()
    inflation = compute_inflation(st.session_state.auction_log, base_data)

    # Scoring with punt + inflation adjustments (F6, F9)
    taken_names = set(st.session_state.taken.keys())
    punted = st.session_state.get("punted_categories", set())
    scored = score_players(players, taken_names, budget_cap,
                           punted_cats=punted, inflation=inflation)

    # Slot scarcity (F2)
    slot_scarcity = compute_slot_scarcity(
        st.session_state.roster_slots, scored, taken_names
    )

    # Page title (unchanged)
    st.html(...)

    # Nomination bar (F4: undo button added inside)
    render_nomination_bar(scored["player_name"].tolist(), all_teams, players)

    # Two-column layout
    left, right = st.columns([30, 70])
    with left:
        render_left_column(live_standings, budget_left, eff_budget, h_open, p_open,
                          inflation, scored, slot_scarcity)
    with right:
        render_right_column(scored, live_standings)
```

### Left Column Render Order (after all features)

1. **Projected Finish** (F8) — place, pts, gap, category badges
2. **Budget & Spots** — 4-card grid (unchanged)
3. **Inflation Tracker** (F3) — market %, H/P split
4. **My Lineup** — 15H + 11P + farm, with scarcity badges on empty slots (F2)
5. **Category Ranks** — 10-cat bar chart (unchanged)
6. **Punt Categories** (F9) — multiselect with auto-detected suggestions
7. **Field Standings** (F5) — collapsible 10×10 heatmap
8. **Full Auction Log** — collapsible table + CSV download (unchanged)

### Right Column Changes

1. **Filter row** gains 4th column: sort mode toggle (F7) — "Targeting (TS)" or "Nomination"
2. **Table** gains `Tgt $` column, `Bid $` renamed to `Ceil $` (F11)
3. **Below table**: player selectbox + category breakdown panel (F1)
4. When "Nomination" sort is active: shows Nom column, sorts by nomination score (F7)

---

## Verification

After implementing all features, verify:

1. **App boots clean:** `streamlit run auction/app.py` — no errors, all components render
2. **Category breakdown:** Select a player → 10-category grid shows rank deltas with correct colors
3. **Undo:** Log a result → click Undo → player reappears in available list, budget restores
4. **Inflation:** Log 3+ results at various prices → inflation card shows correct % and H/P split
5. **Field standings:** Expand heatmap → 10 teams × 10 categories with correct ranks and colors
6. **Punt detection:** With a category at rank 1-2, multiselect suggests it; toggling it changes TS for relevant players
7. **Market-adjusted MI:** After 3+ logged results with inflation, MI values shift for remaining players
8. **Slot scarcity:** With unfilled C or SS slots and few eligible players remaining, lineup shows "N left" badge
9. **Bid target vs ceiling:** Two bid columns in table, target always ≤ ceiling
10. **End-game projection:** Card at top of left column shows projected place, updates as players are drafted
11. **Nomination mode:** Toggle sort to "Nomination" → table reorders by nomination score, high-value players you don't need sort to top
12. **Dynamic updates:** Log a draft pick for another team → all components (standings, category ranks, projection, inflation, MSP scores) update correctly

### Dry Run Test

Simulate the user's original scenario:
1. Log Gilbert $52 → Gusteroids, Valdez $46 → Gusteroids, Kirby $42 → Gusteroids
2. Verify: pitching category ranks improve, projected finish improves, Dylan Cease drops in TS
3. Verify: "Nomination" mode shows elite pitchers at top (rivals need them, you don't)
4. Verify: hitter slots show "N left" badges, SS/C slots flag as tight if few options remain
5. Verify: punt detection suggests W or SO if rank is still low despite 3 starters
6. Click Undo → Kirby removed, TS recalculates, pitching ranks drop back

---

## Files Modified

- `auction/app.py` — All 10 features implemented here (single file)
- `plans/05-auction-targeting.md` — Update with cross-reference to Plan 06

## Files Read (not modified)

- `targeting/model.py` — Reference for MSP data structures, delta_rank computation
- `data/valuations_atc_2026.csv` — Source data schema (sgp_*, position, pos_type)
- `data/preauction_rosters_2026.csv` — Keeper roster structure
- `data/msp_projected_standings_2026.csv` — Standings schema reference
