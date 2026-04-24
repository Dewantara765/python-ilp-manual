from ortools.sat.python import cp_model
from second_half import generate_second_half_semi_deterministic
from evaluate import evaluate_full


teams = [
    "ARS","AVL","BOU","BRE","BHA",
    "CHE","CRY","EVE","FUL","IPS",
    "LEI","LIV","MCI","MUN","NEW",
    "NFO","SOU","TOT","WHU","WOL"
]#contoh liga inggris


big_matches = [ ("ARS","CHE"), ("ARS","LIV"), ("ARS","MCI"), ("ARS","MUN"), ("ARS","TOT"), 
                ("CHE","LIV"), ("CHE","MCI"), ("CHE","MUN"), ("CHE","TOT"), 
                ("LIV","MCI"), ("LIV","MUN"), ("LIV","TOT"), 
                ("MCI","MUN"), ("MCI","TOT"), 
                ("MUN","TOT") ]


derby_pairs = [("ARS","TOT"), ("CHE","FUL"), ("EVE","LIV"), ("MCI","MUN")]

N = len(teams)
R = N - 1  # 19 round

shift = 10

big_teams = ["ARS","CHE","LIV","MCI","MUN","TOT"]

team_idx = {t:i for i,t in enumerate(teams)}
big_idx = [team_idx[t] for t in big_teams]

# =========================
# Print helper
# =========================
def print_schedule(schedule, title):
    print(f"\n=== {title} ===")
    for r, matches in enumerate(schedule):
        print(f"Round {r+1}")
        for h, a in matches:
            print(f"{h} vs {a}")
        print()

model = cp_model.CpModel()

# =========================
# Variables
# =========================
x = {}
for i in range(N):
    for j in range(N):
        if i != j:
            for r in range(R):
                x[i,j,r] = model.NewBoolVar(f"x_{i}_{j}_{r}")

# Home indicator
h = {}
for i in range(N):
    for r in range(R):
        h[i,r] = model.NewBoolVar(f"h_{i}_{r}")

# =========================
# Link x -> h
# =========================
for i in range(N):
    for r in range(R):
        model.Add(
            h[i,r] == sum(x[i,j,r] for j in range(N) if j != i)
        )

# =========================
# Each pair plays once
# =========================
for i in range(N):
    for j in range(i+1, N):
        model.Add(
            sum(x[i,j,r] + x[j,i,r] for r in range(R)) == 1
        )

# =========================
# One match per round
# =========================
for i in range(N):
    for r in range(R):
        model.Add(
            sum(x[i,j,r] + x[j,i,r] for j in range(N) if j != i) == 1
        )

# =========================
# Derby constraint
# =========================
for t1, t2 in derby_pairs:
    i = team_idx[t1]
    j = team_idx[t2]
    for r in range(R):
        model.Add(h[i,r] + h[j,r] == 1)

# =========================
# Round 1-2 and 18-19 HA/AH
# =========================
for i in range(N):
    model.Add(h[i,0] != h[i,1])
    model.Add(h[i,17] != h[i,18])

# # mapping semi-mirror
# s0 = (0 + shift) % R

# for i in range(N):
#     # no H H H
#     model.Add(
#         h[i,17] + h[i,18] + (1 - h[i,s0]) <= 2
#     )

#     # no A A A
#     model.Add(
#         (1-h[i,17]) + (1-h[i,18]) + h[i,s0] <= 2
#     )

# =========================
# Ensure Round 37/38 HA/AH
# =========================
for i in range(N):
    s1 = (17 + shift) % R
    s2 = (18 + shift) % R

    model.Add(h[i, s1] != h[i, s2])

# =========================
# Home count (9 or 10)
# =========================
for i in range(N):
    total_home = sum(h[i,r] for r in range(R))
    model.Add(total_home >= 9)
    model.Add(total_home <= 10)

# =========================
# No 3 consecutive H/A
# =========================
for i in range(N):
    for r in range(R-2):
        model.Add(h[i,r] + h[i,r+1] + h[i,r+2] <= 2)
        model.Add((1-h[i,r]) + (1-h[i,r+1]) + (1-h[i,r+2]) <= 2)

# =========================
# No derby in Round 1
# =========================
for t1, t2 in derby_pairs:
    i = team_idx[t1]
    j = team_idx[t2]

    for r in [0, 9]:  # Round 1 & Round 3
        model.Add(x[i,j,r] == 0)
        model.Add(x[j,i,r] == 0)

