"""Plan independent two-proportion A/B tests using only the Python standard library.

Two-sided pooled-null normal approximation, without continuity correction. The
closed-form planning formula ignores the negligible opposite tail for the power
target. It is not a sequential, cluster-randomized, ratio-metric or revenue test.
No network, credentials, model calls or external packages are used.
All proportions use decimals: 0.10 means 10%, not 0.10%.
"""
import argparse
import json
import math
from statistics import NormalDist

NORMAL = NormalDist()


def probability(value, name, lower=0.0, upper=1.0):
    if not math.isfinite(value) or not lower < value < upper:
        raise ValueError(f'{name} must be between {lower} and {upper}, exclusive')


def variance_terms(baseline, target, treatment_share):
    ratio = treatment_share / (1 - treatment_share)  # n_B / n_A
    pooled = (baseline + ratio * target) / (1 + ratio)
    null_var = pooled * (1 - pooled) * (1 + 1 / ratio)
    alt_var = baseline * (1 - baseline) + target * (1 - target) / ratio
    return ratio, math.sqrt(null_var), math.sqrt(alt_var)


def sample_size(baseline, target, alpha=0.05, power=0.80, treatment_share=0.50):
    for name, value in [('baseline', baseline), ('target', target),
                        ('treatment_share', treatment_share)]:
        probability(value, name)
    probability(alpha, 'alpha', upper=0.5)
    probability(power, 'power', lower=0.5)
    delta = abs(target - baseline)
    if delta == 0:
        raise ValueError('baseline and target must differ; no finite sample detects zero difference')
    ratio, std_null, std_alt = variance_terms(baseline, target, treatment_share)
    required_a = ((NORMAL.inv_cdf(1 - alpha / 2) * std_null
                   + NORMAL.inv_cdf(power) * std_alt) / delta) ** 2
    n_a = math.ceil(required_a)
    n_b = math.ceil(ratio * n_a)
    # Rounding B up after A is conservative. Integer quotas may differ slightly
    # from the requested allocation ratio.
    return n_a, n_b


def normal_power(baseline, target, n_a, alpha=0.05, treatment_share=0.50):
    """Evaluate both normal rejection tails; not an empirical business power."""
    _, std_null, std_alt = variance_terms(baseline, target, treatment_share)
    critical = NORMAL.inv_cdf(1 - alpha / 2) * std_null / math.sqrt(n_a)
    se_alt = std_alt / math.sqrt(n_a)
    delta = abs(target - baseline)
    return (1 - NORMAL.cdf((critical - delta) / se_alt)
            + NORMAL.cdf((-critical - delta) / se_alt))


def plan(baseline=0.10, target=0.11, alpha=0.05, power=0.80,
         treatment_share=0.50, enrollment=0.20, daily_new_users=10000,
         min_days=7, outcome_lag_days=0):
    if not math.isfinite(enrollment) or not 0 < enrollment <= 1:
        raise ValueError('enrollment must be positive and at most 1')
    if not math.isfinite(daily_new_users) or daily_new_users <= 0:
        raise ValueError('daily_new_users must be positive and finite')
    for name, value in [('min_days', min_days), ('outcome_lag_days', outcome_lag_days)]:
        if not isinstance(value, int) or value < 0:
            raise ValueError(f'{name} must be a nonnegative integer')
    n_a, n_b = sample_size(baseline, target, alpha, power, treatment_share)
    daily_a = daily_new_users * enrollment * (1 - treatment_share)
    daily_b = daily_new_users * enrollment * treatment_share
    fill_days = math.ceil(max(n_a / daily_a, n_b / daily_b))
    warnings = []
    if min(n_a * baseline, n_a * (1 - baseline),
           n_b * target, n_b * (1 - target)) < 10:
        warnings.append('Low expected event/non-event counts: reassess normal approximation; 10 is only a heuristic.')
    return {
        'baseline': baseline, 'target': target,
        'absolute_change_percentage_points': (target - baseline) * 100,
        'relative_change': (target - baseline) / baseline,
        'alpha_two_sided': alpha, 'target_power': power,
        'enrollment_fraction': enrollment,
        'treatment_share_within_experiment': treatment_share,
        'whole_population_a_fraction': enrollment * (1 - treatment_share),
        'whole_population_b_fraction': enrollment * treatment_share,
        'required_users_a': n_a, 'required_users_b': n_b,
        'required_total_users': n_a + n_b,
        'estimated_daily_new_eligible_users': daily_new_users,
        'estimated_daily_a': daily_a, 'estimated_daily_b': daily_b,
        'sample_collection_days': fill_days,
        'minimum_business_cycle_days': min_days,
        'outcome_lag_days': outcome_lag_days,
        'planned_enrollment_days': max(fill_days, min_days),
        'planned_calendar_days_approx': max(fill_days, min_days) + outcome_lag_days,
        'normal_approx_power_at_planned_a': normal_power(
            baseline, target, n_a, alpha, treatment_share),
        'warnings': warnings,
        'scope': 'Independent randomized users, one binary result per user, fixed-horizon normal approximation; no guarantee of significance.',
    }


