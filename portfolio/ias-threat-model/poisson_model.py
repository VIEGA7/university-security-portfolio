"""Supplement to MIAS 6-8. Attempts, not successful compromises. Rate: attempts/day."""
import argparse
import csv
import math
from pathlib import Path


def pmf(k, rate, days):
    if not isinstance(k, int) or isinstance(k, bool) or k < 0:
        raise ValueError('k must be a nonnegative integer')
    if not math.isfinite(rate) or not math.isfinite(days) or rate < 0 or days < 0:
        raise ValueError('rate and days must be finite and nonnegative')
    mean = rate*days
    if not math.isfinite(mean):
        raise ValueError('rate * days must be finite')
    if mean == 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(k*math.log(mean)-mean-math.lgamma(k+1))


def at_least_one(rate, days):
    pmf(0, rate, days)  # validate inputs
    return -math.expm1(-rate*days)


def scenario(n):
    if not isinstance(n, int) or n < 0:
        raise ValueError('n must be a nonnegative integer')
    rate1, rate2 = n*0.01, n*0.02
    rows = []
    for days in range(2, 31, 2):
        row = dict(n=n, days=days, rate1=rate1, rate2=rate2)
        row.update({f'p{k}_one_actor': pmf(k, rate1, days) for k in range(5)})
        row['p_more_than_4_one_actor'] = max(0, 1-sum(pmf(k, rate1, days) for k in range(5)))
        row['p_any_one_actor'] = at_least_one(rate1, days)
        row['p_any_two_independent_actors'] = at_least_one(rate1+rate2, days)
        row['expected_attempts_two_actors'] = (rate1+rate2)*days
        rows.append(row)
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n', type=int, default=11,
                        help='Explicit example parameter; the original report used N=00')
    parser.add_argument('--output', type=Path, default=Path('output/poisson.csv'))
    args = parser.parse_args()
    rows = scenario(args.n)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    print(f'N={args.n}; expected attempts over 14 days, two actors: {args.n*0.03*14:.4f}')
    print(f'P(at least one attempt over 30 days, one actor)={at_least_one(args.n*0.01,30):.6f}')
