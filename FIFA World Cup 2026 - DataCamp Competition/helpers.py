import numbers
from collections import Counter, defaultdict

import pandas as pd
from feature_engineering import resolve_team_updated_to_original
from simulations import get_round_of_32


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

        # =========================
        # NUMERICAL STATS
        # =========================
        sums = defaultdict(float)
        counts = defaultdict(int)

        # =========================
        # CATEGORICAL STATS
        # =========================
        categorical = defaultdict(list)

        # =========================
        # GROUP STAGE OUTCOME STORAGE
        # =========================
        group_home_goals = []
        group_away_goals = []

        # =========================
        # KNOCKOUT OUTCOME STORAGE (JOINT!)
        # =========================
        knockout_outcomes = []

        for sim in sims:

            # -------------------------
            # NUMERIC + CATEGORICAL
            # -------------------------
            for k, v in sim.items():

                if k in ["match_id"]:
                    continue

                # skip outcome fields (handled separately)
                if k in [
                    "predicted_home_team",
                    "predicted_away_team",
                    "predicted_home_goals",
                    "predicted_away_goals",
                    "winning_team",
                    "penalties"
                ]:
                    continue

                if isinstance(v, numbers.Number):
                    sums[k] += v
                    counts[k] += 1
                else:
                    categorical[k].append(v)

            # -------------------------
            # GROUP STAGE
            # -------------------------
            if "predicted_home_goals" in sim and "predicted_away_goals" in sim:

                hg = sim["predicted_home_goals"]
                ag = sim["predicted_away_goals"]

                group_home_goals.append(hg)
                group_away_goals.append(ag)

            # -------------------------
            # KNOCKOUT (JOINT STATE)
            # -------------------------
            if all(k in sim for k in [
                "predicted_home_team",
                "predicted_away_team",
                "predicted_home_goals",
                "predicted_away_goals",
                "winning_team",
                "penalties"
            ]):

                knockout_outcomes.append((
                    sim["predicted_home_team"],
                    sim["predicted_away_team"],
                    sim["predicted_home_goals"],
                    sim["predicted_away_goals"],
                    sim["winning_team"],
                    sim["penalties"]
                ))

        # =========================
        # BUILD FINAL ROW
        # =========================
        row = {}

        # -------------------------
        # MEAN FOR NUMERIC STATS
        # -------------------------
        for k in sums:
            row[k] = int(round(sums[k] / counts[k]))

        # -------------------------
        # MODE FOR CATEGORICAL
        # -------------------------
        for k, vals in categorical.items():
            if vals:
                row[k] = mode(vals)

        # =========================
        # GROUP STAGE RESULT
        # =========================
        if group_home_goals and group_away_goals:

            h = mode(group_home_goals)
            a = mode(group_away_goals)

            row["predicted_home_goals"] = h
            row["predicted_away_goals"] = a

            if h > a:
                row["winning_team"] = "home"
            elif h < a:
                row["winning_team"] = "away"
            else:
                row["winning_team"] = "draw"

        # =========================
        # KNOCKOUT RESULT (JOINT MODE)
        # =========================
        if knockout_outcomes:

            best = Counter(knockout_outcomes).most_common(1)[0][0]

            row["predicted_home_team"] = best[0]
            row["predicted_away_team"] = best[1]
            row["predicted_home_goals"] = best[2]
            row["predicted_away_goals"] = best[3]
            row["winning_team"] = best[4]
            row["penalties"] = best[5]

        result[match_id] = row

    return result


# =========================
# RE-CHAIN KNOCKOUT BRACKET
# =========================
KNOCKOUT_ROUND_ORDER = [
    "Round of 32",
    "Round of 16",
    "Quarter-final",
    "Semi-final",
    "Third-place playoff",
    "Final",
]


