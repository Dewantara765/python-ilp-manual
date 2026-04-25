import random

def generate_second_half_semi_deterministic(first_half, base_shift=10, jitter=1):
    R = len(first_half)
    second_half = [None] * R

    fixed_map = {
        8: 17,
        9: 18
    }

    used_targets = set(fixed_map.values())
    mapping = {}  # <-- simpan mapping di sini

    # =========================
    # apply fixed mapping
    # =========================
    for src, dst in fixed_map.items():
        second_half[dst] = [(away, home) for home, away in first_half[src]]
        mapping[src] = dst  # <-- catat mapping

    # =========================
    # semi-deterministic mapping
    # =========================
    remaining_src = [r for r in range(R) if r not in fixed_map]

    def circular_distance(a, b, R):
            return min(abs(a - b), R - abs(a - b))
    
    for src in remaining_src:
        ideal = (src + R//2) % R

    # deviation kecil dari ideal
        target = (ideal + random.choice([-1, 0, 1])) % R
        

        # bias supaya tidak terlalu jauh dari ideal
        if circular_distance(target, ideal, R) > 2:
            target = ideal

        # resolve collision
        while target in used_targets:
            target = (target + 1) % R

        second_half[target] = [(away, home) for home, away in first_half[src]]
        used_targets.add(target)

        mapping[src] = target  # <-- catat mapping

    return second_half, mapping