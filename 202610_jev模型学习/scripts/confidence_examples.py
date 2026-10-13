"""离线演算：自构造概率分布，不调用 Jev API。"""

from math import isclose, isfinite


def validate(probabilities):
    if len(probabilities) < 2:
        raise ValueError("至少需要两个等级")
    if any(not isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("概率必须为 0 至 1 的有限数")
    if not isclose(sum(probabilities), 1.0, abs_tol=1e-9):
        raise ValueError("概率之和必须为 1")


def choice_confidence(probabilities):
    validate(probabilities)
    n = len(probabilities)
    return (max(probabilities) - 1 / n) / (1 - 1 / n)


def score_summary(probabilities):
    """输入按数值等级升序排列；精确并列时取最小等级。"""
    validate(probabilities)
    n = len(probabilities)
    modes = [i for i, p in enumerate(probabilities) if p == max(probabilities)]
    baseline = sum(abs(i - (n - 1) / 2) for i in range(n)) / n
    alternatives = {
        m: max(0.0, 1 - sum(p * abs(i - m) for i, p in enumerate(probabilities)) / baseline)
        for m in modes
    }
    return {
        "score": sum(i * p for i, p in enumerate(probabilities)),
        "modes": modes,
        "reference_mode": modes[0],
        "confidence": alternatives[modes[0]],
        "alternative_centers": alternatives,
        "highest_level_probability": probabilities[-1],
    }


if __name__ == "__main__":
    for name, values in {
        "明确中间等级": [0.0, 1.0, 0.0],
        "两个极端并列": [0.5, 0.0, 0.5],
        "并列中心影响公式": [0.4, 0.4, 0.0, 0.2],
    }.items():
        print(name, score_summary(values))
    print("三分类概率 0.85 对应 confidence:", choice_confidence([0.85, 0.10, 0.05]))
