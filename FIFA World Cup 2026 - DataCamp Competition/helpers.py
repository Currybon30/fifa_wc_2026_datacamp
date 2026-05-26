from collections import defaultdict, Counter
from feature_engineering import resolve_team_updated_to_original
import numbers
import pandas as pd

# =========================
# STEP 1: flatten iterations
# =========================
def flatten_by_match_id(stage_sims):
    """
    Input:
        {iteration: [match_dicts]}

    Output:
        {match_id: [all simulations]}
    """
    grouped = defaultdict(list)

    for _, matches in stage_sims.items():
        for match in matches:
            grouped[match["match_id"]].append(match)

    return dict(grouped)


# =========================
# STEP 2: merge stages
# =========================
def merge_stages(group_flat, knockout_flat):
    merged = defaultdict(list)

    for k, v in group_flat.items():
        merged[k].extend(v)

    for k, v in knockout_flat.items():
        merged[k].extend(v)

    return dict(merged)


# =========================
# STEP 3: Monte Carlo aggregate
# =========================
def monte_carlo_aggregate(data):

    def mode(values):
        return Counter(values).most_common(1)[0][0]

    result = {}

    for match_id, sims in data.items():

        sums = defaultdict(float)
        counts = defaultdict(int)
        categorical = defaultdict(list)
        binary = defaultdict(list)

        for sim in sims:
            for k, v in sim.items():

                if k == "match_id":
                    continue

                # penalties (binary)
                if k == "penalties":
                    binary[k].append(v)
                    continue

                # numeric → mean
                if isinstance(v, numbers.Number) or isinstance(v, int):
                    sums[k] += v
                    counts[k] += 1

                # categorical → mode
                else:
                    categorical[k].append(v)

        row = {}

        # numeric averages
        for k in sums:
            row[k] = int(round(sums[k] / counts[k]))

        # categorical modes
        for k, vals in categorical.items():
            row[k] = mode(vals)

        # binary (penalties) → majority vote
        for k, vals in binary.items():
            row[k] = mode(vals)

        result[match_id] = row

    return result


# =========================
# FULL PIPELINE
# =========================
def run_mc_pipeline(group_stage_sims, knockout_stage_sims):

    group_flat = flatten_by_match_id(group_stage_sims)
    knockout_flat = flatten_by_match_id(knockout_stage_sims)

    merged = merge_stages(group_flat, knockout_flat)

    return monte_carlo_aggregate(merged)

# =========================
# FILL PREDICTIONS DF
# =========================

def fill_predictions_df(group_df, knockout_df, predictions, match_id_col="match_id"):
    """
    Fill group and knockout prediction DataFrames from Monte Carlo results.

    Rules:
    - group stage uses: winning_team
    - knockout stage uses: match_winner = winning_team
    """

    group_df = group_df.copy()
    knockout_df = knockout_df.copy()

    # =========================
    # ENSURE COLUMNS EXIST
    # =========================

    group_cols = [
        "predicted_home_goals",
        "predicted_away_goals",
        "corners",
        "yellow_cards",
        "red_cards",
        "winning_team",
    ]

    knockout_cols = [
        "predicted_home_team",
        "predicted_away_team",
        "predicted_home_goals",
        "predicted_away_goals",
        "corners",
        "yellow_cards",
        "red_cards",
        "match_winner",
        "penalties",
    ]

    for col in group_cols:
        if col not in group_df.columns:
            group_df[col] = None

    for col in knockout_cols:
        if col not in knockout_df.columns:
            knockout_df[col] = None

    # =========================
    # FILL VALUES
    # =========================
    for match_id, pred in predictions.items():

        g_mask = group_df[match_id_col] == match_id
        k_mask = knockout_df[match_id_col] == match_id

        # =========================
        # GROUP STAGE FILL
        # =========================
        for k, v in pred.items():
            if k in group_df.columns:
                group_df.loc[g_mask, k] = v

        # =========================
        # KNOCKOUT STAGE FILL
        # =========================
        for k, v in pred.items():

            if k in knockout_df.columns:

                if k == "winning_team":
                    knockout_df.loc[k_mask, "match_winner"] = v 
                else:
                    knockout_df.loc[k_mask, k] = v

        # enforce rule explicitly (safe override)
        if "winning_team" in pred:
            knockout_df.loc[k_mask, "match_winner"] = pred["winning_team"]


        # =========================
        # RESOLVE TEAM NAMES - REVERSE MAPPING
        # =========================
        
        # Group Fixtures
        group_df = group_df.copy()
        group_df["home_team"] = group_df["home_team"].apply(resolve_team_updated_to_original)
        group_df["away_team"] = group_df["away_team"].apply(resolve_team_updated_to_original)

        # Knockout Slots
        knockout_df = knockout_df.copy()
        knockout_df["predicted_home_team"] = knockout_df["predicted_home_team"].apply(resolve_team_updated_to_original)
        knockout_df["predicted_away_team"] = knockout_df["predicted_away_team"].apply(resolve_team_updated_to_original)


    return group_df, knockout_df


