"""Teaching analysis of independent binary A/B outcomes, using the standard library.

Uses a two-sided, pooled two-proportion z test and an unpooled Wald difference
interval. These are large-sample approximations, not sequential or clustered
inference. Sparse outcomes need another method. No network or packages needed.
"""
import argparse
import json
import math
from statistics import NormalDist


def analyze(n_a, x_a, n_b, x_b, alpha=0.05):
    for name, n, x in [('A', n_a, x_a), ('B', n_b, x_b)]:
        if type(n) is not int or type(x) is not int or n <= 0 or not 0 <= x <= n:
            raise ValueError(f'{name}: users must be a positive integer and conversions an integer from 0 to users')
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError('alpha must be finite and between 0 and 1')
    p_a, p_b = x_a / n_a, x_b / n_b
    delta = p_b - p_a
    pooled = (x_a + x_b) / (n_a + n_b)
    se_null = math.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    if se_null == 0:
        raise ValueError('All outcomes are identical: this normal test is degenerate; use an appropriate exact/score method')
    z = delta / se_null
    p_value = math.erfc(abs(z) / math.sqrt(2))
    se_est = math.sqrt(p_a * (1 - p_a) / n_a + p_b * (1 - p_b) / n_b)
    critical = NormalDist().inv_cdf(1 - alpha / 2)
    low, high = delta - critical * se_est, delta + critical * se_est
    warnings = []
    if min(x_a, n_a - x_a, x_b, n_b - x_b) < 10:
        warnings.append('Sparse outcomes: the normal/Wald approximation may be unreliable; 10 is only a heuristic.')
    return {
        'users_a': n_a, 'conversions_a': x_a, 'users_b': n_b, 'conversions_b': x_b,
        'rate_a': p_a, 'rate_b': p_b,
        'difference': delta,
        'difference_percentage_points': round(delta * 100, 10),
        'relative_lift_point_estimate': round(delta / p_a, 12) if p_a > 0 else None,
        'confidence_level_chosen_in_advance': 1 - alpha,
        'standard_error_for_difference_interval': se_est,
        'difference_ci': [low, high],
        'difference_ci_percentage_points': [low * 100, high * 100],
        'pooled_rate_under_equal_rates_hypothesis': pooled,
        'standard_error_under_equal_rates_hypothesis': se_null,
        'z_statistic': z,
        'p_value_two_sided': p_value,
        'reject_equal_rates_at_alpha_normal_approx': p_value < alpha,
        'warnings': warnings,
        'method': 'Pooled two-proportion z test; unpooled Wald difference CI. No posterior win probability is calculated.',
    }


def examples():
    return {
        'data_origin': 'Synthetic counts for teaching, not observed business experiment results',
        'users_14000_per_group': analyze(14000, 1400, 14000, 1554),
        'same_observed_lift_users_1000_per_group': analyze(1000, 100, 1000, 111),
        'same_counts_99_percent_interval': analyze(14000, 1400, 14000, 1554, alpha=0.01),
    }


def self_check():
    result = analyze(14000, 1400, 14000, 1554)
    assert math.isclose(result['p_value_two_sided'], 0.0027364859624517427, rel_tol=1e-10)
    assert math.isclose(result['difference_ci'][0], 0.0038047505313289826, rel_tol=1e-10)
    assert result['difference_ci'][0] > 0
    reverse = analyze(14000, 1554, 14000, 1400)
    assert math.isclose(reverse['p_value_two_sided'], result['p_value_two_sided'])
    assert math.isclose(reverse['difference_ci'][1], -result['difference_ci'][0])
    larger = analyze(56000, 5600, 56000, 6216)
    assert math.isclose(larger['standard_error_for_difference_interval'],
                        result['standard_error_for_difference_interval'] / 2)
    assert larger['p_value_two_sided'] < result['p_value_two_sided']
    wider = analyze(14000, 1400, 14000, 1554, alpha=0.01)
    assert wider['difference_ci'][0] < result['difference_ci'][0]
    equal = analyze(1000, 100, 1000, 100)
    assert equal['p_value_two_sided'] == 1 and equal['difference_ci'][0] < 0 < equal['difference_ci'][1]
    sparse = analyze(1000, 1, 1000, 3)
    assert sparse['warnings']
    for args in [(0, 0, 100, 10), (100, -1, 100, 10), (100, 101, 100, 10),
                 (100, 10.0, 100, 10), (100, 0, 100, 0), (100, 100, 100, 100),
                 (100, 10, 100, 10, 0), (100, 10, 100, 10, float('nan'))]:
        try:
            analyze(*args)
        except ValueError:
            continue
        raise AssertionError(f'Accepted unsupported input: {args}')
    print('PASS: reference example, reversal, sample scaling, confidence width, null, sparse and invalid/degenerate counts')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--users-a', type=int, default=14000)
    parser.add_argument('--conversions-a', type=int, default=1400)
    parser.add_argument('--users-b', type=int, default=14000)
    parser.add_argument('--conversions-b', type=int, default=1554)
    parser.add_argument('--alpha', type=float, default=0.05)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--self-check', action='store_true')
    modes.add_argument('--examples', action='store_true')
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return
    try:
        result = examples() if args.examples else analyze(
            args.users_a, args.conversions_a, args.users_b, args.conversions_b, args.alpha)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
