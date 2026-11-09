# Extracted from a university report; see ../README.md.
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import linprog

# ============================================
# Вариант n = 11
# Главный критерий: f2 = -3*x1 + x2 (максимизируем)
# Пороги: γ1 = 55, γ3 = -66
# ============================================

n = 11

# Параметры задачи
gamma1 = 5 * n      # = 55 (порог для f1)
gamma3 = -6 * n     # = -66 (порог для f3)

print("=" * 60)
print(f"РЕШЕНИЕ ЗАДАЧИ МЕТОДОМ ГЛАВНОГО КРИТЕРИЯ (n = {n})")
print("=" * 60)
print(f"Главный критерий: f2(x) = -3*x1 + x2 → max")
print(f"Порог по f1: γ1 = {gamma1}  (x1 + x2 ≥ {gamma1})")
print(f"Порог по f3: γ3 = {gamma3}  (x1 - 3*x2 ≥ {gamma3})")
print("=" * 60)

# ============================================
# 1. Решение задачи линейного программирования
# ============================================
# Максимизируем f2 = -3*x1 + x2
# Приводим к виду минимизации: -f2 = 3*x1 - x2 → min
c = [3, -1]  # коэффициенты для linprog (минимизация)

# Ограничения в виде A_ub @ x <= b_ub
# Все неравенства приводим к виду <=
A_ub = []
b_ub = []

# Исходные ограничения:
# 1) x1 + x2 >= 22  →  -x1 - x2 <= -22
A_ub.append([-1, -1])
b_ub.append(-22)

# 2) x1 - 2*x2 <= 11
A_ub.append([1, -2])
b_ub.append(11)

# 3) -3*x1 + 2*x2 <= 22
A_ub.append([-3, 2])
b_ub.append(22)

# 4) x1 <= 44
A_ub.append([1, 0])
b_ub.append(44)

# 5) x2 <= 33
A_ub.append([0, 1])
b_ub.append(33)

# Пороговые ограничения:
# 6) x1 + x2 >= 55  →  -x1 - x2 <= -55
A_ub.append([-1, -1])
b_ub.append(-55)

# 7) x1 - 3*x2 >= -66  →  -x1 + 3*x2 <= 66
A_ub.append([-1, 3])
b_ub.append(66)

# Границы переменных: x1 >= 0, x2 >= 0
bounds = [(0, None), (0, None)]

# Решаем задачу
result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

# ============================================
# 2. Вывод результатов
# ============================================
print("\n" + "-" * 60)
print("РЕЗУЛЬТАТЫ РЕШЕНИЯ")
print("-" * 60)

if result.success:
    x1_opt, x2_opt = result.x

    # Вычисляем значения критериев
    f1_opt = x1_opt + x2_opt
    f2_opt = -3*x1_opt + x2_opt
    f3_opt = x1_opt - 3*x2_opt

    print(f"Оптимальное решение:")
    print(f"  x1* = {x1_opt:.4f}")
    print(f"  x2* = {x2_opt:.4f}")
    print(f"\nЗначения критериев в оптимальной точке:")
    print(f"  f1 = x1 + x2 = {f1_opt:.4f}  (порог ≥ {gamma1})")
    print(f"  f2 = -3*x1 + x2 = {f2_opt:.4f}  (главный критерий, максимум)")
    print(f"  f3 = x1 - 3*x2 = {f3_opt:.4f}  (порог ≥ {gamma3})")
    print(f"\nПроверка порогов:")
    print(f"  f1 ≥ {gamma1}: {f1_opt:.4f} ≥ {gamma1} → {f1_opt >= gamma1}")
    print(f"  f3 ≥ {gamma3}: {f3_opt:.4f} ≥ {gamma3} → {f3_opt >= gamma3}")
else:
    print("Решение не найдено!")
    print(f"Причина: {result.message}")

# ============================================
# 3. Визуализация
# ============================================
plt.figure(figsize=(14, 10))

# Настройка сетки
x1_max = 50
x2_max = 40
x1 = np.linspace(0, x1_max, 500)
x2 = np.linspace(0, x2_max, 500)
X1, X2 = np.meshgrid(x1, x2)

# ====== Отрисовка линий ограничений ======
line_style = {'color': 'blue', 'linestyle': '-', 'linewidth': 1.5}

# Исходные ограничения
plt.plot(x1, 22 - x1, **line_style, label='$x_1 + x_2 \\geq 22$')
plt.plot(x1, (x1 - 11)/2, **line_style, label='$x_1 - 2x_2 \\leq 11$')
plt.plot(x1, (3*x1 + 22)/2, **line_style, label='$-3x_1 + 2x_2 \\leq 22$')
plt.axvline(44, **line_style, label='$x_1 \\leq 44$')
plt.axhline(33, **line_style, label='$x_2 \\leq 33$')

# Пороговые ограничения
plt.plot(x1, 55 - x1, 'green', linestyle='--', linewidth=2,
         label=f'$x_1 + x_2 \\geq {gamma1}$ (порог f₁)')
plt.plot(x1, (x1 + 66)/3, 'orange', linestyle='--', linewidth=2,
         label=f'$x_1 - 3x_2 \\geq {gamma3}$ (порог f₃)')

# ====== Заливка допустимой области ======
# Исходная область D
cond_D = (
    (X1 + X2 >= 22) &
    (X1 - 2*X2 <= 11) &
    (-3*X1 + 2*X2 <= 22) &
    (X1 <= 44) &
    (X2 <= 33)
)

# Итоговая область D' (с учётом порогов)
cond_Dprime = cond_D & (X1 + X2 >= gamma1) & (X1 - 3*X2 >= gamma3)

plt.imshow(cond_Dprime.astype(int), extent=(0, x1_max, 0, x2_max),
           origin='lower', cmap='Greens', alpha=0.3, aspect='auto')

# ====== Линия уровня целевой функции ======
if result.success:
    f2_opt = -3*x1_opt + x2_opt
    # Целевая функция f2 = -3*x1 + x2 = const → x2 = f2_opt + 3*x1
    plt.plot(x1, f2_opt + 3*x1, 'red', linestyle=':', linewidth=2,
             label=f'Целевая $f_2$ (max = {f2_opt:.2f})')

    # Оптимальная точка
    plt.scatter(x1_opt, x2_opt, color='red', s=150, zorder=5,
                edgecolor='black', linewidth=2,
                label=f'Оптимум ({x1_opt:.2f}, {x2_opt:.2f})')

# ====== Оформление ======
plt.xlim(0, x1_max)
plt.ylim(0, x2_max)
plt.xlabel('$x_1$', fontsize=12)
plt.ylabel('$x_2$', fontsize=12)
plt.title(f'Метод главного критерия (n = {n}, главный $f_2$)', fontsize=14)
plt.grid(True, linestyle=':', alpha=0.5)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
plt.tight_layout()
plt.show()

# ============================================
# 4. Дополнительная информация
# ============================================
print("\n" + "=" * 60)
print("ОПИСАНИЕ МЕТОДА ГЛАВНОГО КРИТЕРИЯ")
print("=" * 60)
print("""
Метод главного критерия (пороговой оптимизации):
1. Из множества критериев выделяется один главный (наиболее важный)
2. На остальные критерии накладываются пороговые ограничения
3. Исходная многокритериальная задача сводится к однокритериальной

В данной задаче:
- Главный критерий: f2(x) = -3*x1 + x2
- Порог по f1: f1(x) ≥ 55
- Порог по f3: f3(x) ≥ -66

Полученное решение является оптимальным в рамках
заданных ограничений и порогов.
""")