def rechain_knockout_bracket(predictions, knockout_df):
    """
    Make the aggregated knockout bracket internally consistent.

    `monte_carlo_aggregate` picks the most common result for each match_id
    INDEPENDENTLY. That breaks the bracket chain: the team in a later slot
    (e.g. "Winner Match 73") is that match's own modal team, which need not
    equal the aggregated winner of match 73. This walks the bracket round by
    round and rewrites each match's teams from the previous rounds' aggregated
    winners / losers, exactly like a single deterministic run does.

    Round of 32 teams are left untouched (they come from the group-stage
    aggregation). The winning side ("home"/"away") and all match statistics
    from the aggregation are preserved; only the team identities are re-linked.

    Parameters
    -------------------------------
    predictions : dict[match_id, dict]
        Output of `monte_carlo_aggregate`.

    knockout_df : DataFrame
        Knockout slot definitions (needs: match_id, round, slot_home, slot_away).

    Returns
    -------------------------------
    dict[match_id, dict]
        The same predictions dict with consistent knockout team identities.
    """
    slots = {
        int(row.match_id): (row.round, row.slot_home, row.slot_away)
        for row in knockout_df.itertuples(index=False)
    }

    winner_map = {}
    loser_map = {}

    def resolve_slot(slot):
        if not isinstance(slot, str):
            return slot
        if "Winner Match" in slot:
            return winner_map.get(int(slot.split()[-1]))
        if "Loser Match" in slot:
            return loser_map.get(int(slot.split()[-1]))
        # Round of 32 slots already hold actual team names post-aggregation.
        return slot

    for round_name in KNOCKOUT_ROUND_ORDER:
        for match_id, (r, slot_home, slot_away) in slots.items():

            if r != round_name:
                continue

            pred = predictions.get(match_id)
            if pred is None:
                continue

            # Re-derive teams from previous rounds for every round after R32.
            if round_name != "Round of 32":
                pred["predicted_home_team"] = resolve_slot(slot_home)
                pred["predicted_away_team"] = resolve_slot(slot_away)

            home = pred.get("predicted_home_team")
            away = pred.get("predicted_away_team")

            # winning_team is the modal winning SIDE; map it onto the
            # (now consistent) team identities to propagate forward.
            if pred.get("winning_team") == "away":
                winner_map[match_id], loser_map[match_id] = away, home
            else:
                winner_map[match_id], loser_map[match_id] = home, away

    return predictions


# =========================
# FULL PIPELINE
# =========================
def run_mc_pipeline(group_stage_sims, knockout_stage_sims, knockout_df=None):

    group_flat = flatten_by_match_id(group_stage_sims)
    knockout_flat = flatten_by_match_id(knockout_stage_sims)

    merged = merge_stages(group_flat, knockout_flat)

    predictions = monte_carlo_aggregate(merged)

    # Re-link the knockout bracket so later-round teams match the aggregated
    # winners of the matches that feed them (independent per-match modes break
    # this chain). Requires the slot definitions; skipped if not provided.
    if knockout_df is not None:
        # R32 teams from per-match modes can repeat (same team in 2+ matches).
        # Rebuild from aggregated group-stage qualifiers + slot rules instead.
        qualifiers = aggregate_r32_qualifiers_from_mc(group_stage_sims)
        predictions = apply_round_of_32_teams(
            predictions, knockout_df, qualifiers)
        predictions = rechain_knockout_bracket(predictions, knockout_df)

    return predictions

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
    group_df["home_team"] = group_df["home_team"].apply(
        resolve_team_updated_to_original)
    group_df["away_team"] = group_df["away_team"].apply(
        resolve_team_updated_to_original)

    # Knockout Slots
    knockout_df["predicted_home_team"] = knockout_df["predicted_home_team"].apply(
        resolve_team_updated_to_original)
    knockout_df["predicted_away_team"] = knockout_df["predicted_away_team"].apply(
        resolve_team_updated_to_original)

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
# BEST 3rd-PLACE ASSIGNMENT
# =========================
def assign_third_place_slots(third_slots, available_groups):
    """
    Globally assign qualified 3rd-place groups to "Best 3rd" knockout slots.

    Each Round of 32 slot only accepts a 3rd-place team from a fixed set of
    groups (e.g. "Best 3rd (Groups A/B/C/D/F)"). A purely greedy, slot-by-slot
    assignment can dead-end: an early slot may grab the only group a later
    slot could have used. This solves it as a bipartite matching (Kuhn's
    augmenting-path algorithm) so assignments are reshuffled (backtracked)
    whenever that frees up a feasible team for another slot.

    Parameters
    -------------------------------
    third_slots : list[tuple[str, list[str]]]
        Ordered list of (slot_string, candidate_groups) pairs.

    available_groups : set[str]
        Groups that actually have a qualified 3rd-place team.

    Returns
    -------------------------------
    dict[str, str]
        Mapping of slot_string -> assigned group.
    """
    # group -> index of the slot it is currently matched to
    group_to_slot = {}

    def try_assign(slot_idx, visited):
        for group in third_slots[slot_idx][1]:
            if group not in available_groups or group in visited:
                continue
            visited.add(group)
            current = group_to_slot.get(group)
            if current is None or try_assign(current, visited):
                group_to_slot[group] = slot_idx
                return True
        return False

    for slot_idx in range(len(third_slots)):
        try_assign(slot_idx, set())

    return {
        third_slots[slot_idx][0]: group
        for group, slot_idx in group_to_slot.items()
    }


