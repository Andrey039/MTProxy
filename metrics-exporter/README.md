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

- `http://localhost:9090/` - веб-дашборд
- `http://localhost:9090/metrics` - метрики в формате Prometheus
- `http://localhost:9090/health` - проверка готовности (200/503)
- `http://localhost:9090/status` - статус прокси (JSON для дашборда)

## Основные метрики

- `mtproxy_ready_outbound_connections` - готовые соединения к Telegram серверам
- `mtproxy_active_connections` - всего активных соединений
- `mtproxy_inbound_connections` - входящие соединения от клиентов
- `mtproxy_tot_forwarded_queries` - всего переслано запросов
- `mtproxy_healthy` - статус здоровья (1=здоров, 0=нездоров)

## Веб-дашборд

Простой веб-интерфейс с таблицами:
- 📊 Статус прокси и время работы
- 🔗 Количество подключений
- 📈 Объемы и скорость трафика
- 📋 Статистика запросов/ответов
- 🔄 Автообновление каждые 5 секунд

## Пример ответа /status

```json
{
  "status": "🟢 Отлично",
  "uptime": "2 ч 15 мин",
  "connections": {
    "clients": 3,
    "telegram_servers": 16,
    "total_active": 67
  },
  "traffic": {
    "total": {
      "received": "1.2 GB",
      "sent": "890.5 MB",
      "total": "2.1 GB"
    },
    "current_speed": {
      "download": "125.3 KB/s",
      "upload": "89.7 KB/s",
      "total": "215.0 KB/s"
    }
  },
  "requests": {
    "total": {
      "queries": 1547,
      "responses": 1623
    },
    "per_second": {
      "queries": "2.3",
      "responses": "2.1"
    }
  }
}
```

## Требования

- Python 3.6+
- MTProxy должен работать на localhost:8888 с включенным `--http-stats`