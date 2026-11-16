"""Offline, standard-library checks of the PO teaching examples; no model/network needed."""

import math


def grpo_advantages(rewards, eps=1e-4):
    if len(rewards) < 2:
        raise ValueError("A relative-reward group needs at least two samples")
    mean = sum(rewards) / len(rewards)
    std = math.sqrt(sum((r - mean) ** 2 for r in rewards) / (len(rewards) - 1))
    return [(r - mean) / (std + eps) for r in rewards]


def rloo_advantages(rewards):
    if len(rewards) < 2:
        raise ValueError("Leave-one-out needs at least two samples")
    return [r - (sum(rewards) - r) / (len(rewards) - 1) for r in rewards]


def clipped_surrogate(ratio, advantage, epsilon=0.2):
    clipped = min(1 + epsilon, max(1 - epsilon, ratio))
    return min(ratio * advantage, clipped * advantage)


def main():
    assert math.isclose(math.log1p(math.exp(0)), math.log(2))
    assert math.isclose(math.log1p(math.exp(-1)), 0.31326168751822286)
    assert math.isclose(clipped_surrogate(1.5, 2), 2.4)
    assert math.isclose(clipped_surrogate(1.5, -2), -3.0)
    assert grpo_advantages([0, 0, 0, 0]) == [0.0] * 4
    assert grpo_advantages([1, 1]) == [0.0, 0.0]
    assert rloo_advantages([1, 0]) == [1.0, -1.0]
    a = grpo_advantages([1, 0])
    assert math.isclose(a[0], 0.5 / (math.sqrt(0.5) + 1e-4))
    assert math.isclose(sum(a), 0.0)
    for fn in (grpo_advantages, rloo_advantages):
        for bad in ([], [1]):
            try:
                fn(bad)
            except ValueError:
                pass
            else:
                raise AssertionError("Invalid group was accepted")
    # IPO has a finite optimum, unlike DPO's monotonic margin objective.
    beta = 0.1
    target = 1 / (2 * beta)
    assert (target - target) ** 2 == 0 and (target + 1 - target) ** 2 == 1
    # GSPO's geometric mean is distinct from the average token ratio.
    ratios = [2.0, 0.5]
    assert math.isclose(math.exp(sum(map(math.log, ratios)) / 2), 1.0)
    assert sum(ratios) / 2 == 1.25
    # Same token contributions, different length normalizers: no optimizer involved here.
    token_terms = [[1.0], [1.0, 1.0, 1.0]]
    grpo = sum(sum(row) / len(row) for row in token_terms) / 2
    dapo = sum(map(sum, token_terms)) / sum(map(len, token_terms))
    dr_grpo = sum(map(sum, token_terms)) / (2 * 4)
    assert (grpo, dapo, dr_grpo) == (1.0, 1.0, 0.5)
    # Nonuniform contributions reveal GRPO sequence weighting vs token weighting.
    token_terms = [[2.0], [0.0, 0.0, 0.0]]
    assert sum(sum(row) / len(row) for row in token_terms) / 2 == 1.0
    assert sum(map(sum, token_terms)) / 4 == 0.5
    # Illustrate DAPO's binary-outcome filtering, without claiming dynamic training.
    groups = [[0, 0], [1, 1], [1, 0]]
    kept = [group for group in groups if min(group) != max(group)]
    assert kept == [[1, 0]]
    print("PASS: DPO/PPO/GRPO/RLOO/GSPO, normalization and filtering examples")


if __name__ == "__main__":
    main()
