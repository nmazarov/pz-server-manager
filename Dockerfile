FROM python:3.10-slim

# Install system dependencies for PyQt5 and other binaries
RUN apt-get update && apt-get install -y \
    libqt5gui5 \
    libqt5core5a \
    libqt5widgets5 \
    libgl1-mesa-glx \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY requirements.txt requirements-web.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt -r requirements-web.txt

# Copy application code
COPY . .

# Expose ports
# Web Dashboard: 8080
# PZ Server: 16261 (UDP), 16262 (UDP), 8766 (UDP), 8767 (UDP), 27015 (TCP)
EXPOSE 8080 16261/udp 16262/udp 8766/udp 8767/udp 27015/tcp

# Run the application
CMD ["python", "main.py", "--web"]
