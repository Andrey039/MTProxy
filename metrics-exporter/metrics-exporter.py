#!/usr/bin/env python3
"""
MTProxy Metrics Exporter
Простой HTTP сервер для экспорта метрик MTProxy в формате Prometheus
"""

import json
import re
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen
from urllib.error import URLError


class MetricsHandler(BaseHTTPRequestHandler):
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
            response = self.format_prometheus_metrics(metrics)
            
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

    def format_prometheus_metrics(self, metrics):
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