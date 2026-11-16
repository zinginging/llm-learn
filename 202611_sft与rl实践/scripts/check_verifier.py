"""Offline tests of the reward boundary and grouped data separation; standard library only."""

from common import correctness_reward, data_splits, is_correct


def main():
    assert is_correct("5", "5") and is_correct(" 5\n", "5")
    for bad in ["", "05", "5 or 6", "The answer is 5", "=5", "5!", "5\n6", "-5", "5.0"]:
        assert not is_correct(bad, "5"), bad
    assert not is_correct("6", "5")
    assert correctness_reward(["5", "6", "5 or 6"], ["5", "5", "5"]) == [1, 0, 0]
    try:
        correctness_reward(["5"], [])
    except ValueError:
        pass
    else:
        raise AssertionError("Length mismatch was accepted")
    groups = {}
    for split, rows in data_splits().items():
        for row in rows:
            a, b = map(int, row["prompt"][:-1].split("+"))
            group = (min(a, b), max(a, b))
            assert group not in groups or groups[group] == split
            groups[group] = split
    print("PASS: canonical-answer verifier, malformed outputs, aligned rewards, commutative-group split")


if __name__ == "__main__":
    main()
