from collections import defaultdict
import pandas as pd
import numpy as np

# ===============================
# RESOLVE TEAM NAME ORIGINAL GROUP FIXTURES TO UPDATED NAME
# ===============================
def resolve_team_original_to_updated(name):
    ORIGINAL_TO_UPDATED_NAME = {
        "UEFA Playoff A": "Bosnia and Herzegovina",
        "UEFA Playoff B": "Sweden",
        "UEFA Playoff C": "Turkey",
        "UEFA Playoff D": "Czechia",
        "FIFA Playoff 1": "DR Congo",
        "FIFA Playoff 2": "Iraq"
    }
    return ORIGINAL_TO_UPDATED_NAME.get(name, name)


# ===============================
# RESOLVE TEAM NAME UPDATED GROUP FIXTURES TO ORIGINAL NAME
# ===============================
def resolve_team_updated_to_original(name):
    UPDATED_TO_ORIGINAL_NAME = {
        "Bosnia and Herzegovina": "UEFA Playoff A",
        "Sweden": "UEFA Playoff B",
        "Turkey": "UEFA Playoff C",
        "Czechia": "UEFA Playoff D",
        "DR Congo": "FIFA Playoff 1",
        "Iraq": "FIFA Playoff 2",
        "United States": "USA" # This is a special case, USA is the official name of the country, but the team is called "United States" in the dataset
    }
    return UPDATED_TO_ORIGINAL_NAME.get(name, name)


# ===============================
# COMBINE TEAMS ELO TO MATCH CSV
# ===============================
def combine_teams_elo(match_csv, elo_csv):
    elo_lookup = (
        elo_csv.rename(columns={"Team": "team", "Elo": "elo"})
        .drop_duplicates(subset="team", keep="first")
    )
    match = match_csv.copy()
    match = match.merge(
        elo_lookup.rename(columns={"team": "home_team", "elo": "home_elo"}),
        on="home_team",
        how="left",
    )
    match = match.merge(
        elo_lookup.rename(columns={"team": "away_team", "elo": "away_elo"}),
        on="away_team",
        how="left",
    )

    match["elo_diff"] = match["home_elo"] - match["away_elo"]
    return match


# ===============================
# TOURNAMENT WEIGHT
# ===============================
def tournament_weight(tournament):
    
    if pd.isna(tournament):
        return 1.0

    t = str(tournament).lower()

    if "world cup" in t:
        return 1.3
    else:
        return 1.0


# ===============================
# TEAM DISCIPLINE
# ===============================
def team_disc(team):
    TEAM_DISCIPLINE = {
        "Argentina": 2.4,
        "Saudi Arabia": 4.7,
        "Serbia": 4.0,
        "Netherlands": 2.8,
        "Switzerland": 2.3,
        "Ghana": 2.7,
        "Morocco": 1.6,
        "France": 1.1,
        "Croatia": 1.1,
        "Uruguay": 2.7,
        "Canada": 2.7,
        "Qatar": 2.3,
        "Cameroon": 3.3,
        "Senegal": 1.8,
        "Australia": 1.8,
        "Poland": 1.8,
        "Iran": 2.3,
        "Mexico": 2.3,
        "Japan": 1.5,
        "Portugal": 1.2,
        "South Korea": 1.5,
        "Costa Rica": 2.0,
        "Brazil": 1.2,
        "United States": 1.3,
        "Tunisia": 1.7,
        "Wales": 2.7,
        "Denmark": 1.7,
        "Belgium": 1.7,
        "Germany": 1.0,
        "Ecuador": 1.0,
        "Spain": 0.5,
        "England": 0.2
    }

    DEFAULT_DISC = np.mean(list(TEAM_DISCIPLINE.values()))
    return TEAM_DISCIPLINE.get(team, DEFAULT_DISC)