# =========================
# KNOCKOUT MAP FUNCTION
# =========================
def knockout_map(previous_round_results):
    """
    This is used to map knockout brackets from Q16 -> final
    """
    winner_map = {}
    loser_map = {}

    for match in previous_round_results["knockout_results"]:

        match_id = match["match_id"]

        winner = match["match_winner"]

        # ---------------------------------------------
        # Determine loser
        # ---------------------------------------------
        loser = (
            match["predicted_away_team"] if winner == match["predicted_home_team"]
            else match["predicted_home_team"]
        )

        winner_map[match_id] = winner
        loser_map[match_id] = loser

    return winner_map, loser_map


# =========================
# FILL KNOCKOUT TABLE FUNCTION
# =========================
def fill_knockout_table(knockout_df, round_name, qualifiers, previous_round_results=None):
    """
    Populate knockout slots with actual teams.

    Parameters
    -------------------------------
    knockout_df : DataFrame
        Full knockout bracket dataframe.

    round_name : str
        Current round name.

    qualifiers : list[dict]
        Qualifiers of group stage

    previous_round_results : dict
        Results dict from previous knockout round.
        Must contain in "results" key:
            - match_id
            - match_winner
            - predicted_home_team
            - predicted_away_team
    """

    # =====================================================
    # FILTER ROUND
    # =====================================================
    df_round = knockout_df[
            knockout_df["round"] == round_name
        ].copy()

    # =====================================================
    # ROUND OF 32
    # =====================================================

    if round_name == "Round of 32":
        # =========================
        # BUILD LOOKUPS
        # =========================
        group_winners = {}
        group_runners = {}
        group_thirds = []

        for qualifier in qualifiers:
            if qualifier["pos"] == 1:
                group_winners[qualifier["group"]] = qualifier["team"]
            elif qualifier["pos"] == 2:
                group_runners[qualifier["group"]] = qualifier["team"]
            elif qualifier["pos"] == 3:
                group_thirds.append(qualifier["team"])

        third_index = 0

        # =========================
        # SLOT RESOLVER
        # =========================
        def resolve(slot):
            nonlocal third_index

            # Winner Group X
            if "Winner Group" in slot:
                group = slot.split()[-1]
                return group_winners.get(group)

            # Runner-up Group X
            if "Runner-up Group" in slot:
                group = slot.split()[-1]
                return group_runners.get(group)

            # Best 3rd
            if "Best 3rd" in slot:
                if third_index >= len(group_thirds):
                    return None
                team = group_thirds[third_index]
                third_index += 1
                return team

            return None  # strict fallback (prevents silent bad data)

    # =====================================================
    # ALL OTHER ROUNDS (R16, R8, R4, Final, Third place)
    # =====================================================
    else:
        winner_map, loser_map = knockout_map(previous_round_results)
        
        def resolve(slot):
            
            if slot is None:
                return None

            if not isinstance(slot, str):
                return slot

            # ---------------------------------------------
            # Winner Match X
            # ---------------------------------------------
            if "Winner Match" in slot:

                match_id = int(slot.split()[-1])

                return winner_map.get(match_id)

            # ---------------------------------------------
            # Loser Match X
            # ---------------------------------------------
            if "Loser Match" in slot:

                match_id = int(slot.split()[-1])

                return loser_map.get(match_id)
        
            return slot

    # =====================================================
    # FILL TEAMS
    # =====================================================
    knockout_df = knockout_df.copy()

    df_round["predicted_home_team"] = df_round["slot_home"].apply(resolve)
    df_round["predicted_away_team"] = df_round["slot_away"].apply(resolve) 
    
    # =====================================================
    # WRITE BACK TO FULL DF (CRITICAL)
    # =====================================================
    knockout_df.loc[df_round.index, "predicted_home_team"] = df_round["predicted_home_team"].values
    knockout_df.loc[df_round.index, "predicted_away_team"] = df_round["predicted_away_team"].values
        
    return knockout_df



