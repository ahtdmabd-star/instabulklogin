FROM python:3.11-slim

# Playwright এবং ব্রাউজার চালানোর জন্য প্রয়োজনীয় লাইব্রেরি ইনস্টল করা
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps chromium

COPY . .

CMD gunicorn --bind 0.0.0.0:$PORT app:app
