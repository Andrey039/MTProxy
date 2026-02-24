FROM python:3.11-slim

WORKDIR /app

COPY metrics-exporter.py /app/

EXPOSE 9090

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:9090/health || exit 1

CMD ["python3", "metrics-exporter.py"]