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

    for src in remaining_src:
        # base mapping (deterministic)
        target = (src + base_shift) % R

        # small controlled variation (jitter)
        if jitter > 0:
            shift_variation = random.choice([-jitter, 0, jitter])
            target = (target + shift_variation) % R

        # resolve collision
        while target in used_targets:
            target = (target + 1) % R

        second_half[target] = [(away, home) for home, away in first_half[src]]
        used_targets.add(target)

        mapping[src] = target  # <-- catat mapping

    return second_half, mapping