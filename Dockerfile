FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY bridge ./bridge
RUN pip install --no-cache-dir '.[mqtt]'
EXPOSE 8000
CMD ["uvicorn", "bridge.api:app", "--host", "0.0.0.0", "--port", "8000"]
