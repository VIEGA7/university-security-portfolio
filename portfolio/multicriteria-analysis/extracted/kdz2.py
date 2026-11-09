# Extracted from a university report; see ../README.md.
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arc

# ==========================================================
# КДЗ №2
# Вариант 11
# ==========================================================

# Критерии:
# J1(u) = 0.2(u1 - 70)^2 + 0.8(u2 - 20)^2 -> min
# J2(u) = 0.2(u1 - 10)^2 + 0.8(u2 - 70)^2 -> min
#
# D:
# 0 <= u1 <= 79
# 0 <= u2 <= 79
#
# Интервалы весов:
# μ1 ∈ [0.4 ; 0.7]
# μ2 ∈ [0.3 ; 0.6]
# ==========================================================

MU1_MIN = 0.4
MU1_MAX = 0.7

MU2_MIN = 0.3
MU2_MAX = 0.6

# ==========================================================
# Построение матрицы полиэдрального конуса доминирования
# ==========================================================

def build_cone_matrix(mu1_min, mu1_max, mu2_min, mu2_max):

    vertices = [
        (mu1_min, mu2_min),  # 00
        (mu1_max, mu2_min),  # 01
        (mu1_max, mu2_max),  # 11
        (mu1_min, mu2_max)   # 10
    ]

    b_vectors = []

    for i in range(4):

        p = vertices[i]
        q = vertices[(i + 1) % 4]

        Lp = p[0] + p[1] - 1
        Lq = q[0] + q[1] - 1

        # пересечение внутри ребра
        if Lp * Lq < 0:

            denom = (q[0] + q[1]) - (p[0] + p[1])

            t = -Lp / denom

            mu1 = p[0] + t * (q[0] - p[0])
            mu2 = p[1] + t * (q[1] - p[1])

            b_vectors.append((mu1, mu2))

        # вершина лежит на прямой
        elif abs(Lp) < 1e-12:
            b_vectors.append(p)

        elif abs(Lq) < 1e-12:
            b_vectors.append(q)

    B = np.array(b_vectors)

    if len(B) > 0:
        B = np.unique(np.round(B, 12), axis=0)

    if len(B) == 2:
        angles = np.arctan2(B[:, 1], B[:, 0])
        B = B[np.argsort(angles)]

    return B

# ==========================================================
# Матрица конуса доминирования
# ==========================================================

B = build_cone_matrix(
    MU1_MIN,
    MU1_MAX,
    MU2_MIN,
    MU2_MAX
)

print("Матрица B:")
print(B)

for i, b in enumerate(B, start=1):
    print(f"b{i} = ({b[0]:.3f}, {b[1]:.3f})")

# ==========================================================
# Критерии
# ==========================================================

def criteria(U):

    u1 = U[:, 0]
    u2 = U[:, 1]

    j1 = 0.2 * (u1 - 70) ** 2 + 0.8 * (u2 - 20) ** 2
    j2 = 0.2 * (u1 - 10) ** 2 + 0.8 * (u2 - 70) ** 2

    return np.column_stack([j1, j2])

# ==========================================================
# Генерация точек
# ==========================================================

def generate_points(n, seed=11):

    rng = np.random.default_rng(seed)

    return rng.uniform(0, 79, size=(n, 2))

# ==========================================================
# Парето-множество
# ==========================================================

def pareto_min(F, eps=1e-12):

    order = np.lexsort((F[:, 1], F[:, 0]))

    best_j2 = np.inf
    keep = []

    for i in order:

        if F[i, 1] < best_j2 - eps:
            keep.append(i)
            best_j2 = F[i, 1]

    return np.array(keep, dtype=int)

# ==========================================================
# Ω-оптимальные решения
# ==========================================================

def omega_optimal(F, pareto_idx, B, eps=1e-9):

    P = F[pareto_idx]

    n = len(P)

    dominated = np.zeros(n, dtype=bool)

    for i in range(n):

        diff = P - P[i]

        vals = diff @ B.T

        mask = (
            np.all(vals <= eps, axis=1)
            & np.any(np.abs(diff) > eps, axis=1)
        )

        if np.any(mask):
            dominated[i] = True

    return pareto_idx[~dominated]

# ==========================================================
# Основные вычисления
# ==========================================================

def calculate(n):

    U = generate_points(n)

    F = criteria(U)

    pareto_idx = pareto_min(F)

    omega_idx = omega_optimal(F, pareto_idx, B)

    return U, F, pareto_idx, omega_idx

# ==========================================================
# Рисунок 1
# Геометрическая интерпретация
# ==========================================================

