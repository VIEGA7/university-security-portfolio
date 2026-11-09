# Extracted from a university report; see ../README.md.
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from scipy.optimize import linprog

# Параметры задачи
n = 11

# Начальная точка
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
    """Решает задачу min c^T * x при ограничениях"""
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    if res.status != 0:
        raise RuntimeError(f"Ошибка linprog: {res.message}")
    return res.x

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

            # Проверяем, удовлетворяет ли точка всем ограничениям
            if all(np.dot(A_all[k], v) <= b_all[k] + 1e-7 for k in range(m)):
                verts.append(v)

    if not verts:
        return np.empty((0, 2))

    pts = np.array(verts)
    # Сортируем вершины по часовой стрелке
    center = pts.mean(0)
    angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
    return pts[np.argsort(angles)]

print("=" * 60)
print("Метод Франка-Вульфа - Первая итерация (с графиком)")
print(f"n = {n}")
print("=" * 60)

# Вычисление градиента в начальной точке
g0 = grad_rho(x0)
print(f"\n∇ρ(x⁰) = [{g0[0]:.6f}, {g0[1]:.6f}]")

# Решение задачи линейного программирования
s1 = solve_lp(g0)
print(f"s¹ = [{s1[0]:.4f}, {s1[1]:.4f}]")

# Поиск оптимального шага λ
d = s1 - x0
Ad = Acrit @ d
r = Acrit @ x0 - f_star

a = float(Ad @ Ad)
b = float(2.0 * (r @ Ad))

if a <= 0:
    lam = 0 if b >= 0 else 1
else:
    lam = -b / (2 * a)
    lam = max(0.0, min(1.0, lam))

print(f"Оптимальный шаг λ₀ = {lam:.6f}")

# Вычисляем новую точку
x1 = x0 + lam * d
print(f"x¹ = [{x1[0]:.6f}, {x1[1]:.6f}]")
print(f"ρ(x¹) = {rho(x1):.6f}")
print(f"Уменьшение ρ: {rho(x0):.6f} → {rho(x1):.6f}")

# ==================== ПОСТРОЕНИЕ ГРАФИКА ====================

# Создаем фигуру с увеличенным размером для лучшей читаемости
fig, ax = plt.subplots(figsize=(14, 11))
ax.set_title(f'Первая итерация метода Франка-Вульфа (n = {n})',
             fontsize=16, fontweight='bold', pad=20)

# Получаем и отрисовываем допустимую область
poly = get_feasible_polygon()
if len(poly) >= 3:
    patch = MplPolygon(poly, closed=True, facecolor='#d4e8fc',
                        alpha=0.5, edgecolor='black', linewidth=1.5)
    ax.add_patch(patch)

# Отрисовка линий ограничений
x_plt = np.linspace(-5, 4*n+15, 600)

# x1 + x2 >= 22  -> x2 >= 22 - x1
line1 = ax.plot(x_plt, 2*n - x_plt, 'k--', linewidth=1.2, alpha=0.6)

# x1 - 2x2 <= 11 -> x2 >= (x1 - 11)/2
line2 = ax.plot(x_plt, (x_plt - n)/2, 'k--', linewidth=1.2, alpha=0.6)

# -3x1 + 2x2 <= 22 -> x2 <= (22 + 3x1)/2
line3 = ax.plot(x_plt, (2*n + 3*x_plt)/2, 'k--', linewidth=1.2, alpha=0.6)

# x1 <= 44, x2 <= 33
ax.axvline(4*n, color='k', linestyle='--', linewidth=1.2, alpha=0.6)
ax.axhline(3*n, color='k', linestyle='--', linewidth=1.2, alpha=0.6)

# Оси координат
ax.axhline(0, color='black', linewidth=1.2)
ax.axvline(0, color='black', linewidth=1.2)

# Подписи уравнений на графике (сдвинуты подальше от линий)
# Для x1 + x2 = 22
ax.annotate(f'$x_1 + x_2 = {2*n}$', xy=(25, 30), fontsize=9, rotation=-44,
            ha='center', va='bottom', color='black', alpha=0.7,
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.7))

# Для x1 - 2x2 = 11
ax.annotate(f'$x_1 - 2x_2 = {n}$', xy=(50, (50 - n)/2 - 3), fontsize=9, rotation=22,
            ha='center', va='top', color='black', alpha=0.7,
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.7))

# Для -3x1 + 2x2 = 22
ax.annotate(f'$-3x_1 + 2x_2 = {2*n}$', xy=(15, (2*n + 45)/2 + 5), fontsize=9, rotation=48,
            ha='center', va='bottom', color='black', alpha=0.7,
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.7))

# Для x1 = 44
ax.annotate(f'$x_1 = {4*n}$', xy=(4*n - 5, 20), fontsize=9, rotation=90,
            ha='center', va='bottom', color='black', alpha=0.7,
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.7))

# Для x2 = 33
ax.annotate(f'$x_2 = {3*n}$', xy=(25, 3*n + 2), fontsize=9,
            ha='center', va='bottom', color='black', alpha=0.7,
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.7))

# ==================== ТОЧКИ ====================

# Точка x⁰
ax.plot(x0[0], x0[1], 'bo', markersize=12, label='$x^0$', zorder=5)
# Аннотация x⁰ в левую сторону (чтобы не налезала на область)
ax.annotate(f'$x^0 = [{x0[0]:.1f}, {x0[1]:.1f}]$',
            xy=x0, xytext=(-30, 15), textcoords='offset points',
            fontsize=11, color='blue', fontweight='bold',
            ha='right', va='bottom',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='blue', alpha=0.9, linewidth=1.5))

