# Dockerfile (example)
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system deps, Xvfb, and Google Chrome
# Install system dependencies, Chromium and Xvfb in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates unzip xvfb \
    libnss3 libxss1 fonts-liberation libappindicator3-1 libatk1.0-0 \
    libatk-bridge2.0-0 libgtk-3-0 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxrandr2 \
    libasound2 libpangocairo-1.0-0 libglib2.0-0 libdbus-1-3 \
    chromium \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download and install a matching ChromeDriver
RUN CHROME_VERSION=$(chromium --version | awk '{print $2}' | cut -d'.' -f1) \
    && echo "Chromium major version: $CHROME_VERSION" \
    && DRIVER_URL=$(wget -qO- "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION}") \
    && wget -O /tmp/chromedriver.zip "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${DRIVER_URL}/linux64/chromedriver-linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/*
# copy app
COPY . .

# Make entrypoint script executable
RUN chmod +x ./start.sh

# Optional: expose a default port (Render expects the process to bind $PORT)
EXPOSE 8000

CMD ["./start.sh"]