def plot_geometry():

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.set_title(
        "Геометрическая интерпретация полиэдрального конуса доминирования"
    )

    ax.set_xlim(-0.2, 1.1)
    ax.set_ylim(-0.2, 1.1)

    ax.set_xlabel(r'$\mu_1$')
    ax.set_ylabel(r'$\mu_2$')

    ax.grid(True, linestyle=':', alpha=0.5)

    # прямая μ1 + μ2 = 1

    x = np.linspace(0, 1.1, 300)

    ax.plot(
        x,
        1 - x,
        '--',
        color='gray',
        linewidth=1.5,
        label=r'$\mu_1+\mu_2=1$'
    )

    # гиперпараллелепипед

    rect = Rectangle(
        (MU1_MIN, MU2_MIN),
        MU1_MAX - MU1_MIN,
        MU2_MAX - MU2_MIN,
        facecolor='lightsteelblue',
        edgecolor='blue',
        linewidth=2,
        alpha=0.35,
        label='Π'
    )

    ax.add_patch(rect)

    # вершины

    pi0 = (MU1_MIN, MU2_MIN)
    pi1 = (MU1_MAX, MU2_MIN)
    pi2 = (MU1_MAX, MU2_MAX)
    pi3 = (MU1_MIN, MU2_MAX)

    ax.scatter(
        [pi0[0], pi1[0], pi2[0], pi3[0]],
        [pi0[1], pi1[1], pi2[1], pi3[1]],
        color='blue',
        s=35
    )

    ax.text(pi0[0], pi0[1] - 0.05, r'$\pi_0$')
    ax.text(pi1[0] + 0.01, pi1[1] - 0.03, r'$\pi_1$')
    ax.text(pi2[0] + 0.01, pi2[1] + 0.01, r'$\pi_2$')
    ax.text(pi3[0] - 0.05, pi3[1] + 0.01, r'$\pi_3$')

    # точки пересечения

    b1 = B[0]
    b2 = B[1]

    ax.scatter(
        [b1[0], b2[0]],
        [b1[1], b2[1]],
        color='purple',
        s=60,
        zorder=5
    )

    # векторы b1 b2

    ax.arrow(
        0,
        0,
        b1[0],
        b1[1],
        width=0.003,
        color='purple',
        length_includes_head=True
    )

    ax.arrow(
        0,
        0,
        b2[0],
        b2[1],
        width=0.003,
        color='purple',
        length_includes_head=True
    )

    ax.text(
        b1[0] + 0.02,
        b1[1],
        r'$b^1$',
        color='purple'
    )

    ax.text(
        b2[0] - 0.04,
        b2[1] + 0.03,
        r'$b^2$',
        color='purple'
    )

    # конус Ω

    ax.arrow(
        0,
        0,
        -0.12,
        0.15,
        width=0.002,
        color='green',
        length_includes_head=True
    )

    ax.arrow(
        0,
        0,
        0.12,
        -0.15,
        width=0.002,
        color='green',
        length_includes_head=True
    )

    ax.text(
        -0.08,
        0.03,
        r'$\Omega$',
        color='green',
        fontsize=14
    )

    # угол β

    arc = Arc(
        (0, 0),
        0.25,
        0.25,
        theta1=25,
        theta2=55,
        color='purple',
        lw=2
    )

    ax.add_patch(arc)

    ax.text(0.12, 0.09, r'$\beta$')

    # отметки интервалов

    ax.text(MU1_MIN, -0.12, r'$\mu_{1min}$', ha='center')
    ax.text(MU1_MAX, -0.12, r'$\mu_{1max}$', ha='center')

    ax.text(-0.14, MU2_MIN, r'$\mu_{2min}$', va='center')
    ax.text(-0.14, MU2_MAX, r'$\mu_{2max}$', va='center')

    ax.legend()

    plt.tight_layout()
    plt.show()

# ==========================================================
# Рисунок 2
# ==========================================================

def plot_reachable(F, n):

    plt.figure(figsize=(7, 5))

    plt.scatter(
        F[:, 0],
        F[:, 1],
        s=22 if n == 100 else 4,
        marker='D' if n == 100 else '.',
        alpha=0.75
    )

    plt.title(
        f'Множество достижимых векторных оценок ({n} точек)'
    )

    plt.xlabel('J1')
    plt.ylabel('J2')

    plt.grid(True)

    plt.tight_layout()
    plt.show()

# ==========================================================
# Рисунок 3
# ==========================================================

def plot_pareto(F, pareto_idx, n):

    mask = np.ones(len(F), dtype=bool)
    mask[pareto_idx] = False

    plt.figure(figsize=(7, 5))

    plt.scatter(
        F[mask, 0],
        F[mask, 1],
        alpha=0.3,
        s=15
    )

    plt.scatter(
        F[pareto_idx, 0],
        F[pareto_idx, 1],
        color='red',
        s=30
    )

    plt.title(
        f'Множество Парето-оптимальных решений ({n} точек)'
    )

    plt.xlabel('J1')
    plt.ylabel('J2')

    plt.grid(True)

    plt.tight_layout()
    plt.show()

# ==========================================================
# Рисунок 4
# ==========================================================

def plot_omega(F, pareto_idx, omega_idx, n):

    p_mask = np.zeros(len(F), dtype=bool)
    p_mask[pareto_idx] = True

    o_mask = np.zeros(len(F), dtype=bool)
    o_mask[omega_idx] = True

    p_only = p_mask & ~o_mask

    plt.figure(figsize=(7, 5))

    plt.scatter(
        F[p_only, 0],
        F[p_only, 1],
        s=20,
        alpha=0.5,
        label='Парето'
    )

    plt.scatter(
        F[omega_idx, 0],
        F[omega_idx, 1],
        s=60,
        color='cyan',
        edgecolor='blue',
        label='Ω'
    )

    plt.title(
        f'Множество Ω-оптимальных решений ({n} точек)'
    )

    plt.xlabel('J1')
    plt.ylabel('J2')

    plt.grid(True)

    plt.legend()

    plt.tight_layout()
    plt.show()

# ==========================================================
# Запуск
# ==========================================================

for n in (100, 10000):

    U, F, pareto_idx, omega_idx = calculate(n)

    print()
    print(f'Количество точек: {n}')
    print(f'Парето-оптимальных решений: {len(pareto_idx)}')
    print(f'Ω-оптимальных решений: {len(omega_idx)}')

    plot_reachable(F, n)
    plot_pareto(F, pareto_idx, n)
    plot_omega(F, pareto_idx, omega_idx, n)

plot_geometry()