for (t1, t2) in big_matches:
    i = team_idx[t1]
    j = team_idx[t2]

    model.Add(x[i,j,9] == 0)
    model.Add(x[j,i,9] == 0)

# =========================
# Break Only in Even to Odd Round
# =========================
for i in range(N):
    for r in range(18):   # transition r -> r+1

        if r % 2 == 0:
            model.Add(h[i,r] != h[i,r+1])
# =========================
# Break
# =========================

breaks = []

for i in range(N):
    for r in range(R-1):
        b = model.NewBoolVar(f"break_{i}_{r}")

        # b = 1 kalau sama (H-H atau A-A)
        model.Add(h[i,r] == h[i,r+1]).OnlyEnforceIf(b)
        model.Add(h[i,r] != h[i,r+1]).OnlyEnforceIf(b.Not())

        breaks.append(b)

big_home_count = {i: [] for i in range(N)}

for (t1, t2) in big_matches:
    i = team_idx[t1]
    j = team_idx[t2]

    for r in range(R):

        # i home vs j
        bh_i = model.NewBoolVar(f"bh_{i}_{j}_{r}")
        model.Add(x[i,j,r] == 1).OnlyEnforceIf(bh_i)
        model.Add(x[i,j,r] == 0).OnlyEnforceIf(bh_i.Not())

        # j home vs i
        bh_j = model.NewBoolVar(f"bh_{j}_{i}_{r}")
        model.Add(x[j,i,r] == 1).OnlyEnforceIf(bh_j)
        model.Add(x[j,i,r] == 0).OnlyEnforceIf(bh_j.Not())

        big_home_count[i].append(bh_i)
        big_home_count[j].append(bh_j)
        

big_penalties = []

for i in range(N):
    total = sum(big_home_count[i])

    under = model.NewIntVar(0, 10, f"under_{i}")
    over  = model.NewIntVar(0, 10, f"over_{i}")

    model.Add(total + under >= 2)
    model.Add(total - over <= 3)

    big_penalties.append(under)
    big_penalties.append(over)

plays_big = {}

for i in range(N):
    for r in range(R):
        plays_big[i, r] = model.NewBoolVar(f"plays_big_{i}_{r}")

for i in range(N):
    for r in range(R):
        model.Add(
            plays_big[i, r] ==
            sum(
                x[i, j, r] + x[j, i, r]
                for j in big_idx if j != i
            )
        )

big_violations = []

for i in range(N):
    for r in range(R - 3):
        v = model.NewBoolVar(f"big_window_{i}_{r}")

        # violation kalau > 2
        model.Add(
            plays_big[i, r] +
            plays_big[i, r+1] +
            plays_big[i, r+2] +
            plays_big[i, r+3]
            >= 3
        ).OnlyEnforceIf(v)

        model.Add(
            plays_big[i, r] +
            plays_big[i, r+1] +
            plays_big[i, r+2] +
            plays_big[i, r+3]
            <= 2
        ).OnlyEnforceIf(v.Not())

        big_violations.append(v)
# # =========================
# # Cross Break
# # =========================
# cross_breaks = []

# for i in range(N):
#     b = model.NewBoolVar(f"cross_break_{i}")

#     # bandingkan last round first half vs first round second half
#     model.Add(h[i, R-1] == h[i, R]).OnlyEnforceIf(b)
#     model.Add(h[i, R-1] != h[i, R]).OnlyEnforceIf(b.Not())

#     cross_breaks.append(b)

model.Minimize(
    7* sum(breaks) +
    3 * sum(big_penalties) +
    5 * sum(big_violations)
)

# =========================
# Solve
# =========================
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60

status = solver.Solve(model)

# =========================
# Output
# =========================
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    first_half = []
    for r in range(R):
        round_matches = []
        for i in range(N):
            for j in range(N):
                if i != j and solver.Value(x[i,j,r]) == 1:
                    round_matches.append((teams[i], teams[j]))
        first_half.append(round_matches)

    second_half = generate_second_half_semi_deterministic(first_half)

    full_schedule = first_half + second_half
    
    print_schedule(full_schedule, "FULL SCHEDULE")

    result = evaluate_full(full_schedule, teams, big_teams)

    print(result["total_breaks"])
    print(result["total_big_violations"])
    print(result["total_imbalance"])

    print("=== BREAK PER TEAM ===")
for t, v in sorted(result["breaks_per_team"].items(), key=lambda x: -x[1]):
    print(t, v)

print("\n=== BIG VIOLATIONS PER TEAM ===")
for t, v in sorted(result["big_per_team"].items(), key=lambda x: -x[1]):
    print(t, v)
    

