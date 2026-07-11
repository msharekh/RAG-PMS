# AEC-RAG Windows Installation Script (PowerShell)
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🏗️  AEC-RAG v1.0 - Windows Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-CommandExists {
    param($command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try {
        if (Get-Command $command) { return $true }
    }
    catch { return $false }
    finally { $ErrorActionPreference = $oldPreference }
}

# Step 1: Check Python
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
if (Test-CommandExists "python") {
    $pythonVersion = python --version
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python is not installed!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation"
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Step 2: Check pip
Write-Host "[2/6] Checking pip..." -ForegroundColor Yellow
if (Test-CommandExists "pip") {
    Write-Host "✅ pip found!" -ForegroundColor Green
} else {
    Write-Host "Installing pip..." -ForegroundColor Yellow
    python -m ensurepip --upgrade
}
Write-Host ""

# Step 3: Install Python packages
Write-Host "[3/6] Installing Python packages..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
$packages = @(
    "ollama",
    "chromadb",
    "pandas",
    "flask",
    "langchain",
    "langchain-community",
    "sentence-transformers"
)

foreach ($package in $packages) {
    Write-Host "  Installing $package..." -ForegroundColor Gray
    pip install $package --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install $package!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Host "✅ Packages installed!" -ForegroundColor Green
Write-Host ""

# Step 4: Check Ollama
Write-Host "[4/6] Checking Ollama installation..." -ForegroundColor Yellow
if (Test-CommandExists "ollama") {
    $ollamaVersion = ollama --version
    Write-Host "✅ Ollama found: $ollamaVersion" -ForegroundColor Green
} else {
    Write-Host "⚠️  Ollama not found!" -ForegroundColor Red
    Write-Host "Please install Ollama from: https://ollama.ai/download/windows" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After installing, run this script again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Step 5: Pull Ollama models
Write-Host "[5/6] Pulling Ollama models..." -ForegroundColor Yellow
Write-Host "This will download ~4GB of AI models..." -ForegroundColor Gray
Write-Host "The first time may take 10-20 minutes depending on your internet speed." -ForegroundColor Gray
Write-Host ""

Write-Host "Pulling nomic-embed-text (embedding model)..." -ForegroundColor Cyan
ollama pull nomic-embed-text
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to pull nomic-embed-text!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Pulling llama3.2 (chat model)..." -ForegroundColor Cyan
ollama pull llama3.2
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to pull llama3.2!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✅ Models downloaded!" -ForegroundColor Green
Write-Host ""

# Step 6: Create the Python script
Write-Host "[6/6] Creating AEC-RAG files..." -ForegroundColor Yellow

# Create the Python script using Here-String
$pythonScript = @'
import pandas as pd
import ollama
import chromadb
from chromadb.config import Settings
import json
import random
from datetime import datetime, timedelta
import time

class AECRAG:
    def __init__(self):
        print("🚀 Initializing AEC-RAG System...")
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=None
        ))
        self.collection = self.client.get_or_create_collection(
            name="project_data",
            metadata={"hnsw:space": "cosine"}
        )
        self.projects_df = None
        print("✅ AEC-RAG initialized!")
    
    def generate_sample_data(self, num_projects=100):
        print(f"📊 Generating {num_projects} sample projects...")
        projects = []
        statuses = ['Planning', 'In Progress', 'Review', 'Completed', 'On Hold']
        departments = ['Engineering', 'Construction', 'Design', 'Management']
        
        for i in range(1, num_projects + 1):
            start_date = datetime.now() - timedelta(days=random.randint(0, 730))
            end_date = start_date + timedelta(days=random.randint(30, 365))
            
            project = {
                'project_id': f'PRJ-{i:04d}',
                'project_name': f'Project {i}: {random.choice(["Construction", "Development", "Renovation", "Infrastructure"])}',
                'status': random.choice(statuses),
                'department': random.choice(departments),
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'budget': round(random.uniform(50000, 5000000), 2),
                'actual_cost': round(random.uniform(30000, 4500000), 2),
                'completion_percentage': random.randint(0, 100),
                'project_manager': f'Manager {chr(65 + random.randint(0, 25))}{random.randint(1, 20)}',
                'priority': random.choice(['Low', 'Medium', 'High', 'Critical']),
                'description': f"This project involves {random.choice(['structural improvements', 'system upgrades', 'capacity expansion', 'safety enhancements'])}",
                'cost_variance': 0
            }
            project['cost_variance'] = round(project['actual_cost'] - project['budget'], 2)
            projects.append(project)
        
        self.projects_df = pd.DataFrame(projects)
        print(f"✅ Generated {len(self.projects_df)} projects")
        return self.projects_df
    
    def prepare_documents(self):
        documents = []
        metadatas = []
        ids = []
        
        for idx, row in self.projects_df.iterrows():
            doc_text = f"""
            Project ID: {row['project_id']}
            Project Name: {row['project_name']}
            Status: {row['status']}
            Department: {row['department']}
            Start Date: {row['start_date']}
            End Date: {row['end_date']}
            Budget: ${row['budget']:,.2f}
            Actual Cost: ${row['actual_cost']:,.2f}
            Completion: {row['completion_percentage']}%
            Project Manager: {row['project_manager']}
            Priority: {row['priority']}
            Description: {row['description']}
            Cost Variance: ${row['cost_variance']:,.2f}
            """
            documents.append(doc_text.strip())
            metadatas.append({
                'project_id': row['project_id'],
                'status': row['status'],
                'budget': row['budget'],
                'actual_cost': row['actual_cost'],
                'completion_percentage': row['completion_percentage']
            })
            ids.append(row['project_id'])
        
        return documents, metadatas, ids
    
    def generate_embeddings(self, texts):
        embeddings = []
        for text in texts:
            try:
                response = ollama.embeddings(model="nomic-embed-text", prompt=text)
                embeddings.append(response['embedding'])
            except Exception as e:
                embeddings.append([0.0] * 768)
        return embeddings
    
    def index_projects(self):
        documents, metadatas, ids = self.prepare_documents()
        embeddings = self.generate_embeddings(documents)
        try:
            self.collection.add(embeddings=embeddings, documents=documents, metadatas=metadatas, ids=ids)
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def query(self, question, n_results=3):
        try:
            query_embedding = ollama.embeddings(model="nomic-embed-text", prompt=question)['embedding']
            results = self.collection.query(query_embeddings=[query_embedding], n_results=n_results)
            relevant_docs = []
            for i, doc in enumerate(results['documents'][0]):
                relevant_docs.append({
                    'project_id': results['ids'][0][i],
                    'content': doc,
                    'metadata': results['metadatas'][0][i]
                })
            response = self.generate_response(question, relevant_docs)
            return {'question': question, 'response': response, 'relevant_docs': relevant_docs}
        except Exception as e:
            return {'question': question, 'response': f"Error: {str(e)}", 'relevant_docs': []}
    
    def generate_response(self, question, relevant_docs):
        if not relevant_docs:
            return "No relevant projects found."
        
        context = "Here are the relevant projects:\n\n"
        for i, doc in enumerate(relevant_docs, 1):
            context += f"Project {i}:\n{doc['content']}\n\n"
        
        prompt = f"""You are AEC-RAG, an AI assistant for project managers.
Question: {question}
Based on this information:
{context}
Provide a professional and helpful response."""
        
        try:
            response = ollama.chat(
                model="llama3.2",
                messages=[
                    {"role": "system", "content": "You are a helpful project management assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response['message']['content']
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def run_cli(self):
        print("\n" + "="*60)
        print("🏗️  AEC-RAG - Project Management Assistant")
        print("="*60)
        print("Type 'exit' to quit, 'help' for assistance")
        print("Example questions:")
        print("- What is the status of all projects?")
        print("- Show me projects with budget over $1M")
        print("- Which projects are behind schedule?")
        print("="*60 + "\n")
        
        while True:
            question = input("🔍 Ask about your projects: ").strip()
            if question.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye!")
                break
            elif question.lower() in ['help', '?']:
                print("\nAsk questions about project status, budget, costs\n")
                continue
            elif not question:
                continue
            
            result = self.query(question)
            print("\n" + "="*60)
            print("📋 Response:")
            print("="*60)
            print(result['response'])
            if result['relevant_docs']:
                print("\n📎 Referenced Projects:")
                for doc in result['relevant_docs']:
                    print(f"  • {doc['project_id']}")
            print("\n" + "-"*60 + "\n")

def main():
    rag = AECRAG()
    rag.generate_sample_data(100)
    rag.index_projects()
    rag.run_cli()

if __name__ == "__main__":
    main()
'@

# Save the Python script
$pythonScript | Out-File -FilePath "aec_rag.py" -Encoding UTF8
Write-Host "✅ Created aec_rag.py" -ForegroundColor Green

# Create run script
$runScript = @'
@echo off
echo Starting AEC-RAG...
python aec_rag.py
pause
'@

$runScript | Out-File -FilePath "run.bat" -Encoding ASCII
Write-Host "✅ Created run.bat (double-click to start)" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📌 To run AEC-RAG:" -ForegroundColor Yellow
Write-Host "   Method 1: Double-click run.bat" -ForegroundColor White
Write-Host "   Method 2: python aec_rag.py" -ForegroundColor White
Write-Host ""
Write-Host "📌 Example questions to try:" -ForegroundColor Yellow
Write-Host "   - What is the status of all projects?" -ForegroundColor White
Write-Host "   - Show me projects with budget over $1M" -ForegroundColor White
Write-Host "   - Which projects are behind schedule?" -ForegroundColor White
Write-Host "   - What's the total cost variance?" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"