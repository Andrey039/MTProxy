# MTProxy Metrics Exporter

HTTP сервер для экспорта метрик MTProxy в формате Prometheus.

## Использование

### Docker

```bash
docker build -t mtproxy-metrics .
docker run -d --network host --name mtproxy-metrics mtproxy-metrics
```

### Standalone

```bash
python3 metrics-exporter.py
```

## Эндпоинты

- `http://localhost:9090/metrics` - метрики в формате Prometheus
- `http://localhost:9090/health` - JSON статус здоровья

## Основные метрики

- `mtproxy_ready_outbound_connections` - готовые соединения к Telegram серверам
- `mtproxy_active_connections` - всего активных соединений
- `mtproxy_inbound_connections` - входящие соединения от клиентов
- `mtproxy_tot_forwarded_queries` - всего переслано запросов
- `mtproxy_healthy` - статус здоровья (1=здоров, 0=нездоров)

## Требования

- Python 3.6+
- MTProxy должен работать на localhost:8888 с включенным `--http-stats`