# Use an official Python runtime as a base image
FROM python:3.11-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project requirements
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . /app/

# Expose the application on port 8080
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "serve:app_hub", "--host", "0.0.0.0", "--port", "8080"]
