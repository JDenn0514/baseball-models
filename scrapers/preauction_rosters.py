"""
Scrape 2026 pre-auction rosters from OnRoto.

Fetches the "today" roster page showing keepers and calculates each team's
available auction budget ($360 total minus keeper salaries).

Outputs:
  - data/preauction_rosters_2026.csv  — player-level roster data
  - Prints a team budget summary to stdout
"""

import pandas as pd

from scrapers.auth import login, BASE_URL, LEAGUE
from scrapers.rosters import parse_roster_page


def fetch_today_roster(session, session_id) -> str:
    """Fetch the current pre-auction roster page."""
    url = (
        f"{BASE_URL}/baseball/webnew/display_roster.pl?"
        f"{LEAGUE}+0+all+today&session_id={session_id}"
    )
    resp = session.get(url)
    resp.raise_for_status()
    return resp.text


def main():
    print("Logging in...")
    session, session_id = login()
    print(f"Logged in. Session ID: {session_id[:8]}...")

    print("Fetching pre-auction rosters...")
    html = fetch_today_roster(session, session_id)

    # Save raw HTML for debugging
    with open("data/preauction_rosters_2026.html", "w") as f:
        f.write(html)
    print("Saved raw HTML to data/preauction_rosters_2026.html")

    # Parse using existing roster parser (year=2026)
    records = parse_roster_page(html, year=2026)

    if not records:
        print("ERROR: No roster data found. Check the HTML file for issues.")
        return

    df = pd.DataFrame(records)

    # Reorder columns
    columns = [
        "year", "team", "player_name", "player_id", "mlb_team",
        "position", "contract_year", "salary", "status", "eligibility",
    ]
    df = df[columns]

    # Save player-level data
    output_path = "data/preauction_rosters_2026.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} players to {output_path}")

    # Team budget summary
    TOTAL_BUDGET = 360
    print("\n" + "=" * 60)
    print("TEAM BUDGET SUMMARY")
    print("=" * 60)

    team_summary = []
    for team in sorted(df["team"].unique()):
        team_df = df[df["team"] == team]
        n_keepers = len(team_df[team_df["salary"] > 0])
        total_salary = team_df["salary"].sum()
        available = TOTAL_BUDGET - total_salary
        roster_spots_used = len(team_df)

        team_summary.append({
            "team": team,
            "keepers": n_keepers,
            "salary_committed": total_salary,
            "budget_available": available,
            "roster_spots": roster_spots_used,
        })

        print(f"\n{team}:")
        print(f"  Keepers: {n_keepers}  |  Salary committed: ${total_salary}  |  Available: ${available}")
        if n_keepers > 0:
            keepers = team_df[team_df["salary"] > 0].sort_values("salary", ascending=False)
            for _, p in keepers.iterrows():
                print(f"    ${p['salary']:>3}  {p['player_name']:<25} {p['position']:<4} {p['contract_year']}")

    summary_df = pd.DataFrame(team_summary)
    print("\n" + "=" * 60)
    print(f"League totals: {summary_df['keepers'].sum()} keepers, "
          f"${summary_df['salary_committed'].sum()} committed, "
          f"${summary_df['budget_available'].sum()} available across {len(summary_df)} teams")


if __name__ == "__main__":
    main()