# =========================
# GROUP STAGE -> R32 QUALIFIERS (MONTE CARLO)
# =========================
def build_group_stats_from_results(group_results):
    """Rebuild group standings from a list of simulated group-stage matches."""
    group_stats = {}

    for match in group_results:
        g = match["group"]
        home = match["home_team"]
        away = match["away_team"]

        if g not in group_stats:
            group_stats[g] = {}

        for t in (home, away):
            if t not in group_stats[g]:
                group_stats[g][t] = {
                    "pts": 0, "gf": 0, "ga": 0, "gd": 0,
                    "w": 0, "d": 0, "l": 0,
                    "yc": 0, "rc": 0, "corners": 0,
                }

        s = group_stats[g]
        hg = match["predicted_home_goals"]
        ag = match["predicted_away_goals"]

        s[home]["gf"] += hg
        s[home]["ga"] += ag
        s[away]["gf"] += ag
        s[away]["ga"] += hg

        wt = match.get("winning_team", "")
        if wt == "home":
            s[home]["pts"] += 3
            s[home]["w"] += 1
            s[away]["l"] += 1
        elif wt == "away":
            s[away]["pts"] += 3
            s[away]["w"] += 1
            s[home]["l"] += 1
        else:
            s[home]["pts"] += 1
            s[away]["pts"] += 1
            s[home]["d"] += 1
            s[away]["d"] += 1

        s[home]["gd"] = s[home]["gf"] - s[home]["ga"]
        s[away]["gd"] = s[away]["gf"] - s[away]["ga"]

    return group_stats


def aggregate_r32_qualifiers_from_mc(group_stage_sims):
    """
    Build one R32 qualifier list from many MC group-stage iterations.

    Per iteration, standings are recomputed and get_round_of_32 is applied.
    Positions 1 and 2 use the modal (1st, 2nd) *pair* per group so the same
    team cannot be both winner and runner-up, and cross-group modes cannot
    create duplicate fixtures (e.g. Brazil vs Netherlands twice in R32).
    """
    pair_counts = Counter()       # (group, 1st_team, 2nd_team) -> count
    third_group_counts = Counter()
    third_team_counts = Counter()  # (group, team) -> count when advancing

    for matches in group_stage_sims.values():
        if not matches:
            continue
        group_stats = build_group_stats_from_results(matches)
        by_group = defaultdict(dict)
        for q in get_round_of_32(group_stats)["r32"]:
            by_group[q["group"]][q["pos"]] = q["team"]

        for group, pos_team in by_group.items():
            if 1 in pos_team and 2 in pos_team:
                pair_counts[(group, pos_team[1], pos_team[2])] += 1
            if 3 in pos_team:
                third_group_counts[group] += 1
                third_team_counts[(group, pos_team[3])] += 1

    qualifiers = []
    for group in sorted({g for g, _, _ in pair_counts}):
        pairs = [
            (first, second, cnt)
            for (g, first, second), cnt in pair_counts.items()
            if g == group
        ]
        if not pairs:
            continue
        first, second, _ = max(pairs, key=lambda x: x[2])
        qualifiers.append({"team": first, "group": group, "pos": 1})
        qualifiers.append({"team": second, "group": group, "pos": 2})

    for group, _ in third_group_counts.most_common(8):
        teams = [
            (team, cnt)
            for (g, team), cnt in third_team_counts.items()
            if g == group
        ]
        if teams:
            qualifiers.append({
                "team": max(teams, key=lambda x: x[1])[0],
                "group": group,
                "pos": 3,
            })

    return qualifiers


