FROM python:3.11-slim

# Install system dependencies needed for building certain packages if necessary
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY aec_rag_web_excel.py .

# Expose Flask port
EXPOSE 5000

# Set an environment variable to override the Excel path inside the container
ENV DATA_FILE_PATH="/data/project_data.xlsx"

# Run the app
CMD ["python", "aec_rag_web_excel.py"]