def examples():
    return {
        'parameters': {'baseline': 0.10, 'alpha_two_sided': 0.05,
                       'power': 0.80, 'daily_new_eligible_users': 10000},
        'effect_sizes': [plan(target=p) for p in [0.12, 0.11, 0.105, 0.102, 0.101]],
        'traffic_fractions': [plan(enrollment=q) for q in [1.0, 0.20, 0.10]],
        'unequal_allocation_90a_10b': plan(enrollment=1.0, treatment_share=0.10),
        'seven_day_outcome': plan(enrollment=0.20, outcome_lag_days=7),
        'user_case_20261118': {
            'provided_parameters': {'baseline': 0.10, 'expected_lift': 0.11,
                                    'daily_eligible_users': 20000},
            'assumptions': 'Treat lift as relative and as the planning effect. Daily users are assumed newly enrolled and deduplicated; outcome lag was not provided.',
            'relative_lift_11_percent': [plan(target=0.111, daily_new_users=20000, enrollment=q)
                                         for q in [1.0, 0.20, 0.10]],
            'alternative_target_11_percent': plan(target=0.11, daily_new_users=20000, enrollment=0.20),
            'relative_lift_with_seven_day_outcome': plan(target=0.111, daily_new_users=20000,
                                                       enrollment=0.20, outcome_lag_days=7),
        },
    }


def self_check():
    a, b = sample_size(0.10, 0.11)
    assert (a, b) == (14751, 14751)
    assert sample_size(0.11, 0.10) == (a, b)
    assert sample_size(0.10, 0.105)[0] == 57763
    assert sample_size(0.10, 0.111) == (12242, 12242)
    assert sample_size(0.10, 0.105)[0] > a
    assert sample_size(0.10, 0.11, power=0.90)[0] > a
    assert sample_size(0.10, 0.11, alpha=0.01)[0] > a
    assert sum(sample_size(0.10, 0.11, treatment_share=0.10)) > a + b
    for p0, p1, share in [(0.10, 0.11, 0.5), (0.10, 0.105, 0.5),
                          (0.10, 0.11, 0.1), (0.40, 0.38, 0.7)]:
        n_a, _ = sample_size(p0, p1, treatment_share=share)
        assert normal_power(p0, p1, n_a, treatment_share=share) >= 0.80
    assert plan(enrollment=1)['sample_collection_days'] == 3
    assert plan(enrollment=1)['planned_enrollment_days'] == 7
    assert plan()['sample_collection_days'] == 15
    assert plan(enrollment=0.10)['sample_collection_days'] == 30
    assert plan(outcome_lag_days=7)['planned_calendar_days_approx'] == 22
    assert plan(target=0.111, daily_new_users=20000)['sample_collection_days'] == 7
    invalid = [dict(baseline=0), dict(target=1), dict(target=0.10),
               dict(baseline=float('nan')), dict(power=0.5), dict(alpha=0),
               dict(treatment_share=0), dict(treatment_share=1),
               dict(enrollment=0), dict(enrollment=1.01),
               dict(daily_new_users=0), dict(outcome_lag_days=-1)]
    for kwargs in invalid:
        try:
            plan(**kwargs)
        except ValueError:
            continue
        raise AssertionError(f'Accepted invalid inputs: {kwargs}')
    print('PASS: reference values, symmetry, sensitivity, unequal allocation, power, timing and invalid inputs')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=float, default=0.10)
    parser.add_argument('--target', type=float, default=0.11)
    parser.add_argument('--alpha', type=float, default=0.05)
    parser.add_argument('--power', type=float, default=0.80)
    parser.add_argument('--treatment-share', type=float, default=0.50)
    parser.add_argument('--enrollment', type=float, default=0.20)
    parser.add_argument('--daily-new-users', type=float, default=10000)
    parser.add_argument('--min-days', type=int, default=7)
    parser.add_argument('--outcome-lag-days', type=int, default=0)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--self-check', action='store_true')
    mode.add_argument('--examples', action='store_true')
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return
    try:
        result = examples() if args.examples else plan(
            args.baseline, args.target, args.alpha, args.power,
            args.treatment_share, args.enrollment, args.daily_new_users,
            args.min_days, args.outcome_lag_days)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
