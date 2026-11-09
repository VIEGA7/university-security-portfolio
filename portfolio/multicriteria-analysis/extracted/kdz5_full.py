# Extracted from a university report; see ../README.md.
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from scipy.optimize import linprog

# Параметры задачи
n = 11

# Начальная точка (согласно варианту 11: 11 ≤ n ≤ 15 → x⁰ = [2n, n])
x0 = np.array([2*n, n], dtype=float)  # [22, 11]

# Идеальная точка (из Этапа 1)
f_star = np.array([77.0, 4.4, 7.3333])

# Матрица коэффициентов критериев
Acrit = np.array([[1, 1], [-3, 1], [1, -3]], dtype=float)

# Ограничения: A_ub * x <= b_ub
A_ub = np.array([
    [-1, -1],   # -x1 - x2 <= -22
    [1, -2],    # x1 - 2x2 <= 11
    [-3, 2],    # -3x1 + 2x2 <= 22
    [1, 0],     # x1 <= 44
    [0, 1]      # x2 <= 33
], dtype=float)

b_ub = np.array([-2*n, n, 2*n, 4*n, 3*n], dtype=float)

# Границы переменных
bounds = [(0, None), (0, None)]

def rho(x):
    """Функция метрики ρ(x)"""
    d = Acrit @ x - f_star
    return float(d @ d)

def grad_rho(x):
    """Градиент функции ρ(x)"""
    d = Acrit @ x - f_star
    return 2.0 * (Acrit.T @ d)

def solve_lp(c):
    """Решает задачу min c^T * x при ограничениях A_ub*x <= b_ub, x >= 0"""
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    if res.status != 0:
        raise RuntimeError(f"Ошибка linprog: {res.message}")
    return res.x

def frank_wolfe_algorithm(x_start, eps=0.01, max_iter=5000, verbose=True):
    """
    Алгоритм Франка-Вульфа для минимизации ρ(x) на области D

    Параметры:
    - x_start: начальная точка
    - eps: точность остановки |ρ(x^{k+1}) - ρ(x^k)| ≤ eps
    - max_iter: максимальное число итераций
    - verbose: печать прогресса

    Возвращает:
    - x_opt: оптимальная точка
    - history: список всех точек x^k
    - rho_history: список значений ρ(x^k)
    - iter_count: количество итераций
    """
    xk = x_start.copy()
    history = [xk.copy()]
    rho_history = [rho(xk)]

    if verbose:
        print("=" * 70)
        print("Метод Франка-Вульфа")
        print(f"n = {n}, начальная точка x⁰ = [{xk[0]:.4f}, {xk[1]:.4f}]")
        print(f"ρ(x⁰) = {rho_history[0]:.6f}")
        print(f"Критерий остановки: |ρ(x^{{k+1}}) - ρ(x^k)| ≤ {eps}")
        print("=" * 70)
        print(f"{'Ит.':>4} | {'x₁':>10} | {'x₂':>10} | {'ρ(x)':>12} | {'Δρ':>12} |")
        print("-" * 70)
        print(f"{0:>4} | {xk[0]:10.6f} | {xk[1]:10.6f} | {rho_history[0]:12.6f} | {'—':>12} |")

    for k in range(max_iter):
        # Шаг 1: Вычисляем градиент в текущей точке
        g = grad_rho(xk)

        # Шаг 2: Решаем вспомогательную задачу ЛП
        sk = solve_lp(g)

        # Шаг 3: Находим оптимальный шаг λ
        d = sk - xk
        Ad = Acrit @ d
        r = Acrit @ xk - f_star

        a_quad = float(Ad @ Ad)
        b_quad = float(2.0 * (r @ Ad))

        if a_quad <= 1e-12:  # почти линейная функция
            lam = 0.0 if b_quad >= 0 else 1.0
        else:
            lam = -b_quad / (2 * a_quad)
            lam = max(0.0, min(1.0, lam))

        # Шаг 4: Вычисляем новую точку
        x_next = xk + lam * d
        rho_next = rho(x_next)

        history.append(x_next.copy())
        rho_history.append(rho_next)

        delta = abs(rho_next - rho_history[-2])

        if verbose and (k + 1) % 100 == 0:
            print(f"{k+1:>4} | {x_next[0]:10.6f} | {x_next[1]:10.6f} | {rho_next:12.6f} | {delta:12.6f} |")

        # Проверка условия остановки
        if delta <= eps:
            if verbose:
                print("-" * 70)
                print(f"{k+1:>4} | {x_next[0]:10.6f} | {x_next[1]:10.6f} | {rho_next:12.6f} | {delta:12.6f} |")
                print("=" * 70)
                print(f"✓ Остановка на итерации {k+1}")
                print(f"  |ρ(x^{k+1}) - ρ(x^k)| = {delta:.8f} ≤ {eps}")
            break

        xk = x_next

    else:
        if verbose:
            print(f"⚠ Достигнуто максимальное число итераций ({max_iter})")

    x_opt = history[-1]

    if verbose:
        print(f"\nРезультат:")
        print(f"  x* = [{x_opt[0]:.6f}, {x_opt[1]:.6f}]")
        print(f"  ρ(x*) = {rho_history[-1]:.6f}")
        print(f"  Количество итераций: {len(history)-1}")

    return x_opt, history, rho_history, len(history)-1

