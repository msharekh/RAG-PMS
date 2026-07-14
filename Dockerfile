FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY aec_rag_web_excel.py .

EXPOSE 5000

ENV DATA_FILE_PATH="/data/project_data.xlsx"
ENV OLLAMA_HOST="http://ollama:11434"

# Use a standard sleep delay to ensure the adjacent ollama container has fully booted
# CMD ["sh", "-c", "sleep 10 && python aec_rag_web_excel.py"]
CMD ["python", "aec_rag_web_excel.py"]