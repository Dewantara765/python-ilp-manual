from ortools.sat.python import cp_model
from second_half import generate_second_half


teams = [
    "ARS","AVL","BOU","BRE","BHA",
    "BUR","CHE","CRY","EVE","FUL",
    "LEE","LIV","MCI","MUN","NEW",
    "NFO","SUN","TOT","WHU","WOL"
]#contoh liga inggris


big_matches = [ ("ARS","CHE"), ("ARS","LIV"), ("ARS","MCI"), ("ARS","MUN"), ("ARS","TOT"), 
                ("CHE","LIV"), ("CHE","MCI"), ("CHE","MUN"), ("CHE","TOT"), 
                ("LIV","MCI"), ("LIV","MUN"), ("LIV","TOT"), 
                ("MCI","MUN"), ("MCI","TOT"), 
                ("MUN","TOT") ]


derby_pairs = [("ARS","TOT"), ("CHE","FUL"), ("EVE","LIV"), ("MCI","MUN"), ("NEW","SUN")]

N = len(teams)
R = N - 1  # 19 round

shift = 9

team_idx = {t:i for i,t in enumerate(teams)}

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

    for r in [0, 8]:  # Round 1 & Round 3
        model.Add(x[i,j,r] == 0)
        model.Add(x[j,i,r] == 0)

for (t1, t2) in big_matches:
    i = team_idx[t1]
    j = team_idx[t2]

    model.Add(x[i,j,8] == 0)
    model.Add(x[j,i,8] == 0)

# =========================
# Avoid HH-A-HH & AA-H-AA
# =========================
hhahh = []
aahaa = []

for i in range(N):
    for r in range(R - 4):

        # HH-A-HH
        sum1 = (
            h[i,r] + h[i,r+1] + (1-h[i,r+2]) +
            h[i,r+3] + h[i,r+4]
        )

        v1 = model.NewBoolVar(f"hhahh_{i}_{r}")
        model.Add(sum1 == 5).OnlyEnforceIf(v1)
        model.Add(sum1 <= 4).OnlyEnforceIf(v1.Not())

        hhahh.append(v1)

        # AA-H-AA
        sum2 = (
            (1-h[i,r]) + (1-h[i,r+1]) + h[i,r+2] +
            (1-h[i,r+3]) + (1-h[i,r+4])
        )

        v2 = model.NewBoolVar(f"aahaa_{i}_{r}")
        model.Add(sum2 == 5).OnlyEnforceIf(v2)
        model.Add(sum2 <= 4).OnlyEnforceIf(v2.Not())

        aahaa.append(v2)
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
    5 * sum(breaks) +
    3 * (sum(hhahh) + sum(aahaa)) +
    4 * sum(big_penalties)
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

    second_half = generate_second_half(first_half, shift=9)
    
    print_schedule(first_half, "FIRST HALF")
    print_schedule(second_half, "SECOND HALF")

