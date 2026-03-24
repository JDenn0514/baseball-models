"""Generate self-contained sortable HTML tables from valuation CSVs."""

import csv
import json
import html as html_mod


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def build_html(title, subtitle_text, rows, columns, positions, type_key, type_values):
    """Build a self-contained HTML file with embedded data."""

    all_keys = {c["key"] for c in columns}
    all_keys.add(type_key)
    slim_rows = []
    for r in rows:
        obj = {}
        for k in all_keys:
            v = r.get(k, "")
            obj[k] = v
        slim_rows.append(obj)

    data_json = json.dumps(slim_rows, separators=(",", ":"))
    columns_json = json.dumps(columns, separators=(",", ":"))
    positions_json = json.dumps(sorted(positions), separators=(",", ":"))
    type_values_json = json.dumps(type_values, separators=(",", ":"))

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_mod.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --primary: #3A6EA5;
  --secondary: #C1666B;
  --accent: #2A9D8F;
  --bg: #faf9f5;
  --bg-sidebar: #f4f3ef;
  --grid: #ededeb;
  --border: #e0dfdb;
  --text: #2d2d2d;
  --mid: #666666;
  --light: #999999;
  --green: #2A9D8F;
  --red: #C1666B;
  --name-col-width: 180px;
  --sidebar-width: 220px;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: 'DM Sans', -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}}

/* ── Layout ── */
.page {{
  display: flex;
  min-height: 100vh;
}}

/* ── Sidebar ── */
.sidebar {{
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--grid);
  padding: 32px 16px 24px;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  overflow-y: auto;
  z-index: 10;
  transition: transform 0.25s ease;
}}

.sidebar.collapsed {{
  transform: translateX(calc(-1 * var(--sidebar-width)));
}}

.sidebar-toggle {{
  position: fixed;
  top: 36px;
  left: calc(var(--sidebar-width) + 6px);
  z-index: 20;
  width: 24px;
  height: 24px;
  background: var(--bg);
  border: 1px solid var(--grid);
  border-radius: 4px;
  color: var(--light);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: left 0.25s ease, color 0.15s;
}}

.sidebar-toggle:hover {{ color: var(--text); }}

.sidebar.collapsed + .sidebar-toggle {{ left: 10px; }}

.sidebar-heading {{
  font-family: 'DM Sans', sans-serif;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.8px;
  color: var(--light);
  margin-bottom: 14px;
}}

.sidebar-actions {{
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
}}

.sidebar-actions button {{
  flex: 1;
  padding: 5px 0;
  font-size: 10px;
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: var(--light);
  background: var(--bg);
  border: 1px solid var(--grid);
  border-radius: 4px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}}

.sidebar-actions button:hover {{
  color: var(--text);
  border-color: var(--primary);
}}

.col-list {{ list-style: none; }}

.col-list li {{ margin-bottom: 1px; }}

.col-list label {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12.5px;
  color: var(--mid);
  transition: background 0.12s, color 0.12s;
  user-select: none;
}}

.col-list label:hover {{
  background: var(--bg);
  color: var(--text);
}}

.col-list input[type="checkbox"] {{
  appearance: none;
  width: 14px;
  height: 14px;
  border: 1.5px solid var(--border);
  border-radius: 3px;
  background: var(--bg);
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
  transition: border-color 0.12s, background 0.12s;
}}

.col-list input[type="checkbox"]:checked {{
  background: var(--primary);
  border-color: var(--primary);
}}

.col-list input[type="checkbox"]:checked::after {{
  content: "";
  position: absolute;
  top: 1px;
  left: 4px;
  width: 4px;
  height: 7px;
  border: solid white;
  border-width: 0 1.5px 1.5px 0;
  transform: rotate(45deg);
}}

/* ── Main ── */
.main {{
  margin-left: var(--sidebar-width);
  flex: 1;
  padding: 40px 48px 48px;
  max-width: 100%;
  overflow: hidden;
  transition: margin-left 0.25s ease;
}}

.sidebar.collapsed ~ .main {{ margin-left: 0; }}

.header {{
  margin-bottom: 28px;
}}

.header h1 {{
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.3px;
  line-height: 1.2;
}}

.header .subtitle {{
  font-size: 13px;
  color: var(--light);
  margin-top: 4px;
  font-weight: 400;
}}

