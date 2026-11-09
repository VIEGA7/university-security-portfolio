# Карта проектов

| Каталог | Основной файл | Что смотреть первым |
|---|---|---|
| `portfolio/access-control-demo` | `Program.cs` | Проверка пользователя, серверные роли, CSRF |
| `portfolio/ias-threat-model` | `README.md`, `assets/`, `poisson_model.py` | Границы системы, угрозы, допущения модели |
| `portfolio/multicriteria-analysis` | `analysis.py` | Численные методы и воспроизводимые результаты |
| `portfolio/opensearch-traffic` | `import_traffic.py` | Типизация, bulk, повторный импорт, обработка ошибок |
| `portfolio/database-security` | `01_schema.sql` … `03_verify.sql` | Минимальные права и реальные операции проверки |
| `portfolio/sql-practice` | `queries.sql` | Формулировки и решения; ограничения указаны в README |
| `portfolio/storage-labs` | Подкаталоги сервисов | Развёртывание, импорт STIX, объектное и графовое хранение |
| `portfolio/linux-http-labs` | `nginx.conf`, `www/tasks.js` | HTTP, Basic Auth, XHR |

`tests/` содержит проверки численных методов, обработки данных и контроля доступа. `.github/workflows/checks.yml` запускает их автоматически на GitHub.

`docs/examples/optimization.json` — сохранённый результат запуска расчётной версии, не результат запуска утраченных оригиналов. Файлы `extracted/` являются историческими листингами; статус проверки отличается от реконструкций.

В публикационную копию не входят университетские DOCX/PDF, исходные скриншоты, временные OCR-файлы и резервные копии. Они остаются в локальном архиве владельца.
