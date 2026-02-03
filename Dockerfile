# Use Apify's official Node.js + Puppeteer + Chrome image
FROM apify/actor-node-puppeteer-chrome:20

# Install Python 3 and pip
USER root
RUN apt-get update && apt-get install -y python3 python3-pip dos2unix && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Copy Python requirements
COPY requirements.txt ./

# Install Python dependencies
# Break system packages restriction if needed
RUN pip3 install -r requirements.txt --break-system-packages

# Copy source code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome-stable

# Expose port (internal communication)
EXPOSE 8081

# Make start script executable and fix line endings
RUN dos2unix start.sh && chmod +x start.sh

# Set entrypoint
ENTRYPOINT ["./start.sh"]
