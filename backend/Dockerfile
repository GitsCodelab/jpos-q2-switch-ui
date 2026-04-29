FROM python:3.12-slim

WORKDIR /app

# --- Corporate SSL certificate (FG SSL inspection) ---
# Build context is the repo root, so FG-SSL-INSPECTION.cer is at the top level
COPY FG-SSL-INSPECTION.cer /usr/local/share/ca-certificates/FG-SSL-INSPECTION.crt
RUN apt-get update -o Acquire::https::Verify-Peer=false \
    && apt-get install -y --no-install-recommends ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Install Python deps trusting the updated store ---
COPY backend/requirements.txt .
RUN pip install --no-cache-dir \
    --cert /etc/ssl/certs/ca-certificates.crt \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

# --- Copy app source ---
COPY backend/ .

EXPOSE 8000

CMD ["python", "run.py"]
