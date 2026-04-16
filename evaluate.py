def evaluate_full(schedule, teams, big_teams):
    R = len(schedule)

    team_home = {t: [] for t in teams}
    team_big = {t: [] for t in teams}

    # =========================
    # Build data per tim
    # =========================
    for r, matches in enumerate(schedule):
        for h, a in matches:
            team_home[h].append(1)
            team_home[a].append(0)

            team_big[h].append(1 if a in big_teams else 0)
            team_big[a].append(1 if h in big_teams else 0)

    # =========================
    # 1. BREAK
    # =========================
    total_breaks = 0
    breaks_per_team = {}

    for t in teams:
        b = 0
        for i in range(R - 1):
            if team_home[t][i] == team_home[t][i+1]:
                b += 1
        breaks_per_team[t] = b
        total_breaks += b

    # =========================
    # 2. BIG TEAM VIOLATION (window 4 ≥ 3)
    # =========================
    total_big_violations = 0
    big_per_team = {}

    for t in teams:
        v = 0
        arr = team_big[t]
        for i in range(R - 3):
            if sum(arr[i:i+4]) >= 3:
                v += 1
        big_per_team[t] = v
        total_big_violations += v

    # =========================
    # 3. HOME/AWAY IMBALANCE
    # =========================
    imbalance_total = 0
    imbalance_per_team = {}

    for t in teams:
        home_count = sum(team_home[t])
        away_count = R - home_count
        imbalance = abs(home_count - away_count)

        imbalance_per_team[t] = (home_count, away_count, imbalance)
        imbalance_total += imbalance

    return {
        "total_breaks": total_breaks,
        "total_big_violations": total_big_violations,
        "total_imbalance": imbalance_total,
        "breaks_per_team": breaks_per_team,
        "big_per_team": big_per_team,
        "imbalance_per_team": imbalance_per_team,
    }