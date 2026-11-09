# Extracted from a university report; see ../README.md.
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

# Конфигурация параметров
param_n = 11

# Определение граничных значений
bound_low, bound_high = param_n / 2, 3 * param_n
bound_f2_low, bound_f2_high = param_n / 2, 2 * param_n

# Проверка принадлежности области
def check_point_inside(val1, val2):
    expr1 = ((val1 - param_n) ** 2) / (4 * param_n ** 2)
    expr2 = ((val2 - param_n) ** 2) / (param_n ** 2)
    return (expr1 + expr2) <= 1

# Генерация набора точек
total_points_needed = 200
coordinates = []
flags = []

while len(coordinates) < total_points_needed:
    x_coord = np.random.uniform(bound_low, bound_high)
    y_coord = np.random.uniform(bound_f2_low, bound_f2_high)
    if check_point_inside(x_coord, y_coord):
        coordinates.append((x_coord, y_coord))
        flags.append(0)

coordinates = np.array(coordinates)
flags = np.array(flags, dtype=object)

# Формирование таблицы данных
data_table = pd.DataFrame({
    "ID": np.arange(1, len(coordinates) + 1),
    "X_val": coordinates[:, 0],
    "Y_val": coordinates[:, 1]
})

# Алгоритм удаления доминируемых точек
idx = 0
iteration = 1

while idx < len(coordinates):
    col_name = f"iter_{iteration}"

    if col_name not in data_table:
        data_table[col_name] = ""

    if flags[idx] == "-":
        data_table.at[idx, col_name] = "-"
        idx += 1
        continue

    flags[idx] = "+"
    data_table.at[idx, col_name] = "+"

    current_x, current_y = coordinates[idx]

    for jdx in range(len(coordinates)):
        if idx == jdx or flags[jdx] == "-":
            continue

        x_val, y_val = coordinates[jdx]

        if x_val <= current_x and y_val <= current_y and (x_val < current_x or y_val < current_y):
            flags[jdx] = "-"
            data_table.at[jdx, col_name] = "-"

    idx += 1
    iteration += 1

# Выделение Парето-оптимального множества
pareto_set = set()
for pos in range(len(coordinates)):
    status_row = data_table.iloc[pos, 3:].values
    last_plus_position = None

    for step_idx, status_val in enumerate(status_row):
        if status_val == "+":
            last_plus_position = step_idx

    if last_plus_position is not None and all(s != "-" for s in status_row[last_plus_position + 1:]):
        pareto_set.add(pos)

# Сохранение результатов в Excel
output_file = "output_results.xlsx"

if os.path.exists(output_file):
    os.remove(output_file)

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    data_table.to_excel(writer, index=False, sheet_name="Dominance_Analysis")

workbook = load_workbook(output_file)
worksheet = workbook["Dominance_Analysis"]

green_color_fill = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")

for position in pareto_set:
    for cell in worksheet[position + 2]:
        cell.fill = green_color_fill

# Расчет индексов эффективности
def compute_efficiency_index(data_points):
    count_points = len(data_points)
    efficiency_values = []

    for i, (x_i, y_i) in enumerate(data_points):
        dominated_counter = 0
        for j, (x_j, y_j) in enumerate(data_points):
            if x_j >= x_i and y_j >= y_i and (x_j > x_i or y_j > y_i):
                dominated_counter += 1
        efficiency = 1 / (1 + (dominated_counter / (count_points - 1)))
        efficiency_values.append(efficiency)

    return np.array(efficiency_values)

efficiency_scores = compute_efficiency_index(coordinates)

# Кластеризация по индексам
cluster_assignments = np.zeros(len(coordinates), dtype=int)
center_k1, center_k2, center_k3 = 1.0, 0.85, 0.75

for pos, score in enumerate(efficiency_scores):
    dist_to_k1 = abs(score - center_k1)
    dist_to_k2 = abs(score - center_k2)
    dist_to_k3 = abs(score - center_k3)

    if dist_to_k1 < dist_to_k2 and dist_to_k1 < dist_to_k3:
        cluster_assignments[pos] = 1
    elif dist_to_k2 < dist_to_k1 and dist_to_k2 < dist_to_k3:
        cluster_assignments[pos] = 2
    else:
        cluster_assignments[pos] = 3

# Создание таблицы с индексами эффективности и кластерами

# Создаем DataFrame для отображения в консоли
results_table = pd.DataFrame({
    "Номер точки": np.arange(1, len(coordinates) + 1),
    "f1": coordinates[:, 0],
    "f2": coordinates[:, 1],
    "F": efficiency_scores,
    "Кластер": [f"K{i}" for i in cluster_assignments]
})

# Округляем значения для удобного отображения
results_table["f1"] = results_table["f1"].round(6)
results_table["f2"] = results_table["f2"].round(6)
results_table["F"] = results_table["F"].round(6)

# Сортируем по номеру точки
results_table_sorted = results_table.sort_values("Номер точки")

# Выводим таблицу в консоль
print("\n" + "=" * 80)
print("ТАБЛИЦА РЕЗУЛЬТАТОВ: Индексы эффективности и кластеры")
print("=" * 80)
print(results_table_sorted.to_string(index=False))
print("=" * 80)

# Сохраняем эту таблицу в отдельный лист Excel
cluster_sheet = workbook.create_sheet("Efficiency_Clusters")
cluster_sheet.append(["Номер точки", "f1", "f2", "F", "Кластер"])

