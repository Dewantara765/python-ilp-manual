
# =========================
# Semi-mirror function
# =========================
def generate_second_half(first_half, shift=1):
    R = len(first_half)
    second_half = []

    for r in range(R):
        source_round = (r + shift) % R
        matches = []

        for home, away in first_half[source_round]:
            matches.append((away, home))  # swap HA

        second_half.append(matches)

    return second_half