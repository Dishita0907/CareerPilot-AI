FROM node:22-alpine AS ui
WORKDIR /src
COPY web/package*.json web/
RUN cd web && npm ci
COPY web web
COPY data data
RUN cd web && npm run build
FROM python:3.12-slim
WORKDIR /srv
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app app
COPY data data
COPY --from=ui /src/web/dist web/dist
ENV OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
