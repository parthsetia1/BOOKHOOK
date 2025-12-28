FROM python:3.10-slim

WORKDIR /app

# Install ONLY minimal system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Pre-install pip dependencies using binary wheels only
RUN pip install --upgrade pip setuptools wheel

# Copy only requirements first (better Docker caching)
COPY requirements.txt .

# Force pip to use binary wheels only
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy the rest of the app
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
