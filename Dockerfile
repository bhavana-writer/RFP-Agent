# Use official Python slim image
FROM python:3.12-slim
# Set the working directory
WORKDIR /app
# Copy requirements first to leverage Docker cache
COPY requirements.txt .
# Install dependencies
RUN pip install -r requirements.txt && \
    pip install writer==0.8.3rc10
# Copy application files
COPY . .
# Set the PORT environment variable for Cloud Run
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV WRITER_DEBUG=1
ENV WRITER_API_KEY=7Ygd3hchmQjJV9rEADN8duy0MoSmRQEA
# Run the writer command with remote edit enabled
CMD ["writer", "edit", ".", "--host", "0.0.0.0", "--port", "8080", "--enable-server-setup", "--enable-remote-edit"]
EXPOSE 8080