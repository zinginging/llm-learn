"""Synthetic Pearson chi-square and Welch t examples; requires SciPy 1.17.0.

No network, credentials or real user data. Run --self-check for formula checks;
otherwise print teaching examples as JSON. This is not a production analyzer.
"""
import argparse
import json
import math
import scipy
from scipy import stats


def examples():
    table = [[1400, 12600], [1554, 12446]]  # columns: converted, not converted
    pearson = stats.chi2_contingency(table, correction=False)
    corrected = stats.chi2_contingency(table, correction=True)
    rate_a, rate_b = 1400 / 14000, 1554 / 14000
    pooled = (1400 + 1554) / 28000
    z = (rate_b - rate_a) / math.sqrt(pooled * (1 - pooled) * 2 / 14000)

    n_a = n_b = 100
    mean_a, mean_b, sd_a, sd_b = 100.0, 110.0, 30.0, 30.0
    welch = stats.ttest_ind_from_stats(
        mean1=mean_b, std1=sd_b, nobs1=n_b,
        mean2=mean_a, std2=sd_a, nobs2=n_a,
        equal_var=False, alternative='two-sided')
    var_a, var_b = sd_a ** 2 / n_a, sd_b ** 2 / n_b
    se = math.sqrt(var_a + var_b)
    df = (var_a + var_b) ** 2 / (var_a ** 2 / (n_a - 1) + var_b ** 2 / (n_b - 1))
    critical = float(stats.t.ppf(0.975, df))
    difference = mean_b - mean_a

    # A user's binary outcome is also a numeric observation; its mean is a rate.
    binary_sd_a = math.sqrt(rate_a * (1 - rate_a) * 14000 / 13999)
    binary_sd_b = math.sqrt(rate_b * (1 - rate_b) * 14000 / 13999)
    binary_t = stats.ttest_ind_from_stats(
        mean1=rate_b, std1=binary_sd_b, nobs1=14000,
        mean2=rate_a, std2=binary_sd_a, nobs2=14000,
        equal_var=False, alternative='two-sided')
    return {
        'data_origin': 'Synthetic teaching counts and summary statistics; no observed business effect',
        'scipy_version': scipy.__version__,
        'pearson_chi2_binary_conversion': {
            'observed': table, 'expected_under_independence': pearson.expected_freq.tolist(),
            'continuity_correction': False, 'statistic': float(pearson.statistic),
            'degrees_of_freedom': int(pearson.dof), 'p_value': float(pearson.pvalue),
            'pooled_proportion_z_squared': z * z,
            'yates_corrected_p_value_for_comparison': float(corrected.pvalue),
        },
        'welch_mean_revenue': {
            'users_a': n_a, 'users_b': n_b, 'mean_a_yuan': mean_a, 'mean_b_yuan': mean_b,
            'sample_sd_a_yuan': sd_a, 'sample_sd_b_yuan': sd_b,
            'mean_difference_yuan': difference, 'standard_error_yuan': se,
            't_statistic_b_minus_a': float(welch.statistic), 'degrees_of_freedom': df,
            'p_value_two_sided': float(welch.pvalue), 'confidence_level': 0.95,
            'difference_ci_yuan': [difference - critical * se, difference + critical * se],
        },
        'welch_on_same_binary_conversion_counts': {
            't_statistic_b_minus_a': float(binary_t.statistic),
            'p_value_two_sided': float(binary_t.pvalue),
            'note': 'Large-sample illustration: close to, not exactly equal to, the Pearson/proportion z result.',
        },
        'confidence_label_warning': 'No posterior win probability is computed. A platform may display 1-p, but the test name does not define that label.',
    }


def self_check():
    result = examples()
    chi = result['pearson_chi2_binary_conversion']
    assert math.isclose(chi['statistic'], chi['pooled_proportion_z_squared'], rel_tol=1e-12)
    assert math.isclose(chi['p_value'], math.erfc(math.sqrt(chi['statistic'] / 2)), rel_tol=1e-12)
    reverse = stats.chi2_contingency(list(reversed(chi['observed'])), correction=False)
    assert math.isclose(float(reverse.pvalue), chi['p_value'], rel_tol=1e-12)
    # Construct raw synthetic values with exactly the documented sample mean/SD.
    n = 100
    offset = 30 * math.sqrt((n - 1) / n)
    raw_a = [100 - offset] * 50 + [100 + offset] * 50
    raw_b = [110 - offset] * 50 + [110 + offset] * 50
    raw = stats.ttest_ind(raw_b, raw_a, equal_var=False, alternative='two-sided')
    welch = result['welch_mean_revenue']
    assert math.isclose(float(raw.statistic), welch['t_statistic_b_minus_a'], rel_tol=1e-12)
    assert math.isclose(float(raw.pvalue), welch['p_value_two_sided'], rel_tol=1e-12)
    assert welch['difference_ci_yuan'][0] > 0
    print('PASS: Pearson/z equivalence, reversal, p-value tail and raw/summary Welch agreement')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-check', action='store_true')
    args = parser.parse_args()
    if args.self_check:
        self_check()
    else:
        print(json.dumps(examples(), ensure_ascii=False, indent=2))
