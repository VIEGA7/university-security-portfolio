"""Reconstructed variant 11. Standard library only; original listings in extracted/.

LP problems are solved by enumerating vertices of the bounded 2D feasible polygon.
KDZ 5 uses the same squared-distance objective as the report and finds its exact
polygon minimum, instead of pretending to restore the lost execution environment.
"""
import argparse
import csv
import itertools
import json
import math
from pathlib import Path
import random


def vertices(constraints, tolerance=1e-9):
    """Inequalities are triples (a, b, c): a*x + b*y <= c."""
    points = []
    for (a, b, c), (d, e, f) in itertools.combinations(constraints, 2):
        determinant = a * e - b * d
        if abs(determinant) < tolerance:
            continue
        p = ((c * e - b * f) / determinant, (a * f - c * d) / determinant)
        if all(u*p[0] + v*p[1] <= w + tolerance for u, v, w in constraints):
            if not any(math.dist(p, q) < tolerance for q in points):
                points.append(p)
    if not points:
        raise ValueError('Empty or unsupported feasible polygon')
    center = tuple(sum(p[i] for p in points)/len(points) for i in (0, 1))
    return sorted(points, key=lambda p: math.atan2(p[1]-center[1], p[0]-center[0]))


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def maximize(coefficients, constraints):
    point = max(vertices(constraints), key=lambda p: dot(coefficients, p))
    return point, dot(coefficients, point)


def dominates(a, b, minimize=False):
    direction = -1 if minimize else 1
    return all(direction*x >= direction*y for x, y in zip(a, b)) and any(
        direction*x > direction*y for x, y in zip(a, b))


def pareto(points, minimize=False):
    return [i for i, p in enumerate(points)
            if not any(dominates(q, p, minimize) for j, q in enumerate(points) if i != j)]


def efficiency(points):
    """Report formula F=1/(1+b/(N-1)); singleton convention F=1."""
    if len(points) <= 1:
        return [1.0] * len(points)
    return [1/(1 + sum(dominates(q, p) for q in points)/(len(points)-1)) for p in points]


def kdz1(count=200, seed=11):
    if count < 1:
        raise ValueError('count must be positive')
    rng = random.Random(seed)
    n = 11
    points = []
    while len(points) < count:
        x, y = rng.uniform(n/2, 3*n), rng.uniform(n/2, 2*n)
        if (x-n)**2/(4*n*n) + (y-n)**2/(n*n) <= 1:
            points.append((x, y))
    scores = efficiency(points)
    front = set(pareto(points))
    centers = (1, 0.85, 0.75)
    return [dict(id=i+1, f1=x, f2=y, efficiency=scores[i], pareto=i in front,
                 cluster=min(range(3), key=lambda k: (abs(scores[i]-centers[k]), k))+1)
            for i, (x, y) in enumerate(points)]


def kdz2(count=200, seed=11):
    if count < 1:
        raise ValueError('count must be positive')
    rng = random.Random(seed)
    decisions = [(rng.uniform(0, 79), rng.uniform(0, 79)) for _ in range(count)]
    criteria = [(0.2*(x-70)**2 + 0.8*(y-20)**2,
                 0.2*(x-10)**2 + 0.8*(y-70)**2) for x, y in decisions]
    # Intersection of [0.4,0.7] x [0.3,0.6] with mu1+mu2=1.
    weighted = [(0.4*a + 0.6*b, 0.7*a + 0.3*b) for a, b in criteria]
    front, omega = set(pareto(criteria, True)), set(pareto(weighted, True))
    return [dict(id=i+1, u1=p[0], u2=p[1], j1=criteria[i][0], j2=criteria[i][1],
                 pareto=i in front, omega=i in omega) for i, p in enumerate(decisions)]


BASE = [(-1, -1, -22), (1, -2, 11), (-3, 2, 22), (1, 0, 44),
        (0, 1, 33), (-1, 0, 0), (0, -1, 0)]
CRITERIA = [(1, 1), (-3, 1), (1, -3)]


def kdz3():
    constraints = BASE + [(-1, -1, -55), (-1, 3, 66)]
    point, value = maximize(CRITERIA[1], constraints)
    return dict(point=point, f2=value, criteria=[dot(c, point) for c in CRITERIA])


def kdz4():
    # Different feasible region than KDZ 3/5: transcribed from report equations and image2.png.
    constraints = [(1, 2, 44), (-2, -1, -11), (-1, 0, 0),
                   (0, -1, 0), (1, 0, 22), (0, 1, 16.5)]
    first, f2 = maximize(CRITERIA[1], constraints)
    constraints.append((3, -1, -(f2-2)))  # delta_f2=2, NOT positional delta_1=3.
    second, f1 = maximize(CRITERIA[0], constraints)
    constraints.append((-1, -1, -(f1-3)))  # delta_f1=3.
    third, f3 = maximize(CRITERIA[2], constraints)
    return dict(stages=[dict(point=first, f2=f2), dict(point=second, f1=f1),
                        dict(point=third, f3=f3)], concessions=dict(f2=2, f1=3))


def kdz5():
    polygon = vertices(BASE)
    # Compute ideal values rather than copying rounded constants from the old listing.
    ideal = [maximize(c, BASE)[1] for c in CRITERIA]
    def objective(p):
        return sum((dot(c, p)-goal)**2 for c, goal in zip(CRITERIA, ideal))
    # Solve unconstrained quadratic normal equations, then project onto each edge
    # using the objective's quadratic metric, not Euclidean distance.
    h11 = sum(c[0]**2 for c in CRITERIA)
    h12 = sum(c[0]*c[1] for c in CRITERIA)
    h22 = sum(c[1]**2 for c in CRITERIA)
    g1 = sum(c[0]*goal for c, goal in zip(CRITERIA, ideal))
    g2 = sum(c[1]*goal for c, goal in zip(CRITERIA, ideal))
    determinant = h11*h22-h12*h12
    unconstrained = ((g1*h22-h12*g2)/determinant, (h11*g2-h12*g1)/determinant)
    candidates = list(polygon)
    if all(a*unconstrained[0]+b*unconstrained[1] <= c+1e-9 for a,b,c in BASE):
        candidates.append(unconstrained)
    for p, q in zip(polygon, polygon[1:]+polygon[:1]):
        direction = (q[0]-p[0], q[1]-p[1])
        fd = [dot(c, direction) for c in CRITERIA]
        fp = [dot(c, p)-goal for c, goal in zip(CRITERIA, ideal)]
        t = max(0, min(1, -dot(fd, fp)/dot(fd, fd)))
        candidates.append((p[0]+t*direction[0], p[1]+t*direction[1]))
    best = min(candidates, key=objective)
    return dict(point=best, ideal=ideal, squared_distance=objective(best),
                criteria=[dot(c, best) for c in CRITERIA],
                method='exact minimum of the report objective over a 2D polygon')


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('output'))
    parser.add_argument('--count', type=int, default=200)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output/'kdz1.csv', kdz1(args.count))
    write_csv(args.output/'kdz2.csv', kdz2(args.count))
    result = {'kdz3': kdz3(), 'kdz4': kdz4(), 'kdz5': kdz5()}
    (args.output/'solutions.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
