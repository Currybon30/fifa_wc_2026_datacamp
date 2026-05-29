import numpy as np
import pandas as pd


# =========================
# SIMULATE MATCH FUNCTIONS
# =========================
def simulate_match(match_id, cache, knockout=False, et_total=0.8):
    c = cache[match_id]

    # =========================
    # 90 MIN SIMULATION
    # =========================
    home_goals = np.random.poisson(max(0, c["lam_home_goal"]))
    away_goals = np.random.poisson(max(0, c["lam_away_goal"]))

    home_yellow = np.random.poisson(max(0, c["lam_home_yellow"]))
    away_yellow = np.random.poisson(max(0, c["lam_away_yellow"]))

    home_corners = np.random.poisson(max(0, c["lam_home_corner"]))
    away_corners = np.random.poisson(max(0, c["lam_away_corner"]))

    home_red = int(np.random.random() < max(0, c["lam_home_red"]))
    away_red = int(np.random.random() < max(0, c["lam_away_red"]))

    # =========================
    # EXTRA TIME
    # =========================
    is_penalty = False
    penalty_winner = None

    if knockout and home_goals == away_goals:

        total = c["lam_home_goal"] + c["lam_away_goal"]
        if total <= 0:
            h_share = 0.5
        else:
            h_share = c["lam_home_goal"] / total

        lam_home_et = et_total * h_share
        lam_away_et = et_total * (1 - h_share)

        et_home = np.random.poisson(lam_home_et)
        et_away = np.random.poisson(lam_away_et)

        home_goals += et_home
        away_goals += et_away

        if et_home == et_away:
            is_penalty = True
            penalty_winner = (
                c["home_team"] if np.random.random() < 0.5 else c["away_team"]
            )

    # =========================
    # RESULT
    # =========================
    if home_goals > away_goals:
        result_str = "W"
    elif home_goals < away_goals:
        result_str = "L"
    else:
        result_str = "D"

    if is_penalty:
        result_str = "W" if penalty_winner == c["home_team"] else "L"

    return {
        "home_goals": home_goals,
        "away_goals": away_goals,
        "home_yellow": home_yellow,
        "away_yellow": away_yellow,
        "home_red": home_red,
        "away_red": away_red,
        "home_corners": home_corners,
        "away_corners": away_corners,
        "penalty": is_penalty,
        "result_str": result_str
    }