# Точка s¹
ax.plot(s1[0], s1[1], 'ro', markersize=12, label='$s^1$', zorder=5)
# Аннотация s¹ вверх (так как точка внизу)
ax.annotate(f'$s^1 = [{s1[0]:.1f}, {s1[1]:.1f}]$',
            xy=s1, xytext=(10, 20), textcoords='offset points',
            fontsize=11, color='red', fontweight='bold',
            ha='left', va='bottom',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='red', alpha=0.9, linewidth=1.5))

# Точка x¹
ax.plot(x1[0], x1[1], 'go', markersize=12, label='$x^1$', zorder=5)
# Аннотация x¹ вправо-вниз (у неё мало места слева)
ax.annotate(f'$x^1 = [{x1[0]:.2f}, {x1[1]:.2f}]$\n$\\lambda_0 = {lam:.4f}$',
            xy=x1, xytext=(20, -30), textcoords='offset points',
            fontsize=11, color='green', fontweight='bold',
            ha='left', va='top',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='green', alpha=0.9, linewidth=1.5))

# ==================== ВЕКТОРЫ ====================

# Вектор направления d (от x⁰ к s¹) - пунктирный
ax.annotate('', xy=s1, xytext=x0,
            arrowprops=dict(arrowstyle='->', color='gray', lw=2.5,
                          linestyle='dashed', alpha=0.7, shrinkA=5, shrinkB=5))

# Подпись направления d посередине, но со смещением
mid_x = (x0[0] + s1[0]) / 2
mid_y = (x0[1] + s1[1]) / 2
# Смещаем подпись перпендикулярно вектору
dx = s1[0] - x0[0]
dy = s1[1] - x0[1]
perp = np.array([-dy, dx])
perp = perp / np.linalg.norm(perp) * 8
ax.annotate('направление $d$', xy=(mid_x, mid_y), xytext=(mid_x + perp[0], mid_y + perp[1]),
            fontsize=10, color='gray', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='gray', alpha=0.9))

# Вектор градиента ∇ρ в точке x⁰
gn = g0 / np.linalg.norm(g0)  # нормализованный градиент
grad_length = 18  # длина стрелки градиента
grad_end = (x0[0] + gn[0]*grad_length, x0[1] + gn[1]*grad_length)

# Рисуем градиент
ax.annotate('', xy=grad_end, xytext=x0,
            arrowprops=dict(arrowstyle='->', color='purple', lw=3, alpha=0.9, shrinkA=3, shrinkB=3))

# Подпись градиента на конце стрелки со смещением
ax.annotate('$\\nabla\\rho(x^0)$', xy=grad_end, xytext=(5, 5), textcoords='offset points',
            fontsize=12, color='purple', fontweight='bold', ha='left', va='bottom',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='purple', alpha=0.9, linewidth=1.5))

# Линия траектории от x⁰ к x¹ (жирная зеленая линия)
ax.plot([x0[0], x1[0]], [x0[1], x1[1]], 'g-', linewidth=3, alpha=0.8)

# ==================== НАСТРОЙКИ ГРАФИКА ====================

ax.set_xlim(-3, 4*n+18)
ax.set_ylim(-3, 3*n+20)
ax.set_xlabel('$x_1$', fontsize=13, fontweight='bold')
ax.set_ylabel('$x_2$', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.25, linestyle=':', linewidth=0.8)

# Легенда в правом верхнем углу
ax.legend(loc='upper right', fontsize=11, framealpha=0.95, fancybox=True, shadow=True)

# Текстовая информация на графике - в нижний левый угол (там свободно)
info_text = f'''Параметры первой итерации:

• $x^0 = [{x0[0]:.1f}, {x0[1]:.1f}]$
• $s^1 = [{s1[0]:.1f}, {s1[1]:.1f}]$
• $\\lambda_0 = {lam:.4f}$
• $x^1 = [{x1[0]:.2f}, {x1[1]:.2f}]$
• $\\rho(x^0) = {rho(x0):.2f}$
• $\\rho(x^1) = {rho(x1):.2f}$'''

ax.text(0.02, 0.02, info_text, transform=ax.transAxes,
        fontsize=10, verticalalignment='bottom',
        bbox=dict(boxstyle='round,pad=0.6', fc='white', ec='gray', alpha=0.95, linewidth=1))

# Добавляем небольшую стрелку на оси для наглядности
ax.annotate('', xy=(4*n+10, 0), xytext=(4*n+5, 0),
            arrowprops=dict(arrowstyle='->', color='black', lw=1))
ax.annotate('', xy=(0, 3*n+15), xytext=(0, 3*n+10),
            arrowprops=dict(arrowstyle='->', color='black', lw=1))

plt.tight_layout()
plt.savefig('frank_wolfe_iteration_1.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.show()

print("\n✓ График сохранён как 'frank_wolfe_iteration_1.png'")
print("✓ Все элементы расположены без перекрытий:")
print("  - x⁰ аннотация слева от точки")
print("  - s¹ аннотация сверху от точки")
print("  - x¹ аннотация справа снизу")
print("  - Информационная панель в левом нижнем углу")
print("  - Легенда в правом верхнем углу")
print("  - Подписи уравнений на белых подложках")