# =========================
# LAMBDA CACHE - GROUP STAGE
# =========================
def build_lambda_cache_group_stage(stage_table_df, models, elo_ratings, team_hist, feature_engine):
    cache = {}

    stage_table_df = stage_table_df.copy()
    stage_table_df["date"] = pd.to_datetime(stage_table_df["date_utc"], utc=True)

    goal_cols = [
        "home_elo", "away_elo", "elo_diff", "home_advantage",
        "home_attack_rate", "home_defense_rate",
        "away_attack_rate", "away_defense_rate"
    ]

    card_cols = goal_cols + ["home_disc", "away_disc", "disc_diff", "disc_sum"]

    for row in stage_table_df.itertuples(index=False):

        # -------------------------
        # build 1-row input WITHOUT pandas dict overhead
        # -------------------------
        match_row = {
            "home_team": row.home_team,
            "away_team": row.away_team,
            "date": row.date,
            "venue": row.venue
        }

        match_row = pd.DataFrame([match_row])

        # -------------------------
        # FEATURE ENGINEERING (same logic)
        # -------------------------
        match_row = feature_engine["combine_elo"](match_row, elo_ratings)

        match_row["home_advantage"] = int(
            feature_engine["home_adv"](match_row["home_team"], match_row["venue"])
        )

        match_row = feature_engine["match_features"](match_row, team_hist)

        # -------------------------
        # model input
        # -------------------------
        X_goals = match_row[goal_cols].to_numpy()
        X_cards = match_row[card_cols].to_numpy()

        match_id = row.match_id

        # -------------------------
        # cache store
        # -------------------------
        cache[match_id] = {
            "home_team": row.home_team,
            "away_team": row.away_team,

            "lam_home_goal": float(models["goal_home"].predict(X_goals)[0]),
            "lam_away_goal": float(models["goal_away"].predict(X_goals)[0]),

            "lam_home_yellow": float(models["yellow_home"].predict(X_cards)[0]),
            "lam_away_yellow": float(models["yellow_away"].predict(X_cards)[0]),

            "lam_home_red": float(models["red_home"].predict(X_cards)[0]),
            "lam_away_red": float(models["red_away"].predict(X_cards)[0]),

            "lam_home_corner": float(models["corner_home"].predict(X_goals)[0]),
            "lam_away_corner": float(models["corner_away"].predict(X_goals)[0]),
        }

    return cache


# =========================
# LAMBDA CACHE - KNOCKOUT
# =========================
def build_lambda_cache_knockout(
    knockout_df,
    models,
    elo_ratings,
    team_hist,
    feature_engine
):
    cache = {}

    # =========================
    # PREP DATA
    # =========================
    df = knockout_df.copy()
    df["date"] = pd.to_datetime(df["date_utc"], utc=True)

    goal_cols = [
        "home_elo", "away_elo", "elo_diff", "home_advantage",
        "home_attack_rate", "home_defense_rate",
        "away_attack_rate", "away_defense_rate"
    ]

    card_cols = goal_cols + [
        "home_disc", "away_disc", "disc_diff", "disc_sum"
    ]

    goal_model_home = models["goal_home"]
    goal_model_away = models["goal_away"]
    yellow_home = models["yellow_home"]
    yellow_away = models["yellow_away"]
    red_home = models["red_home"]
    red_away = models["red_away"]
    corner_home = models["corner_home"]
    corner_away = models["corner_away"]

    # =========================
    # FAST LOOP
    # =========================
    for row in df.itertuples(index=False):

        match_id = row.match_id
        home = row.predicted_home_team
        away = row.predicted_away_team
        date = row.date
        venue = row.venue

        # =========================
        # BUILD MATCH FRAME (minimal overhead)
        # =========================
        match_row = pd.DataFrame({
            "home_team": [home],
            "away_team": [away],
            "date": [date],
            "venue": [venue],
        })

        # =========================
        # FEATURE ENGINEERING (still unavoidable unless fully refactored)
        # =========================
        match_row = feature_engine["combine_elo"](match_row, elo_ratings)

        match_row["home_advantage"] = int(
            feature_engine["home_adv"](match_row["home_team"], match_row["venue"])
        )

        match_row = feature_engine["match_features"](match_row, team_hist)

        # =========================
        # NUMPY EXTRACTION (faster than pandas .values)
        # =========================
        X_goals = match_row[goal_cols].to_numpy()
        X_cards = match_row[card_cols].to_numpy()

        # =========================
        # PREDICT LAMBDAS (faster local binding)
        # =========================
        cache[match_id] = {
            "home_team": home,
            "away_team": away,

            "lam_home_goal": float(goal_model_home.predict(X_goals)[0]),
            "lam_away_goal": float(goal_model_away.predict(X_goals)[0]),

            "lam_home_yellow": float(yellow_home.predict(X_cards)[0]),
            "lam_away_yellow": float(yellow_away.predict(X_cards)[0]),

            "lam_home_red": float(red_home.predict(X_cards)[0]),
            "lam_away_red": float(red_away.predict(X_cards)[0]),

            "lam_home_corner": float(corner_home.predict(X_goals)[0]),
            "lam_away_corner": float(corner_away.predict(X_goals)[0]),
        }

    return cache