# =========================
# SIMULATE GROUP STAGE FUNCTION
# =========================
def simulate_group_stage(stage_table_df, cache, simulate_match_fn, verbose=False):
    """
    Simulate group stage from a match schedule dataframe.
    """

    groups = stage_table_df["group"].unique()

    # =========================
    # PRECOMPUTE GROUP DATA
    # =========================
    group_matches_map = {
        g: stage_table_df[stage_table_df["group"] == g]
        for g in groups
    }

    group_teams_map = {
        g: pd.unique(df[["home_team", "away_team"]].values.ravel())
        for g, df in group_matches_map.items()
    }

    # =========================
    # INIT STATS
    # =========================
    group_stats = {}

    for g in groups:
        group_stats[g] = {
            t: {
                "pts": 0, "gf": 0, "ga": 0, "gd": 0,
                "w": 0, "d": 0, "l": 0,
                "yc": 0, "rc": 0, "corners": 0
            }
            for t in group_teams_map[g]
        }

    # store results for replay / debugging
    results = []

    rows = list(zip(
        stage_table_df["match_id"],
        stage_table_df["group"],
        stage_table_df["home_team"],
        stage_table_df["away_team"]
    ))

    # =========================
    # SIMULATE EACH MATCH
    # =========================
    for match_id, group, home_team, away_team in rows:

        stats = group_stats[group]
        group_teams = group_teams_map[group]

        result = simulate_match_fn(
            match_id,
            cache
        )

        home = home_team
        away = away_team

        home_goals = result["home_goals"]
        away_goals = result["away_goals"]
        home_yellow = result["home_yellow"]
        away_yellow = result["away_yellow"]
        home_red = result["home_red"]
        away_red = result["away_red"]
        home_corners = result["home_corners"]
        away_corners = result["away_corners"]
        result_str = result["result_str"]

        # =========================
        # UPDATE STATS
        # =========================

        # goals for / against
        stats[home]["gf"] += home_goals
        stats[home]["ga"] += away_goals

        stats[away]["gf"] += away_goals
        stats[away]["ga"] += home_goals

        # yellow cards
        stats[home]["yc"] += home_yellow
        stats[away]["yc"] += away_yellow

        # red cards
        stats[home]["rc"] += home_red
        stats[away]["rc"] += away_red

        # corners
        stats[home]["corners"] += home_corners
        stats[away]["corners"] += away_corners

        winning_team = ""
        # result
        if result_str == "W":
            stats[home]["pts"] += 3
            stats[home]["w"] += 1
            stats[away]["l"] += 1
            winning_team = "home"
        elif result_str == "L":
            stats[away]["pts"] += 3
            stats[away]["w"] += 1
            stats[home]["l"] += 1
            winning_team = "away"
        else:
            stats[home]["pts"] += 1
            stats[away]["pts"] += 1
            stats[home]["d"] += 1
            stats[away]["d"] += 1
            winning_team = "draw"

        # =========================
        # STORE RESULT
        # =========================
        result_record = {
            "match_id": int(match_id),
            "group": group,
            "home_team": home,
            "away_team": away,
            "predicted_home_goals": home_goals,
            "predicted_away_goals": away_goals,
            "yellow_cards": home_yellow + away_yellow,
            "red_cards": home_red + away_red,
            "corners": home_corners + away_corners,
            "winning_team": winning_team  # home, away, or draw
        }
        results.append(result_record)

        # =========================
        # GOAL DIFFERENCE
        # =========================
        stats[home]["gd"] = stats[home]["gf"] - stats[home]["ga"]
        stats[away]["gd"] = stats[away]["gf"] - stats[away]["ga"]

        # =========================
        # PRINT STATS
        # =========================
        if verbose:
            # =========================
            # SORT TEAMS - FIFA tiebreakers: Points → Goal Difference → Goals Scored
            # =========================
            ranking = sorted(
                group_teams,
                key=lambda x: (
                    stats[x]["pts"],
                    stats[x]["gd"],
                    stats[x]["gf"]
                ),
                reverse=True  # sort in descending order
            )

            print(f"\n{'═' * 60}")
            print(f"  GROUP {group}")
            print(f"{'═' * 60}\n")

            print(f"  {'#':<3} {'Team':<25} {'Pts':<4} {'W':<4} {'D':<4} {'L':<4} {'GF':<4} {'GA':<4} {'GD':<4} {'Corners':<4} {'YC':<4} {'RC':<4}")
            print(f"{'-' * 60}")

            for i, t in enumerate(ranking):
                s = stats[t]

                print(f"{i+1:<3} {t:<25} {s['pts']:>4} {s['w']:>4} "
                      f"{s['d']:>4} {s['l']:>4} {s['gf']:>4} {s['ga']:>4} "
                      f"{s['gd']:>4} {s['corners']:>7} {s['yc']:>4} "
                      f"{s['rc']:>4}")

            print(f"\nMatch Results - Group {group}:")
            for r in results:
                if r["group"] == group:
                    print(
                        f"  {r['home_team']:<15} {r['predicted_home_goals']} - {r['predicted_away_goals']} {r['away_team']}")

    return {
        "group_stats": group_stats,
        "group_results": results
    }