# Цвета для кластеров
cluster_colors = {1: "00FF00", 2: "FFFF00", 3: "FF0000"}
cluster_names_map = {1: "K1", 2: "K2", 3: "K3"}

for pos in range(len(coordinates)):
    cluster_name = cluster_names_map[cluster_assignments[pos]]
    cluster_sheet.append([pos + 1, coordinates[pos, 0], coordinates[pos, 1], efficiency_scores[pos], cluster_name])

    # Закрашиваем строку цветом кластера
    color_fill = PatternFill(start_color=cluster_colors[cluster_assignments[pos]],
                              end_color=cluster_colors[cluster_assignments[pos]],
                              fill_type="solid")
    for cell in cluster_sheet[pos + 2]:
        cell.fill = color_fill

# Дополнительная таблица: Парето-оптимальные точки с кластерами
pareto_table = results_table[results_table["Номер точки"].isin([p + 1 for p in pareto_set])]
pareto_table = pareto_table.sort_values("F", ascending=False)

print("\n" + "=" * 80)
print("ТАБЛИЦА ПАРЕТО-ОПТИМАЛЬНЫХ ПРОЕКТОВ (с кластерами)")
print("=" * 80)
print(pareto_table.to_string(index=False))
print("=" * 80)

# Сохраняем Парето-таблицу в отдельный лист Excel
pareto_sheet = workbook.create_sheet("Pareto_Optimal")
pareto_sheet.append(["Номер точки", "f1", "f2", "F", "Кластер"])

for _, row in pareto_table.iterrows():
    pareto_sheet.append([int(row["Номер точки"]), row["f1"], row["f2"], row["F"], row["Кластер"]])

# Закрашиваем Парето-оптимальные точки зеленым
green_fill_pareto = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")
for row_idx in range(2, len(pareto_table) + 2):
    for cell in pareto_sheet[row_idx]:
        cell.fill = green_fill_pareto

workbook.save(output_file)

# Построение графиков

# График 1: Исходное распределение точек
plt.figure(figsize=(8, 6))
non_optimal = coordinates[flags == "-"]
plt.scatter(non_optimal[:, 0], non_optimal[:, 1], color="gray", alpha=0.6)
candidates = coordinates[flags == "+"]
plt.scatter(candidates[:, 0], candidates[:, 1], color="gray", alpha=0.8, label="Все проекты")
plt.xlabel("Показатель f₁")
plt.ylabel("Показатель f₂")
plt.title("Исходное множество проектов")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# График 2: Парето-оптимальные проекты
plt.figure(figsize=(8, 6))
dominated_set = coordinates[flags == "-"]
plt.scatter(dominated_set[:, 0], dominated_set[:, 1], color="red", alpha=0.5, label="Доминируемые проекты")
pareto_set_points = coordinates[flags == "+"]
plt.scatter(pareto_set_points[:, 0], pareto_set_points[:, 1],
            color="green", edgecolor="black", s=80, label="Парето-оптимальные")
plt.xlabel("Показатель f₁")
plt.ylabel("Показатель f₂")
plt.title("Выделение Парето-фронта")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# График 3: Результаты кластеризации
plt.figure(figsize=(8, 6))
visual_colors = {1: "green", 2: "gold", 3: "crimson"}
cluster_names = {1: "Кластер 1 (F ≈ 1.0)", 2: "Кластер 2 (F ≈ 0.85)", 3: "Кластер 3 (F ≈ 0.75)"}

for cluster_id in [1, 2, 3]:
    cluster_data = coordinates[cluster_assignments == cluster_id]
    plt.scatter(cluster_data[:, 0], cluster_data[:, 1],
                color=visual_colors[cluster_id],
                label=cluster_names[cluster_id],
                edgecolor="black", alpha=0.7)

plt.xlabel("Показатель f₁")
plt.ylabel("Показатель f₂")
plt.title("Кластеризация проектов по индексу эффективности")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# Вывод статистики
print("\n" + "=" * 80)
print("ИТОГОВАЯ СТАТИСТИКА")
print("=" * 80)
print(f"Всего проектов: {len(coordinates)}")
print(f"Парето-оптимальных проектов: {len(pareto_set)} ({len(pareto_set)/len(coordinates)*100:.1f}%)")
print(f"\nРаспределение по кластерам:")
print(f"  Кластер K1 (F ≈ 1.0):  {np.sum(cluster_assignments == 1)} проектов ({np.sum(cluster_assignments == 1)/len(coordinates)*100:.1f}%)")
print(f"  Кластер K2 (F ≈ 0.85): {np.sum(cluster_assignments == 2)} проектов ({np.sum(cluster_assignments == 2)/len(coordinates)*100:.1f}%)")
print(f"  Кластер K3 (F ≈ 0.75): {np.sum(cluster_assignments == 3)} проектов ({np.sum(cluster_assignments == 3)/len(coordinates)*100:.1f}%)")
print(f"\nРезультаты сохранены в файл: {output_file}")
print("=" * 80)

# Вывод первых 20 строк таблицы
print("\n" + "=" * 80)
print("ПЕРВЫЕ 20 ПРОЕКТОВ (с кластерами)")
print("=" * 80)
print(results_table_sorted.head(20).to_string(index=False))
