FROM node:22-bookworm-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
WORKDIR /app
COPY --from=frontend /usr/local/bin/node /usr/local/bin/node
COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir .
COPY cases/ cases/
COPY sources/ sources/
COPY benchmarks/ benchmarks/
COPY evaluation/ evaluation/
COPY engineering_cases/ engineering_cases/
COPY frontend/sam-mask-metrics.mjs frontend/sam-mask-metrics.mjs
COPY --from=frontend /app/frontend/node_modules/ frontend/node_modules/
COPY --from=frontend /app/frontend/dist/ frontend/dist/
CMD ["python", "-m", "mre_engineer", "serve"]
