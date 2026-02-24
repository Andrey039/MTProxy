#!/usr/bin/env python3
"""
MTProxy Metrics Exporter
Простой HTTP сервер для экспорта метрик MTProxy в формате Prometheus
"""

import json
import re
import time
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen
from urllib.error import URLError


class MetricsHandler(BaseHTTPRequestHandler):
    # Хранение истории для расчета rate
    _history = deque(maxlen=60)  # 60 записей = 5 минут при интервале 5 сек
    _last_metrics = {}
    
    @classmethod
    def update_history(cls, metrics):
        """Обновляет историю метрик для расчета rate"""
        current_time = time.time()
        cls._history.append({
            'timestamp': current_time,
            'tot_forwarded_queries': metrics.get('tot_forwarded_queries', 0),
            'tot_forwarded_responses': metrics.get('tot_forwarded_responses', 0),
            'tcp_readv_bytes': metrics.get('tcp_readv_bytes', 0),
            'tcp_writev_bytes': metrics.get('tcp_writev_bytes', 0)
        })
        cls._last_metrics = metrics
    
    @classmethod
    def calculate_rates(cls):
        """Вычисляет rate метрики"""
        if len(cls._history) < 2:
            return {'queries_per_sec': 0, 'responses_per_sec': 0}
        
        # Берем данные за последние 5 минут или все доступные
        recent = list(cls._history)[-12:]  # последние 12 записей = 1 минута
        if len(recent) < 2:
            recent = list(cls._history)
        
        first = recent[0]
        last = recent[-1]
        
        time_diff = last['timestamp'] - first['timestamp']
        if time_diff <= 0:
            return {'queries_per_sec': 0, 'responses_per_sec': 0}
        
        queries_diff = last['tot_forwarded_queries'] - first['tot_forwarded_queries']
        responses_diff = last['tot_forwarded_responses'] - first['tot_forwarded_responses']
        read_bytes_diff = last['tcp_readv_bytes'] - first['tcp_readv_bytes']
        write_bytes_diff = last['tcp_writev_bytes'] - first['tcp_writev_bytes']
        
        return {
            'queries_per_sec': queries_diff / time_diff,
            'responses_per_sec': responses_diff / time_diff,
            'bytes_read_per_sec': read_bytes_diff / time_diff,
            'bytes_write_per_sec': write_bytes_diff / time_diff
        }
    def do_GET(self):
        if self.path == '/metrics':
            self.send_metrics()
        elif self.path == '/health':
            self.send_health()
        else:
            self.send_response(404)
            self.end_headers()

    def send_metrics(self):
        try:
            metrics = self.get_mtproxy_metrics()
            self.update_history(metrics)
            rates = self.calculate_rates()
            response = self.format_prometheus_metrics(metrics, rates)
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode('utf-8'))

    def send_health(self):
        try:
            metrics = self.get_mtproxy_metrics()
            status = "healthy" if metrics.get('ready_outbound_connections', 0) > 0 else "unhealthy"
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {"status": status, "ready_connections": metrics.get('ready_outbound_connections', 0)}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode('utf-8'))

    def get_mtproxy_metrics(self):
        """Получает метрики от MTProxy"""
        try:
            with urlopen('http://localhost:8888/stats', timeout=5) as response:
                data = response.read().decode('utf-8')
            
            metrics = {}
            for line in data.split('\n'):
                if '\t' in line:
                    key, value = line.split('\t', 1)
                    try:
                        metrics[key] = float(value)
                    except ValueError:
                        metrics[key] = value
            
            return metrics
        except URLError as e:
            raise Exception(f"Failed to connect to MTProxy stats: {e}")

    def format_prometheus_metrics(self, metrics, rates):
        """Форматирует метрики в формате Prometheus"""
        output = []
        
        # Основные метрики
        important_metrics = {
            'ready_outbound_connections': 'MTProxy ready outbound connections to Telegram servers',
            'active_connections': 'Total active connections',
            'inbound_connections': 'Active inbound client connections',
            'outbound_connections': 'Active outbound connections to Telegram',
            'tot_forwarded_queries': 'Total forwarded queries from clients',
            'tot_forwarded_responses': 'Total forwarded responses from Telegram',
            'tcp_readv_bytes': 'Total bytes read from TCP sockets',
            'tcp_writev_bytes': 'Total bytes written to TCP sockets',
            'uptime': 'MTProxy uptime in seconds',
            'qps_get': 'Queries per second',
            'http_qps': 'HTTP queries per second',
            'ready_targets': 'Ready Telegram server targets',
            'active_targets': 'Active Telegram server targets',
            'total_encrypted_connections': 'Total encrypted connections'
        }
        
        timestamp = int(time.time() * 1000)
        
        for metric_name, description in important_metrics.items():
            value = metrics.get(metric_name, 0)
            if isinstance(value, (int, float)):
                output.append(f'# HELP mtproxy_{metric_name} {description}')
                output.append(f'# TYPE mtproxy_{metric_name} gauge')
                output.append(f'mtproxy_{metric_name} {value} {timestamp}')
                output.append('')
        
        # Rate метрики (трафик в секунду)
        output.append('# HELP mtproxy_queries_per_second Rate of forwarded queries per second')
        output.append('# TYPE mtproxy_queries_per_second gauge')
        output.append(f'mtproxy_queries_per_second {rates["queries_per_sec"]:.2f} {timestamp}')
        output.append('')
        
        output.append('# HELP mtproxy_responses_per_second Rate of forwarded responses per second')
        output.append('# TYPE mtproxy_responses_per_second gauge')
        output.append(f'mtproxy_responses_per_second {rates["responses_per_sec"]:.2f} {timestamp}')
        output.append('')
        
        # Трафик в байтах в секунду
        output.append('# HELP mtproxy_bytes_read_per_second Bytes read per second from TCP sockets')
        output.append('# TYPE mtproxy_bytes_read_per_second gauge')
        output.append(f'mtproxy_bytes_read_per_second {rates["bytes_read_per_sec"]:.2f} {timestamp}')
        output.append('')
        
        output.append('# HELP mtproxy_bytes_write_per_second Bytes written per second to TCP sockets')
        output.append('# TYPE mtproxy_bytes_write_per_second gauge')
        output.append(f'mtproxy_bytes_write_per_second {rates["bytes_write_per_sec"]:.2f} {timestamp}')
        output.append('')
        
        # Статус здоровья (1 = healthy, 0 = unhealthy)
        health_status = 1 if metrics.get('ready_outbound_connections', 0) > 0 else 0
        output.append('# HELP mtproxy_healthy MTProxy health status (1=healthy, 0=unhealthy)')
        output.append('# TYPE mtproxy_healthy gauge')
        output.append(f'mtproxy_healthy {health_status} {timestamp}')
        
        return '\n'.join(output)

    def log_message(self, format, *args):
        """Отключаем логи запросов"""
        pass


def main():
    port = 9090
    server = HTTPServer(('0.0.0.0', port), MetricsHandler)
    print(f"MTProxy Metrics Exporter started on port {port}")
    print(f"Metrics: http://localhost:{port}/metrics")
    print(f"Health: http://localhost:{port}/health")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()