# ===============================
# GET TEAM RATES
# ===============================
def get_team_rates(team_hist, team, current_date, window=10, default=1.0):
    history = team_hist.get(team, [])
    
    # filter only relevant history games where date is before current date
    history = [h for h in history if h.date < current_date]

    if len(history) == 0:
        return default, default

    history = history[-window:]

    scored, conceded = [], []

    for h in history:
        if h.home_team == team:
            scored.append(h.home_score)
            conceded.append(h.away_score)
        else:
            scored.append(h.away_score)
            conceded.append(h.home_score)

    
    weights = np.array([tournament_weight(h.tournament) for h in history])

    n = len(history)

    # =========================
    # CASE 1: 1–5 games
    # =========================
    if n <= 5:

        gs = np.sum(np.array(scored) * weights) / np.sum(weights)
        gc = np.sum(np.array(conceded) * weights) / np.sum(weights)

        alpha = n / 5

        return (
            alpha * gs + (1 - alpha) * default,
            alpha * gc + (1 - alpha) * default
        )

    # =========================
    # CASE 2: 6–10 games
    # =========================
    last5 = history[-5:]
    prev5 = history[-10:-5]
    

    def calc(chunk):
        if len(chunk) == 0:
            return default, default

        s, c, w = [], [], []

        for h in chunk:
            if h.home_team == team:
                sh = h.home_score
                ch = h.away_score
                
            else:
                sh = h.away_score
                ch = h.home_score

            # 🔥 critical fix
            if not np.isfinite(sh) or not np.isfinite(ch):
                continue

            s.append(sh)
            c.append(ch)
            w.append(tournament_weight(h.tournament))

        s = np.array(s)
        c = np.array(c)
        w = np.array(w)

        return np.sum(s * w) / np.sum(w), np.sum(c * w) / np.sum(w)

    A5, D5 = calc(last5)
    A10, D10 = calc(prev5)

    attack = 0.7 * A5 + 0.3 * A10
    defense = 0.7 * D5 + 0.3 * D10

    return attack, defense


# ===============================
# TEAM ATTACK
# ===============================
def team_attack(team_hist, team, current_date):
    attack_rate, _ = get_team_rates(team_hist, team, current_date)
    return attack_rate


# ===============================
# TEAM DEFENSE
# ===============================
def team_def(team_hist, team, current_date):
    _, def_rate = get_team_rates(team_hist, team, current_date)
    return def_rate   


# =========================
# YELLOW CARDS
# =========================
def pseudo_yellow(team_hist, row, row_index):

    # =========================
    # GLOBAL BASE (IMPORTANT)
    # =========================
    BASE_TOTAL = 3.5

    # split baseline (home advantage)
    home_base = BASE_TOTAL * 0.52
    away_base = BASE_TOTAL * 0.48

    h_disc = team_disc(row.home_team)
    a_disc = team_disc(row.away_team)

    h_attack = team_attack(team_hist, row.home_team, row.date)
    a_attack = team_attack(team_hist, row.away_team, row.date)

    # intensity per team (NOT shared)
    home_effect = 0.25 * (h_attack + a_disc - 1)
    away_effect = 0.25 * (a_attack + h_disc - 1)

    home_base += home_effect + 0.35 * h_disc
    away_base += away_effect + 0.35 * a_disc

    # tournament effects - world cup

    home_base *= 1.15
    away_base *= 1.15

    rng = np.random.default_rng(hash(row_index) % 2**32)

    home_yellow = rng.poisson(np.clip(home_base, 0.5, 7))
    away_yellow = rng.poisson(np.clip(away_base, 0.5, 7))

    return home_yellow, away_yellow


# =========================
# RED CARDS
# =========================
def pseudo_red(team_hist, row, row_index):

    h_disc = team_disc(row.home_team)
    a_disc = team_disc(row.away_team)

    h_attack = team_attack(team_hist, row.home_team, row.date)
    a_attack = team_attack(team_hist, row.away_team, row.date)

    # asymmetry affects BOTH teams differently
    home_intensity = abs(h_attack - a_attack)
    away_intensity = abs(a_attack - h_attack)

    # discipline risk
    home_risk = h_disc + a_disc
    away_risk = a_disc + h_disc

    # probabilities per team
    p_home = 0.01 + 0.008 * home_intensity + 0.012 * home_risk
    p_away = 0.01 + 0.008 * away_intensity + 0.012 * away_risk

    # tournament effect
    p_home += 0.008
    p_away += 0.008

    # clamp
    p_home = np.clip(p_home, 0.005, 0.25)
    p_away = np.clip(p_away, 0.005, 0.25)

    rng = np.random.default_rng(hash(row_index) % 2**32)

    home_red = int(rng.random() < p_home)
    away_red = int(rng.random() < p_away)

    return home_red, away_red


