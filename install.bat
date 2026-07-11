@echo off
echo ========================================
echo 🏗️  AEC-RAG v1.0 - Windows Installation
echo ========================================
echo.

:: Check if Python is installed
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed!
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)
echo ✅ Python found!
python --version
echo.

:: Check if pip is installed
echo [2/6] Checking pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip not found! Installing...
    python -m ensurepip --upgrade
)
echo ✅ pip found!
echo.

:: Install Python packages
echo [3/6] Installing Python packages...
echo This may take a few minutes...
pip install ollama chromadb pandas flask langchain langchain-community sentence-transformers --quiet
if errorlevel 1 (
    echo ❌ Failed to install packages!
    pause
    exit /b 1
)
echo ✅ Packages installed!
echo.

:: Check if Ollama is installed
echo [4/6] Checking Ollama installation...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Ollama not found!
    echo Please install Ollama from: https://ollama.ai/download/windows
    echo.
    echo After installing, run this script again.
    pause
    exit /b 1
)
echo ✅ Ollama found!
ollama --version
echo.

:: Pull Ollama models
echo [5/6] Pulling Ollama models...
echo This will download ~4GB of AI models...
echo The first time may take 10-20 minutes depending on your internet speed.
echo.

echo Pulling nomic-embed-text (embedding model)...
ollama pull nomic-embed-text
if errorlevel 1 (
    echo ❌ Failed to pull nomic-embed-text!
    pause
    exit /b 1
)

echo Pulling llama3.2 (chat model)...
ollama pull llama3.2
if errorlevel 1 (
    echo ❌ Failed to pull llama3.2!
    pause
    exit /b 1
)
echo ✅ Models downloaded!
echo.

:: Create the Python script files
echo [6/6] Creating AEC-RAG files...
echo.

