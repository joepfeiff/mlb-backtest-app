import streamlit as st
import pandas as pd
import json
from espn_api import ESPN  # Fixed import here

@st.cache_data(show_spinner=False)
def fetch_scoreboard():
    espn = ESPN()
    return espn.get_scoreboard('mlb')

@st.cache_data(show_spinner=False)
def fetch_game_stats(game):
    return game.boxscore()

def run_backtest(picks_df, boxscore):
    stats_dict = {}
    for player in boxscore.home_players + boxscore.away_players:
        key = (player.team.abbreviation, player.name)
        stats_dict[key] = player.stats

    results = []
    for _, pick in picks_df.iterrows():
        key = (pick['team'], pick['player_name'])
        stat = stats_dict.get(key, None)
        if stat is None:
            outcome = "No Data"
        else:
            prop = pick['prop_type'].lower()
            outcome = "loss"
            if "hits o" in prop:
                outcome = "win" if stat.get('hits', 0) >= 1 else "loss"
            elif "rbi o" in prop:
                outcome = "win" if stat.get('rbi', 0) >= 1 else "loss"
            elif "tb o" in prop:
                tb = (stat.get('singles', 0) +
                      2 * stat.get('doubles', 0) +
                      3 * stat.get('triples', 0) +
                      4 * stat.get('homeRuns', 0))
                outcome = "win" if tb >= 2 else "loss"
            elif "hr o" in prop:
                outcome = "win" if stat.get('homeRuns', 0) >= 1 else "loss"
            elif "strikeout" in prop or "ks o" in prop:
                outcome = "win" if stat.get('strikeOuts', 0) >= pick.get('line', 0) else "loss"
            # Add more prop types as needed

        results.append({
            "Player": pick['player_name'],
            "Prop": pick['prop_type'],
            "Tier": pick['tier'],
            "Result": outcome
        })
    return pd.DataFrame(results)

def main():
    st.title("MLB MCP Backtest App")

    uploaded_file = st.file_uploader("Upload MCP Picks JSON", type="json")
    if uploaded_file:
        picks_json = json.load(uploaded_file)
        picks_df = pd.json_normalize(picks_json["picks"])

        st.write("Fetching today's MLB scoreboard...")
        scoreboard = fetch_scoreboard()

        game_options = {f"{g.away_team} @ {g.home_team}": g for g in scoreboard}
        selected_game = st.selectbox("Select Game", list(game_options.keys()))

        if st.button("Run Backtest"):
            boxscore = fetch_game_stats(game_options[selected_game])
            results_df = run_backtest(picks_df, boxscore)
            st.dataframe(results_df)

if __name__ == "__main__":
    main()