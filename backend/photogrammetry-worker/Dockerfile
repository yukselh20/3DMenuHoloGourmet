# Use a stable Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- Install Node.js and gltf-pipeline ---
RUN curl -sL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs
RUN npm install -g gltf-pipeline

# --- Install Meshroom ---
# Copy the pre-downloaded Meshroom archive from the local 'assets' folder
COPY ./assets/Meshroom-2023.3.0-linux.tar.gz /tmp/meshroom.tar.gz

# Extract Meshroom
RUN mkdir -p /opt/meshroom && \
    tar -xzf /tmp/meshroom.tar.gz -C /opt/meshroom --strip-components=1 && \
    rm /tmp/meshroom.tar.gz

# Add Meshroom to the system's PATH
ENV PATH="/opt/meshroom:$PATH"

# --- Install Python dependencies ---
# Copy the requirements file and install dependencies
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code
COPY . .

# Command to run the Celery worker
CMD ["celery", "-A", "celery_app.celery", "worker", "--loglevel=info"]

