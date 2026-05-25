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