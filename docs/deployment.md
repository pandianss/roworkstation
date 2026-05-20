# Deployment Guide

RO Workstation is built for offline-first operation, making it ideal for restricted internal networks commonly found in banking environments.

## Docker Deployment (Recommended)

The easiest way to deploy the application is using Docker and Docker Compose.

### Running with Docker Compose
1. **Build and start the container**:
   ```bash
   docker compose up --build -d
   ```
2. **Access the application**: Open your browser and navigate to `http://localhost:8501`.

The `docker-compose.yml` file includes a health check to ensure the Streamlit service is running correctly.

## Offline Preparation

If the target environment has no internet access, you must prepare the assets on a machine with internet access first.

### 1. Download Dependencies
```bash
pip download -r requirements.txt -d ./wheels/
```

### 2. Pull AI Models
```bash
# Pull the LLM (if using Ollama)
ollama pull mistral
```

The current knowledge services include an offline fallback embedder. If you later add `sentence-transformers`, store local embedding models under `data/models/` and map that directory through the existing `./data:/app/data` Docker volume.

### 3. Package Docker Images
```bash
docker compose build
docker save ro-workstation-app ollama/ollama | gzip > ro-workstation.tar.gz
```

### 4. Transfer and Load
Copy the `.tar.gz` file and the repository folder to the internal network machine.
```bash
docker load < ro-workstation.tar.gz
docker compose up -d
```

## Persistence and Backups

- **Database**: The main application data is stored in a SQLite database (`data/app.db`) or shared JSON/CSV files in the `data/` or `files/` directory.
- **Volumes**: The compose file maps `./data:/app/data` and `./backups:/app/backups`.
- **Backups**: The `backups/` directory contains automated or manual snapshots of the data. Regular backups should be performed by copying this directory to a secure location.

## Environment Configuration

Configuration is managed via the `.env` file. Key variables include:
- `RO_ENVIRONMENT`: `production` or `development`.
- `RO_ADMIN_PASSWORD`: administrative unlock password.
- `RO_PUBLIC_URL`: canonical public URL for SEO metadata, if deployed behind a stable URL.
- `RO_OFFLINE_MODE`: `true` or `false`.
- `RO_REGION_CODE`: region aggregate SOL/code used by analytics defaults.
- `RO_SESSION_TIMEOUT_HOURS`: session lifetime for authenticated users.
- `OLLAMA_HOST`: URL for the Ollama API.