/* ── Controls ── */
.controls {{
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 20px;
}}

.search-box {{
  position: relative;
  flex: 0 1 240px;
}}

.search-box input {{
  width: 100%;
  padding: 7px 10px 7px 32px;
  background: white;
  border: 1px solid var(--grid);
  border-radius: 5px;
  color: var(--text);
  font-family: 'DM Sans', sans-serif;
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s;
}}

.search-box input:focus {{
  border-color: var(--primary);
}}

.search-box::before {{
  content: "\\2315";
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 15px;
  color: var(--light);
  pointer-events: none;
}}

.pill-group {{
  display: flex;
  gap: 0;
  border: 1px solid var(--grid);
  border-radius: 5px;
  overflow: hidden;
}}

.pill {{
  padding: 7px 12px;
  font-family: 'DM Sans', sans-serif;
  font-size: 11.5px;
  font-weight: 500;
  color: var(--light);
  background: white;
  border: none;
  cursor: pointer;
  transition: all 0.12s;
  border-right: 1px solid var(--grid);
}}

.pill:last-child {{ border-right: none; }}

.pill:hover {{
  color: var(--text);
  background: var(--bg-sidebar);
}}

.pill.active {{
  color: white;
  background: var(--primary);
}}

.count-badge {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  color: var(--light);
  margin-left: auto;
}}

/* ── Table ── */
.table-outer {{
  border: 1px solid var(--grid);
  border-radius: 6px;
  overflow: hidden;
  background: white;
}}

.table-scroll {{
  overflow-x: auto;
  overflow-y: auto;
  max-height: calc(100vh - 240px);
}}

table {{
  border-collapse: separate;
  border-spacing: 0;
  font-size: 13px;
  min-width: 100%;
}}

thead {{ position: sticky; top: 0; z-index: 4; }}

/* Player name header — sticky left */
th.name-header {{
  position: sticky;
  left: 0;
  z-index: 6;
  min-width: var(--name-col-width);
  max-width: var(--name-col-width);
}}

th {{
  background: var(--text);
  padding: 9px 12px;
  text-align: left;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10.5px;
  font-weight: 500;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: white;
  border-bottom: none;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  transition: background 0.12s;
}}