def make_r32_slot_resolver(df_round, qualifiers):
    """Return a resolve(slot) function for Round of 32 slot strings."""
    group_winners = {}
    group_runners = {}
    group_thirds = {}

    for qualifier in qualifiers:
        if qualifier["pos"] == 1:
            group_winners[qualifier["group"]] = qualifier["team"]
        elif qualifier["pos"] == 2:
            group_runners[qualifier["group"]] = qualifier["team"]
        elif qualifier["pos"] == 3:
            group_thirds[qualifier["group"]] = qualifier["team"]

    third_slots = []
    seen_slots = set()
    for slot in pd.concat([df_round["slot_home"], df_round["slot_away"]]):
        if isinstance(slot, str) and "Best 3rd" in slot and slot not in seen_slots:
            seen_slots.add(slot)
            inside = slot[slot.find("(") + 1: slot.find(")")]
            candidate_groups = [
                g.strip()
                for g in inside.replace("Groups", "").strip().split("/")
            ]
            third_slots.append((slot, candidate_groups))

    third_assignment = assign_third_place_slots(
        third_slots, set(group_thirds.keys()))

    def resolve(slot):
        if "Winner Group" in slot:
            return group_winners.get(slot.split()[-1])
        if "Runner-up Group" in slot:
            return group_runners.get(slot.split()[-1])
        if "Best 3rd" in slot:
            group = third_assignment.get(slot)
            if group is None:
                return None
            return group_thirds.get(group)
        return None

    return resolve


def apply_round_of_32_teams(predictions, knockout_df, qualifiers):
    """
    Overwrite R32 predicted teams using qualifiers + slot rules.

    Ensures each advancing team appears at most once in the Round of 32
    (unlike independent per-match Monte Carlo modes).
    """
    df_round = knockout_df[knockout_df["round"] == "Round of 32"]
    resolve = make_r32_slot_resolver(df_round, qualifiers)

    for row in df_round.itertuples(index=False):
        match_id = int(row.match_id)
        if match_id not in predictions:
            predictions[match_id] = {}
        predictions[match_id]["predicted_home_team"] = resolve(row.slot_home)
        predictions[match_id]["predicted_away_team"] = resolve(row.slot_away)

    return predictions


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
        # qualifiers is the r32 list (pos 1/2/3) from get_round_of_32
        if isinstance(qualifiers, dict):
            r32 = qualifiers.get("r32", qualifiers)
        else:
            r32 = qualifiers
        resolve = make_r32_slot_resolver(df_round, r32)

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
    knockout_df.loc[df_round.index,
                    "predicted_home_team"] = df_round["predicted_home_team"].values
    knockout_df.loc[df_round.index,
                    "predicted_away_team"] = df_round["predicted_away_team"].values

    return knockout_df


# =========================
# LAMBDA CACHE - GROUP STAGE
# =========================
def build_lambda_cache_group_stage(stage_table_df, models, elo_ratings, team_hist, feature_engine):
    cache = {}

    stage_table_df = stage_table_df.copy()
    stage_table_df["date"] = stage_table_df["date_utc"]

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
            feature_engine["home_adv"](
                match_row["home_team"], match_row["venue"])
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
    # df["date"] = pd.to_datetime(df["date_utc"], utc=True)

    df["date"] = df["date_utc"]

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
            feature_engine["home_adv"](
                match_row["home_team"], match_row["venue"])
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