# =========================
# GET ROUND OF 32 FUNCTION
# =========================
def get_round_of_32(group_stats, verbose=False):
    """
    Top 2 from each group (24) + 8 best 3rd-placed teams = 32.
    Tiebreakers for 3rd place: Pts → GD → GF.
    """

    # =========================
    # PREP DATA
    # =========================
    qualifiers = []
    third_pool = []

    # =========================
    # PROCESS EACH GROUP
    # =========================
    for group, teams_stats in group_stats.items():

        # FINAL RANKING
        ranking = sorted(
            teams_stats.keys(),
            key=lambda x: (
                teams_stats[x]["pts"],
                teams_stats[x]["gd"],
                teams_stats[x]["gf"],
                -teams_stats[x]["yc"],  # - to sort in descending order
                -teams_stats[x]["rc"]
            ),
            reverse=True
        )

        # =========================
        # TOP 2 QUALIFY
        # =========================
        # top 1
        qualifiers.append(
            {
                "team": ranking[0],
                "group": group,
                "pos":  1
            }
        )

        # top 2
        qualifiers.append(
            {
                "team": ranking[1],
                "group": group,
                "pos":  2
            }
        )

        # =========================
        # 3RD PLACED TEAMS
        # =========================
        if len(ranking) >= 3:
            t = ranking[2]
            s = teams_stats[t]

            third_pool.append({
                "team": t,
                "group": group,
                "pts": s["pts"],
                "gd": s["gd"],
                "gf": s["gf"],
                "yc": s["yc"],
                "rc": s["rc"],
                "pos": 3
            })

    # =========================
    # SORT 3RD POOL
    # =========================
    third_pool.sort(
        key=lambda x: (
            x["pts"],
            x["gd"],
            x["gf"],
            -x["yc"],
            -x["rc"]
        ),
        reverse=True
    )

    # =========================
    # GET BEST 8 3RD PLACED TEAMS
    # =========================
    best_third = third_pool[:8]
    r32 = qualifiers + [
        {
            "team": t["team"],
            "group": t["group"],
            "pos": t["pos"]
        }
        for t in best_third
    ]

    if verbose:
        eliminated = third_pool[8:]
        print(f"\n{'═' * 60}")
        print(f"  ROUND OF 32 - QUALIFICATION SUMMARY")
        print(f"{'═' * 60}\n")
        print(f"\n  🟢 Best 3rd-Place Teams (advance to R32):")
        for i, t in enumerate(best_third):
            print(
                f"  {i+1:<2}. {t['team']:<16} {t['group']} {t['pts']:>3} {t['gd']:>3} {t['gf']:>3} {t['yc']:>3} {t['rc']:>3}")
        print(f"\n  🔴 Eliminated Teams (remain in 3rd Pool):")
        for i, t in enumerate(eliminated):
            print(
                f"  {i+1:<2}. {t['team']:<16} {t['group']} {t['pts']:>3} {t['gd']:>3} {t['gf']:>3} {t['yc']:>3} {t['rc']:>3}")
        print(f"\n{'═' * 60}")
        print(f"\n  📊 Total Qualifiers: {len(qualifiers)}")

    return {
        "round_name": "Round of 32",
        "qualifiers": qualifiers,
        "third_pool": third_pool,
        "r32": r32
    }


# =========================
# KNOCKOUT SIMULATE FUNCTION
# =========================
def knockout_simulate(round_name, knockout_df, cache, simulate_match_fn, verbose=False):
    """
    Simulate a knockout round (Round of 32, 16, QF, SF, Final).
    """
    if verbose:
        print(f"\n{'═' * 60}")
        print(f"  {round_name}")
        print(f"{'═' * 60}\n")
        print(f"  {'#':<4} {'Home':<16} {'':>2}{'Score':>7}{'':>2} "
              f"{'Away':<16}  {'Winner'}")
        print(f"  {'─' * 60}")

    knockout_df = knockout_df.copy()

    # =====================================================
    # FILTER MATCHES
    # =====================================================
    matches = knockout_df.copy()

    results = []

    rows = list(zip(
        matches["match_id"],
        matches["predicted_home_team"],
        matches["predicted_away_team"]
    ))

    # =========================
    # SIMULATE EACH MATCH
    # =========================
    for match_id, home_team, away_team in rows:

        result = simulate_match_fn(
            match_id,
            cache,
            knockout=True,
            et_total=0.8
        )

        home_goals = result["home_goals"]
        away_goals = result["away_goals"]
        home_yellow = result["home_yellow"]
        away_yellow = result["away_yellow"]
        home_red = result["home_red"]
        away_red = result["away_red"]
        home_corners = result["home_corners"]
        away_corners = result["away_corners"]
        is_penalty = result["penalty"]
        result_str = result["result_str"]

        match_winner = None
        match_loser = None
        winning_team = ""
        if result_str == "W":
            match_winner = home_team
            match_loser = away_team
            winning_team = "home"
        elif result_str == "L":
            match_winner = away_team
            match_loser = home_team
            winning_team = "away"

        results.append({
            "match_id": match_id,
            "round": round_name,
            "predicted_home_team": home_team,
            "predicted_away_team": away_team,
            "predicted_home_goals": home_goals,
            "predicted_away_goals": away_goals,
            "yellow_cards": home_yellow + away_yellow,
            "red_cards": home_red + away_red,
            "corners": home_corners + away_corners,
            "penalties": is_penalty,  # True or False
            # Team name will be stored (e.g: Brazil)
            "match_winner": match_winner,
            # Team name will be stored (e.g: Brazil)
            "match_loser": match_loser,
            "winning_team": winning_team  # home or away
        })

        if verbose:
            print(
                f"  {match_id:<4} "
                f"{home_team:<16} {home_goals}-{away_goals:<5} "
                f"{away_team:<16} => {match_winner}"
            )

    return {
        "round_name": round_name,
        "knockout_results": results,
    }