th:hover {{ background: #444444; }}

th.sorted {{ background: var(--primary); }}

th .sort-arrow {{
  display: inline-block;
  margin-left: 3px;
  font-size: 9px;
  opacity: 0;
  transition: opacity 0.12s;
}}

th:hover .sort-arrow,
th.sorted .sort-arrow {{ opacity: 1; }}

th.num-col {{ text-align: right; }}

td {{
  padding: 7px 12px;
  border-bottom: 1px solid var(--grid);
  white-space: nowrap;
  color: var(--mid);
  font-size: 13px;
}}

td.num {{
  text-align: right;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--mid);
}}

/* Sticky player name column */
td.player-name {{
  font-weight: 600;
  color: var(--text);
  position: sticky;
  left: 0;
  z-index: 2;
  min-width: var(--name-col-width);
  max-width: var(--name-col-width);
  background: white;
  border-right: 1px solid var(--grid);
  font-size: 13px;
}}

/* Alternating rows */
tr:nth-child(even) td {{ background: var(--bg); }}
tr:nth-child(even) td.player-name {{ background: var(--bg); }}

/* Hover */
tr:hover td {{ background: #eef4fa !important; }}
tr:hover td.player-name {{ background: #eef4fa !important; }}

/* Value colors */
td.val-positive {{ color: var(--green); font-weight: 500; }}
td.val-negative {{ color: var(--red); font-weight: 500; }}
td.val-highlight {{ color: var(--primary); font-weight: 600; }}
td.type-hitter {{ color: var(--primary); }}
td.type-pitcher {{ color: var(--secondary); }}

.empty-state {{
  text-align: center;
  padding: 40px 24px;
  color: var(--light);
  font-size: 13px;
}}
</style>
</head>
<body>

<div class="page">
  <nav class="sidebar" id="sidebar">
    <div class="sidebar-heading">Columns</div>
    <div class="sidebar-actions">
      <button id="btnShowAll">Show All</button>
      <button id="btnHideAll">Hide All</button>
    </div>
    <ul class="col-list" id="colList"></ul>
  </nav>

  <button class="sidebar-toggle" id="sidebarToggle" title="Toggle sidebar">&#9776;</button>

  <div class="main">
    <div class="header">
      <h1>{html_mod.escape(title)}</h1>
      <div class="subtitle" id="subtitle">{html_mod.escape(subtitle_text)}</div>
    </div>

    <div class="controls">
      <div class="search-box">
        <input type="text" id="search" placeholder="Search players, teams\u2026">
      </div>
      <div class="pill-group" id="typeFilter"></div>
      <div class="pill-group" id="posFilter"></div>
      <span class="count-badge" id="count"></span>
    </div>

    <div class="table-outer">
      <div class="table-scroll">
        <table>
          <thead><tr id="headerRow"></tr></thead>
          <tbody id="tbody"></tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<script>
const DATA = {data_json};
const COLUMNS = {columns_json};
const POSITIONS = {positions_json};
const TYPE_KEY = "{type_key}";
const TYPE_VALUES = {type_values_json};

let visibleCols = new Set(COLUMNS.filter(c => c.show !== false).map(c => c.key));
let sortCol = COLUMNS.find(c => c.defaultSort)?.key || COLUMNS[COLUMNS.length - 1].key;
let sortAsc = false;
let filterType = "";
let filterPos = "";

DATA.forEach(r => {{
  COLUMNS.forEach(c => {{
    if (c.type === "num") {{
      const v = r[c.key];
      r[c.key] = (v === "" || v === undefined || v === null) ? null : parseFloat(v);
    }}
  }});
}});

function clearEl(el) {{ while (el.firstChild) el.removeChild(el.firstChild); }}

function init() {{
  buildSidebar();
  buildTypeFilter();
  buildPosFilter();
  buildHeader();
  render();

  document.getElementById("search").addEventListener("input", render);
  document.getElementById("sidebarToggle").addEventListener("click", () => {{
    document.getElementById("sidebar").classList.toggle("collapsed");
  }});
  document.getElementById("btnShowAll").addEventListener("click", () => toggleAllCols(true));
  document.getElementById("btnHideAll").addEventListener("click", () => toggleAllCols(false));
}}

function buildSidebar() {{
  const list = document.getElementById("colList");
  clearEl(list);
  COLUMNS.forEach(c => {{
    const li = document.createElement("li");
    const label = document.createElement("label");
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = visibleCols.has(c.key);
    cb.addEventListener("change", () => {{
      if (cb.checked) visibleCols.add(c.key);
      else visibleCols.delete(c.key);
      buildHeader();
      render();
    }});
    label.appendChild(cb);
    const span = document.createElement("span");
    span.textContent = c.label;
    label.appendChild(span);
    li.appendChild(label);
    list.appendChild(li);
  }});
}}

function toggleAllCols(show) {{
  if (show) visibleCols = new Set(COLUMNS.map(c => c.key));
  else visibleCols = new Set(["player_name"]);
  buildSidebar();
  buildHeader();
  render();
}}

function buildTypeFilter() {{
  const group = document.getElementById("typeFilter");
  clearEl(group);
  const allBtn = document.createElement("button");
  allBtn.className = "pill active";
  allBtn.textContent = "All";
  allBtn.addEventListener("click", () => {{ filterType = ""; setActivePill(group, allBtn); render(); }});
  group.appendChild(allBtn);
  Object.entries(TYPE_VALUES).forEach(([label, val]) => {{
    const btn = document.createElement("button");
    btn.className = "pill";
    btn.textContent = label;
    btn.addEventListener("click", () => {{ filterType = val; setActivePill(group, btn); render(); }});
    group.appendChild(btn);
  }});
}}

function buildPosFilter() {{
  const group = document.getElementById("posFilter");
  clearEl(group);
  const allBtn = document.createElement("button");
  allBtn.className = "pill active";
  allBtn.textContent = "All Pos";
  allBtn.addEventListener("click", () => {{ filterPos = ""; setActivePill(group, allBtn); render(); }});
  group.appendChild(allBtn);
  POSITIONS.forEach(p => {{
    const btn = document.createElement("button");
    btn.className = "pill";
    btn.textContent = p;
    btn.addEventListener("click", () => {{ filterPos = p; setActivePill(group, btn); render(); }});
    group.appendChild(btn);
  }});
}}

function setActivePill(group, activeBtn) {{
  group.querySelectorAll(".pill").forEach(b => b.classList.remove("active"));
  activeBtn.classList.add("active");
}}

function buildHeader() {{
  const tr = document.getElementById("headerRow");
  clearEl(tr);
  COLUMNS.filter(c => visibleCols.has(c.key)).forEach(c => {{
    const th = document.createElement("th");
    if (c.type === "num") th.className = "num-col";
    if (c.key === "player_name") th.classList.add("name-header");
    if (c.key === sortCol) th.classList.add("sorted");
    const text = document.createTextNode(c.label + " ");
    th.appendChild(text);
    const arrow = document.createElement("span");
    arrow.className = "sort-arrow";
    arrow.textContent = (c.key === sortCol) ? (sortAsc ? "\u25B2" : "\u25BC") : "\u25BC";
    th.appendChild(arrow);
    th.addEventListener("click", () => {{
      if (sortCol === c.key) sortAsc = !sortAsc;
      else {{ sortCol = c.key; sortAsc = c.type === "str"; }}
      buildHeader();
      render();
    }});
    tr.appendChild(th);
  }});
}}

function render() {{
  const q = document.getElementById("search").value.toLowerCase();
  let filtered = DATA.filter(r => {{
    if (filterType && r[TYPE_KEY] !== filterType) return false;
    if (filterPos) {{
      const pos = (r.position || r.eligibility || "");
      if (!pos.includes(filterPos)) return false;
    }}
    if (q) {{
      const s = COLUMNS.filter(c => c.type === "str").map(c => (r[c.key] || "").toLowerCase()).join(" ");
      if (!s.includes(q)) return false;
    }}
    return true;
  }});

  const col = COLUMNS.find(c => c.key === sortCol);
  filtered.sort((a, b) => {{
    let va = a[sortCol], vb = b[sortCol];
    if (va == null && vb == null) return 0;
    if (va == null) return 1;
    if (vb == null) return -1;
    if (col && col.type === "str") {{ va = (va || "").toLowerCase(); vb = (vb || "").toLowerCase(); }}
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  }});

  const tbody = document.getElementById("tbody");
  clearEl(tbody);

  if (filtered.length === 0) {{
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = visibleCols.size;
    td.className = "empty-state";
    td.textContent = "No players match your filters";
    tr.appendChild(td);
    tbody.appendChild(tr);
  }} else {{
    const visCols = COLUMNS.filter(c => visibleCols.has(c.key));
    filtered.forEach(r => {{
      const tr = document.createElement("tr");
      visCols.forEach(c => {{
        const td = document.createElement("td");
        if (c.key === "player_name") {{
          td.className = "player-name";
          td.textContent = r[c.key] || "";
        }} else if (c.type === "num") {{
          td.className = "num";
          if (r[c.key] != null) {{
            td.textContent = r[c.key].toFixed(c.dec != null ? c.dec : 1);
            if (c.colored) td.classList.add(r[c.key] >= 0 ? "val-positive" : "val-negative");
            if (c.highlight) td.classList.add("val-highlight");
          }}
        }} else {{
          td.textContent = r[c.key] || "";
          if (c.key === "pos_type" || c.key === TYPE_KEY) {{
            const val = r[c.key];
            if (val === "hitter" || val === "False") td.classList.add("type-hitter");
            else if (val === "pitcher" || val === "True") td.classList.add("type-pitcher");
          }}
        }}
        tr.appendChild(td);
      }});
      tbody.appendChild(tr);
    }});
  }}

  document.getElementById("count").textContent = filtered.length + " / " + DATA.length;
}}

init();
</script>
</body>
</html>'''


# ─── Build 2026 Projections table ───
rows_2026 = read_csv("data/valuations_atc_2026.csv")
cols_2026 = [
    {"key": "player_name", "label": "Player", "type": "str"},
    {"key": "team", "label": "Team", "type": "str"},
    {"key": "pos_type", "label": "Type", "type": "str"},
    {"key": "position", "label": "Pos", "type": "str"},
    {"key": "PA", "label": "PA", "type": "num", "dec": 0},
    {"key": "IP", "label": "IP", "type": "num", "dec": 0},
    {"key": "R", "label": "R", "type": "num", "dec": 1},
    {"key": "HR", "label": "HR", "type": "num", "dec": 1},
    {"key": "RBI", "label": "RBI", "type": "num", "dec": 1},
    {"key": "SB", "label": "SB", "type": "num", "dec": 1},
    {"key": "AVG", "label": "AVG", "type": "num", "dec": 3},
    {"key": "W", "label": "W", "type": "num", "dec": 1},
    {"key": "SV", "label": "SV", "type": "num", "dec": 1},
    {"key": "ERA", "label": "ERA", "type": "num", "dec": 2},
    {"key": "WHIP", "label": "WHIP", "type": "num", "dec": 3},
    {"key": "SO", "label": "SO", "type": "num", "dec": 0},
    {"key": "total_sgp", "label": "SGP", "type": "num", "dec": 2},
    {"key": "par", "label": "PAR", "type": "num", "dec": 2, "highlight": True},
    {"key": "dollar_value", "label": "$Value", "type": "num", "dec": 1, "highlight": True, "defaultSort": True},
]
base_pos_2026 = set()
for r in rows_2026:
    if r.get("position"):
        for part in r["position"].split("/"):
            base_pos_2026.add(part)
base_pos_2026 = sorted(base_pos_2026 - {"DH"})

html_2026 = build_html(
    title="2026 ATC Projections",
    subtitle_text="Moonlight Graham League \u00b7 ATC projection system \u00b7 SGP valuation model",
    rows=rows_2026,
    columns=cols_2026,
    positions=base_pos_2026,
    type_key="pos_type",
    type_values={"Hitters": "hitter", "Pitchers": "pitcher"},
)

with open("reports/valuations_atc_2026.html", "w") as f:
    f.write(html_2026)
print("Wrote reports/valuations_atc_2026.html")


# ─── Build 2024 Historical Valuations table ───
rows_2024 = read_csv("data/player_valuations_2024.csv")
cols_2024 = [
    {"key": "player_name", "label": "Player", "type": "str"},
    {"key": "fantasy_team", "label": "Fantasy Team", "type": "str"},
    {"key": "mlb_team", "label": "MLB", "type": "str"},
    {"key": "position", "label": "Pos", "type": "str"},
    {"key": "salary", "label": "Salary", "type": "num", "dec": 0},
    {"key": "contract_year", "label": "Contract", "type": "str"},
    {"key": "AB", "label": "AB", "type": "num", "dec": 0},
    {"key": "IP", "label": "IP", "type": "num", "dec": 0},
    {"key": "R", "label": "R", "type": "num", "dec": 0},
    {"key": "HR", "label": "HR", "type": "num", "dec": 0},
    {"key": "RBI", "label": "RBI", "type": "num", "dec": 0},
    {"key": "SB", "label": "SB", "type": "num", "dec": 0},
    {"key": "AVG", "label": "AVG", "type": "num", "dec": 3},
    {"key": "W", "label": "W", "type": "num", "dec": 0},
    {"key": "SV", "label": "SV", "type": "num", "dec": 0},
    {"key": "ERA", "label": "ERA", "type": "num", "dec": 2},
    {"key": "WHIP", "label": "WHIP", "type": "num", "dec": 3},
    {"key": "SO", "label": "SO", "type": "num", "dec": 0},
    {"key": "total_sgp", "label": "SGP", "type": "num", "dec": 2},
    {"key": "par", "label": "PAR", "type": "num", "dec": 2, "highlight": True, "defaultSort": True},
    {"key": "production_value", "label": "Prod $", "type": "num", "dec": 1, "highlight": True},
    {"key": "auction_value", "label": "Auction $", "type": "num", "dec": 1, "highlight": True},
    {"key": "surplus", "label": "Surplus", "type": "num", "dec": 1, "colored": True},
]
base_pos_2024 = sorted({r["position"] for r in rows_2024 if r.get("position")})

html_2024 = build_html(
    title="2024 Historical Valuations",
    subtitle_text="Moonlight Graham League \u00b7 Actual stats \u00b7 SGP valuation model",
    rows=rows_2024,
    columns=cols_2024,
    positions=base_pos_2024,
    type_key="is_pitcher",
    type_values={"Hitters": "False", "Pitchers": "True"},
)

with open("reports/player_valuations_2024.html", "w") as f:
    f.write(html_2024)
print("Wrote reports/player_valuations_2024.html")
