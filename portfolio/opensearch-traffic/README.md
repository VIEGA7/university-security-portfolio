# Анализ трафика: PCAP → CSV → OpenSearch

В этом проекте я публикую восстановленную версию своей практики №5 по дисциплине «Технологии хранения в системах кибербезопасности». Для восстановления и доработки импортера я использовал помощь ИИ. Сохранились текст Python-импортера и скриншоты конфигурации. Новая версия использует стандартную библиотеку Python вместо pandas/opensearch-py.

При подготовке этой версии я уделил внимание корректности импорта: типы полей задаются явно; пустая дата не заменяется текущим временем; повторные IP обрабатываются как массив; нет NaN в JSON; загрузка идёт пакетами по 500 записей; проверяются ошибки отдельных bulk-операций. Идентификатор зависит от файла и номера записи: повторный импорт того же CSV не создаёт дубликаты, а одинаковые пакеты на разных строках сохраняются.

## Пример без Docker

Из корня репозитория:

```powershell
python portfolio/opensearch-traffic/import_traffic.py portfolio/opensearch-traffic/sample.csv --dry-run portfolio/opensearch-traffic/output/sample.ndjson
```

Для воспроизводимого примера я добавил в `sample.csv` три **синтетических**, а не захваченных пакета. Преобразование проверено. Файла с исходным трафиком нет.

## Локальный кластер

Нужны Docker Compose и достаточно памяти. Настройки хоста, включая `vm.max_map_count`, описаны в [документации OpenSearch](https://docs.opensearch.org/2.19/install-and-configure/install-opensearch/docker/).

```powershell
docker compose -f portfolio/opensearch-traffic/compose.yaml up -d
python portfolio/opensearch-traffic/import_traffic.py portfolio/opensearch-traffic/sample.csv
```

OpenSearch: `http://127.0.0.1:9210`; Dashboards: `http://127.0.0.1:5610`. В Dashboards создать index pattern `packets-mbm-*`, выбрать `frame.time_epoch` как поле времени. Запросы — в `queries.http`; для примера нужно выбрать диапазон времени, включающий timestamp из CSV.

Security plugin отключён для локальной учебной конфигурации, порты привязаны к loopback. Конфигурация не предназначена для публичного размещения. Версии образов отличаются от исторического `latest` и согласованы между сервисами. [Формат bulk и проверка ошибок](https://docs.opensearch.org/2.19/api-reference/document-apis/bulk/).

## Собственный PCAP

При установленном TShark:

```powershell
python portfolio/opensearch-traffic/extract_pcap.py capture.pcap traffic.csv
python portfolio/opensearch-traffic/import_traffic.py traffic.csv
```

Фильтр сохраняет IPv4-пакеты с TCP, UDP или ICMP; это не полный анализ IPv6. Сбор полей и JSON-конвертация восстановлены; сам TShark и кластер здесь не запускались. Готовых экспортов пяти исторических дашбордов нет. Пять направлений анализа из отчёта: общий трафик, HTTP, сетевые аномалии, DNS и TLS; их наличие в отчёте не заменяет сохранённых конфигураций визуализаций.