:: Create aec_rag.py
echo Creating aec_rag.py...
(
echo import pandas as pd
echo import ollama
echo import chromadb
echo from chromadb.config import Settings
echo import json
echo import random
echo from datetime import datetime, timedelta
echo import time
echo.
echo class AECRAG:
echo     def __init__(self^):
echo         print("🚀 Initializing AEC-RAG System...")
echo         self.client = chromadb.Client(Settings^(
echo             chroma_db_impl="duckdb+parquet",
echo             persist_directory=None
echo         ^)^)
echo         self.collection = self.client.get_or_create_collection^(
echo             name="project_data",
echo             metadata={"hnsw:space": "cosine"}
echo         ^)
echo         self.projects_df = None
echo         print("✅ AEC-RAG initialized!")
echo.
echo     def generate_sample_data(self, num_projects=100^):
echo         print(f"📊 Generating {num_projects} sample projects...")
echo         projects = []
echo         statuses = ['Planning', 'In Progress', 'Review', 'Completed', 'On Hold']
echo         departments = ['Engineering', 'Construction', 'Design', 'Management']
echo         for i in range(1, num_projects + 1^):
echo             start_date = datetime.now(^) - timedelta(days=random.randint(0, 730^)^)
echo             end_date = start_date + timedelta(days=random.randint(30, 365^)^)
echo             project = {
echo                 'project_id': f'PRJ-{i:04d}',
echo                 'project_name': f'Project {i}: {random.choice(["Construction", "Development", "Renovation", "Infrastructure"])}',
echo                 'status': random.choice(statuses^),
echo                 'department': random.choice(departments^),
echo                 'start_date': start_date.strftime('%%Y-%%m-%%d'),
echo                 'end_date': end_date.strftime('%%Y-%%m-%%d'),
echo                 'budget': round(random.uniform(50000, 5000000^), 2^),
echo                 'actual_cost': round(random.uniform(30000, 4500000^), 2^),
echo                 'completion_percentage': random.randint(0, 100^),
echo                 'project_manager': f'Manager {chr(65 + random.randint(0, 25^^)^)}{random.randint(1, 20^)}',
echo                 'priority': random.choice(['Low', 'Medium', 'High', 'Critical']^),
echo                 'description': f"This project involves {random.choice(['structural improvements', 'system upgrades', 'capacity expansion', 'safety enhancements'])}",
echo                 'cost_variance': 0
echo             }
echo             project['cost_variance'] = round(project['actual_cost'] - project['budget'], 2^)
echo             projects.append(project^)
echo         self.projects_df = pd.DataFrame(projects^)
echo         print(f"✅ Generated {len(self.projects_df)} projects")
echo         return self.projects_df
echo.
echo     def prepare_documents(self^):
echo         documents = []
echo         metadatas = []
echo         ids = []
echo         for idx, row in self.projects_df.iterrows(^)^:
echo             doc_text = f"""
echo             Project ID: {row['project_id']}
echo             Project Name: {row['project_name']}
echo             Status: {row['status']}
echo             Department: {row['department']}
echo             Start Date: {row['start_date']}
echo             End Date: {row['end_date']}
echo             Budget: ${row['budget']:,.2f}
echo             Actual Cost: ${row['actual_cost']:,.2f}
echo             Completion: {row['completion_percentage']}%%
echo             Project Manager: {row['project_manager']}
echo             Priority: {row['priority']}
echo             Description: {row['description']}
echo             Cost Variance: ${row['cost_variance']:,.2f}
echo             """
echo             documents.append(doc_text.strip(^)^)
echo             metadatas.append({
echo                 'project_id': row['project_id'],
echo                 'status': row['status'],
echo                 'budget': row['budget'],
echo                 'actual_cost': row['actual_cost'],
echo                 'completion_percentage': row['completion_percentage']
echo             ^})
echo             ids.append(row['project_id']^)
echo         return documents, metadatas, ids
echo.
echo     def generate_embeddings(self, texts^):
echo         embeddings = []
echo         for text in texts:
echo             try:
echo                 response = ollama.embeddings(model="nomic-embed-text", prompt=text^)
echo                 embeddings.append(response['embedding']^)
echo             except Exception as e:
echo                 embeddings.append([0.0] * 768^)
echo         return embeddings
echo.
echo     def index_projects(self^):
echo         documents, metadatas, ids = self.prepare_documents(^)
echo         embeddings = self.generate_embeddings(documents^)
echo         try:
echo             self.collection.add(embeddings=embeddings, documents=documents, metadatas=metadatas, ids=ids^)
echo             return True
echo         except Exception as e:
echo             print(f"❌ Error: {e}")
echo             return False
echo.
echo     def query(self, question, n_results=3^):
echo         try:
echo             query_embedding = ollama.embeddings(model="nomic-embed-text", prompt=question^)['embedding']
echo             results = self.collection.query(query_embeddings=[query_embedding], n_results=n_results^)
echo             relevant_docs = []
echo             for i, doc in enumerate(results['documents'][0]^):
echo                 relevant_docs.append({
echo                     'project_id': results['ids'][0][i],
echo                     'content': doc,
echo                     'metadata': results['metadatas'][0][i]
echo                 ^})
echo             response = self.generate_response(question, relevant_docs^)
echo             return {'question': question, 'response': response, 'relevant_docs': relevant_docs}
echo         except Exception as e:
echo             return {'question': question, 'response': f"Error: {str(e)}", 'relevant_docs': []}
echo.
echo     def generate_response(self, question, relevant_docs^):
echo         if not relevant_docs:
echo             return "No relevant projects found."
echo         context = "Here are the relevant projects:\n\n"
echo         for i, doc in enumerate(relevant_docs, 1^):
echo             context += f"Project {i}:\n{doc['content']}\n\n"
echo         prompt = f"""You are AEC-RAG, an AI assistant for project managers.
echo Question: {question}
echo Based on this information:
echo {context}
echo Provide a professional and helpful response."""
echo         try:
echo             response = ollama.chat(
echo                 model="llama3.2",
echo                 messages=[
echo                     {"role": "system", "content": "You are a helpful project management assistant."},
echo                     {"role": "user", "content": prompt}
echo                 ]
echo             ^)
echo             return response['message']['content']
echo         except Exception as e:
echo             return f"Error generating response: {str(e)}"
echo.
echo     def run_cli(self^):
echo         print("\n" + "="*60^)
echo         print("🏗️  AEC-RAG - Project Management Assistant"^)
echo         print("="*60^)
echo         print("Type 'exit' to quit, 'help' for assistance"^)
echo         while True:
echo             question = input("🔍 Ask about your projects: ").strip(^)
echo             if question.lower(^) in ['exit', 'quit', 'bye']:
echo                 print("👋 Goodbye!"^)
echo                 break
echo             elif question.lower(^) in ['help', '?']:
echo                 print("\nAsk questions about project status, budget, costs\n"^)
echo                 continue
echo             elif not question:
echo                 continue
echo             result = self.query(question^)
echo             print("\n" + "="*60^)
echo             print("📋 Response:"^)
echo             print("="*60^)
echo             print(result['response']^)
echo             if result['relevant_docs']:
echo                 print("\n📎 Referenced Projects:"^)
echo                 for doc in result['relevant_docs']:
echo                     print(f"  • {doc['project_id']}"^)
echo             print("\n" + "-"*60 + "\n"^)
echo.
echo def main(^):
echo     rag = AECRAG(^)
echo     rag.generate_sample_data(100^)
echo     rag.index_projects(^)
echo     rag.run_cli(^)
echo.
echo if __name__ == "__main__":
echo     main(^)
) > aec_rag.py

echo.
echo ========================================
echo ✅ Installation Complete!
echo ========================================
echo.
echo 📌 To run AEC-RAG:
echo    python aec_rag.py
echo.
echo 📌 Example questions to try:
echo    - What is the status of all projects?
echo    - Show me projects with budget over $1M
echo    - Which projects are behind schedule?
echo    - What's the total cost variance?
echo.
pause