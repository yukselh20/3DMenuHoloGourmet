# Use a stable Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app/backend

# Install Python dependencies
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# The CMD will be overridden by docker-compose, but this is a good default
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]