# =========================
# CORNERS
# =========================
def pseudo_corners(team_hist, row, row_index):

    h_attack = team_attack(team_hist, row.home_team, row.date)
    a_attack = team_attack(team_hist, row.away_team, row.date)

    h_def = team_def(team_hist, row.home_team, row.date)
    a_def = team_def(team_hist, row.away_team, row.date)

    # pressure model (attack vs opponent defense)
    home_pressure = h_attack + (1.0 - a_def)
    away_pressure = a_attack + (1.0 - h_def)

    pressure_diff = home_pressure - away_pressure
    
    # =========================
    # WORLD CUP BASELINE
    # =========================
    BASE_TOTAL_CORNERS = 9.7

    # split baseline with small home advantage
    base_home = BASE_TOTAL_CORNERS * 0.52
    base_away = BASE_TOTAL_CORNERS * 0.48

    # =========================
    # APPLY TEAM EFFECT (soft scaling)
    # =========================
    base_home += 0.9 * pressure_diff
    base_away -= 0.9 * pressure_diff

    # =========================
    # ADD MATCH VARIANCE
    # =========================
    rng = np.random.default_rng(hash(row_index) % 2**32)

    # clamp realistic ranges
    base_home = np.clip(base_home, 1.0, 12)
    base_away = np.clip(base_away, 1.0, 12)

    home_corners = rng.poisson(base_home)
    away_corners = rng.poisson(base_away)

    return home_corners, away_corners


# ===============================
# ADD MATCH FEATURES
# ===============================
def add_match_features(mydf, team_hist, window=10):
    mydf = mydf.copy()

    home_attack, home_defense = [], []
    away_attack, away_defense = [], []

    home_disc, away_disc = [], []

    yellow_home, yellow_away = [], []
    red_home, red_away = [], []

    home_corners_list, away_corners_list = [], []

    for i, row in enumerate(mydf.itertuples(index=False)):

        date = row.date

        h_team = row.home_team
        a_team = row.away_team

        # =========================
        # ATTACK / DEFENSE
        # =========================
        ha, hd = get_team_rates(team_hist, h_team, date, window)
        aa, ad = get_team_rates(team_hist, a_team, date, window)

        home_attack.append(ha)
        home_defense.append(hd)
        away_attack.append(aa)
        away_defense.append(ad)

        # =========================
        # DISCIPLINE
        # =========================
        h_d = team_disc(h_team)
        a_d = team_disc(a_team)

        home_disc.append(h_d)
        away_disc.append(a_d)

        # =========================
        # YELLOW CARDS
        # =========================
        y_home, y_away = pseudo_yellow(team_hist, row, i)

        yellow_home.append(y_home)
        yellow_away.append(y_away)

        # =========================
        # RED CARDS
        # =========================
        r_home, r_away = pseudo_red(team_hist, row, i)

        red_home.append(r_home)
        red_away.append(r_away)

        # =========================
        # CORNERS
        # =========================
        hc, ac = pseudo_corners(team_hist, row, i)

        home_corners_list.append(hc)
        away_corners_list.append(ac)

    # =========================
    # ASSIGN TO DF
    # =========================
    mydf["home_attack_rate"] = home_attack
    mydf["home_defense_rate"] = home_defense
    mydf["away_attack_rate"] = away_attack
    mydf["away_defense_rate"] = away_defense

    mydf["home_disc"] = home_disc
    mydf["away_disc"] = away_disc
    mydf["disc_diff"] = mydf["home_disc"] - mydf["away_disc"]
    mydf["disc_sum"] = mydf["home_disc"] + mydf["away_disc"]

    mydf["home_yellow"] = yellow_home
    mydf["away_yellow"] = yellow_away

    mydf["home_red"] = red_home
    mydf["away_red"] = red_away

    mydf["home_corners"] = home_corners_list
    mydf["away_corners"] = away_corners_list

    return mydf


# ===============================
# IS HOME ADVANTAGE
# ===============================
def is_home_advantage(home_team, venue):
    HOST_PLACES = {
        "USA": [
            "Atlanta",
            "Boston",
            "Dallas",
            "Houston",
            "Kansas City",
            "Los Angeles",
            "Miami",
            "New York",
            "Philadelphia",
            "Seattle",
            "San Francisco"
        ],
        "Canada": [
            "Toronto",
            "Vancouver"
        ],
        "Mexico": [
            "Mexico City",
            "Guadalajara",
            "Monterrey"
        ]
    }
    host_cities = HOST_PLACES.get(home_team[0], [])
    if not host_cities:  # not USA / Canada / Mexico
        return False
    return any(city in str(venue) for city in host_cities)

# ===============================
# TEAM HIST
# ===============================
def get_team_hist(rawdf):
    team_hist = defaultdict(list)
    for r in rawdf.itertuples(index=False):
        team_hist[r.home_team].append(r)
        team_hist[r.away_team].append(r)
    return team_hist