def get_feasible_polygon():
    """Получение вершин допустимой области D"""
    A_all = list(A_ub) + [[-1, 0], [0, -1]]
    b_all = list(b_ub) + [0.0, 0.0]
    verts = []
    m = len(A_all)

    for i in range(m):
        for j in range(i+1, m):
            A2 = np.array([A_all[i], A_all[j]], dtype=float)
            b2 = np.array([b_all[i], b_all[j]], dtype=float)

            if abs(np.linalg.det(A2)) < 1e-10:
                continue

            try:
                v = np.linalg.solve(A2, b2)
            except:
                continue

            if all(np.dot(A_all[k], v) <= b_all[k] + 1e-7 for k in range(m)):
                verts.append(v)

    if not verts:
        return np.empty((0, 2))

    pts = np.array(verts)
    center = pts.mean(0)
    angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
    return pts[np.argsort(angles)]

def plot_trajectory(history, rho_history, x0, x_opt, n):
    """
    Построение графика траектории в пространстве x и графика сходимости
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle(f'Метод Франка-Вульфа (n = {n})', fontsize=15, fontweight='bold')

    # ========== Левый график: траектория в пространстве x ==========
    ax1 = axes[0]
    ax1.set_title('Траектория в пространстве $x$', fontsize=13, fontweight='bold')

    # Отрисовка допустимой области
    poly = get_feasible_polygon()
    if len(poly) >= 3:
        patch = MplPolygon(poly, closed=True, facecolor='#d4e8fc',
                           alpha=0.4, edgecolor='black', linewidth=1.5)
        ax1.add_patch(patch)

    # Линии ограничений
    x_plt = np.linspace(-5, 4*n+15, 600)
    ax1.plot(x_plt, 2*n - x_plt, 'k--', linewidth=1, alpha=0.5)
    ax1.plot(x_plt, (x_plt - n)/2, 'k--', linewidth=1, alpha=0.5)
    ax1.plot(x_plt, (2*n + 3*x_plt)/2, 'k--', linewidth=1, alpha=0.5)
    ax1.axvline(4*n, color='k', linestyle='--', linewidth=1, alpha=0.5)
    ax1.axhline(3*n, color='k', linestyle='--', linewidth=1, alpha=0.5)
    ax1.axhline(0, color='black', linewidth=1)
    ax1.axvline(0, color='black', linewidth=1)

    # Траектория
    history_arr = np.array(history)
    ax1.plot(history_arr[:, 0], history_arr[:, 1], 'b-', linewidth=1.5,
             alpha=0.7, label='траектория')
    ax1.plot(history_arr[:, 0], history_arr[:, 1], 'bo', markersize=3, alpha=0.6)

    # Начальная и конечная точки
    ax1.plot(x0[0], x0[1], 'go', markersize=12, label='$x^0$ (начальная)', zorder=5)
    ax1.plot(x_opt[0], x_opt[1], 'ro', markersize=12, label='$x^*$ (оптимальная)', zorder=5)

    # Аннотации для начальной и конечной точек
    ax1.annotate(f'$x^0 = [{x0[0]:.1f}, {x0[1]:.1f}]$',
                 xy=x0, xytext=(-30, 15), textcoords='offset points',
                 fontsize=10, color='green', fontweight='bold',
                 bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='green', alpha=0.9))

    ax1.annotate(f'$x^* = [{x_opt[0]:.2f}, {x_opt[1]:.2f}]$',
                 xy=x_opt, xytext=(15, -25), textcoords='offset points',
                 fontsize=10, color='red', fontweight='bold',
                 bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='red', alpha=0.9))

    # Подписи некоторых итераций (каждые 50-100 итераций)
    n_iters = len(history)
    step_labels = max(1, n_iters // 10)
    for i in range(0, n_iters, step_labels):
        if i > 0 and i < n_iters - 1:
            ax1.annotate(f'$x^{i}$', xy=history[i], xytext=(5, 5),
                        textcoords='offset points', fontsize=8, alpha=0.7)

    ax1.set_xlim(-3, 4*n+20)
    ax1.set_ylim(-3, 3*n+20)
    ax1.set_xlabel('$x_1$', fontsize=12)
    ax1.set_ylabel('$x_2$', fontsize=12)
    ax1.grid(True, alpha=0.25, linestyle=':')
    ax1.legend(loc='upper left', fontsize=10, framealpha=0.95)

    # ========== Правый график: сходимость ρ(x^k) ==========
    ax2 = axes[1]
    ax2.set_title('Сходимость функции $\\rho(x^k)$', fontsize=13, fontweight='bold')

    iterations = np.arange(len(rho_history))
    ax2.semilogy(iterations, rho_history, 'b-', linewidth=2, label='$\\rho(x^k)$')
    ax2.plot(iterations, rho_history, 'bo', markersize=4, alpha=0.5)

    # Горизонтальная линия на конечном значении
    ax2.axhline(y=rho_history[-1], color='r', linestyle='--', linewidth=1.5,
                label=f'$\\rho(x^*) \\approx {rho_history[-1]:.2f}$')

    # Отметка места остановки
    ax2.axvline(x=len(rho_history)-1, color='g', linestyle=':', linewidth=1.5,
                alpha=0.7, label=f'остановка на итерации {len(rho_history)-1}')

    ax2.set_xlabel('итерация $k$', fontsize=12)
    ax2.set_ylabel('$\\rho(x^k)$ (логарифмическая шкала)', fontsize=12)
    ax2.grid(True, alpha=0.3, linestyle=':', which='both')
    ax2.legend(loc='upper right', fontsize=10, framealpha=0.95)

    # Информационная панель
    info_text = f'''Результаты:

• n = {n}
• Начальная точка: $x^0 = [{x0[0]:.1f}, {x0[1]:.1f}]$
• Количество итераций: {len(history)-1}
• $x^* \\approx [{x_opt[0]:.4f}, {x_opt[1]:.4f}]$
• $\\rho(x^*) \\approx {rho_history[-1]:.4f}$

Значения критериев:
• $f_1 = x_1^* + x_2^* = {x_opt[0] + x_opt[1]:.4f}$
• $f_2 = -3x_1^* + x_2^* = {-3*x_opt[0] + x_opt[1]:.4f}$
• $f_3 = x_1^* - 3x_2^* = {x_opt[0] - 3*x_opt[1]:.4f}$'''

    ax2.text(0.02, 0.98, info_text, transform=ax2.transAxes,
             fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='gray', alpha=0.95))

    plt.tight_layout()
    plt.savefig('frank_wolfe_trajectory.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.show()

    return fig

def print_detailed_results(history, rho_history, x_opt, x0, n):
    """Вывод подробных результатов"""
    print("\n" + "=" * 70)
    print("ПОДРОБНЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 70)

    print(f"\nИсходные данные:")
    print(f"  n = {n}")
    print(f"  Начальная точка x⁰ = [{x0[0]:.4f}, {x0[1]:.4f}]")
    print(f"  Идеальная точка F* = [{77.0}, {4.4}, {7.3333}]")

    print(f"\nРезультат оптимизации:")
    print(f"  Оптимальная точка x* = [{x_opt[0]:.8f}, {x_opt[1]:.8f}]")
    print(f"  Количество итераций: {len(history)-1}")
    print(f"  Начальное значение ρ(x⁰) = {rho_history[0]:.8f}")
    print(f"  Конечное значение ρ(x*) = {rho_history[-1]:.8f}")
    print(f"  Уменьшение ρ: {rho_history[0] - rho_history[-1]:.8f}")

    # Значения критериев
    f1_opt = x_opt[0] + x_opt[1]
    f2_opt = -3*x_opt[0] + x_opt[1]
    f3_opt = x_opt[0] - 3*x_opt[1]

    print(f"\nЗначения критериев в оптимальной точке:")
    print(f"  f₁ = x₁ + x₂ = {f1_opt:.8f}")
    print(f"  f₂ = -3x₁ + x₂ = {f2_opt:.8f}")
    print(f"  f₃ = x₁ - 3x₂ = {f3_opt:.8f}")

    print(f"\nПроверка ограничений в оптимальной точке:")
    constraints = [
        (x_opt[0] + x_opt[1] >= 2*n, f"x₁ + x₂ ≥ {2*n}: {x_opt[0]+x_opt[1]:.8f} ≥ {2*n}"),
        (x_opt[0] - 2*x_opt[1] <= n, f"x₁ - 2x₂ ≤ {n}: {x_opt[0]-2*x_opt[1]:.8f} ≤ {n}"),
        (-3*x_opt[0] + 2*x_opt[1] <= 2*n, f"-3x₁ + 2x₂ ≤ {2*n}: {-3*x_opt[0]+2*x_opt[1]:.8f} ≤ {2*n}"),
        (0 <= x_opt[0] <= 4*n, f"0 ≤ x₁ ≤ {4*n}: {x_opt[0]:.8f}"),
        (0 <= x_opt[1] <= 3*n, f"0 ≤ x₂ ≤ {3*n}: {x_opt[1]:.8f}")
    ]
    for check, text in constraints:
        print(f"  {'✓' if check else '✗'} {text}")

# ==================== ОСНОВНОЙ БЛОК ====================
if __name__ == "__main__":
    # Запуск алгоритма Франка-Вульфа
    x_opt, history, rho_history, n_iter = frank_wolfe_algorithm(x0, eps=0.01, verbose=True)

    # Вывод подробных результатов
    print_detailed_results(history, rho_history, x_opt, x0, n)

    # Построение графиков
    plot_trajectory(history, rho_history, x0, x_opt, n)

    # Сохранение истории в файл (опционально)
    np.savetxt('history.csv', np.array(history),
               delimiter=',', header='x1,x2', comments='')
    print("\n✓ История итераций сохранена в 'history.csv'")
