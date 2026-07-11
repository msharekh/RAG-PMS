# aec_rag_web_excel.py - Web Interface with Excel File Loading

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import pandas as pd
import ollama
import chromadb
import os
from datetime import datetime, timedelta
import time
import random
import sys
import subprocess
import traceback

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# ==================== AEC-RAG SYSTEM CLASS ====================

class AECRAG:
    """
    AEC-RAG: Project Management RAG System
    Loads data from Excel file on C drive
    """
    
    def __init__(self, data_file_path=None):
        """
        Initialize the RAG system with file-based data loading
        """
        print("🚀 Initializing AEC-RAG System...")
        
        # Set default file path if not provided
        if data_file_path is None:
            self.data_file_path = "C:/AEC_Projects/project_data.xlsx"
        else:
            self.data_file_path = data_file_path
        
        # Define models with CORRECT names
        self.embedding_model = "nomic-embed-text"      # For embeddings
        self.chat_model = "llama3.2:latest"            # For chat responses
        
        # Check Ollama connection and models
        self.check_ollama_connection()
        
        # Initialize ChromaDB client
        self.client = chromadb.EphemeralClient()
        
        # Create or get collection for project data
        self.collection = self.client.get_or_create_collection(
            name="project_data",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Store project data
        self.projects_df = None
        
        print(f"✅ AEC-RAG initialized! Data source: {self.data_file_path}")
    
    def check_ollama_connection(self):
        """
        Check if Ollama is running and models are available
        """
        print("🔍 Checking Ollama connection...")
        
        try:
            # Try to list models to check connection
            response = ollama.list()
            print("✅ Ollama is running")
            
            # Get installed models
            installed_models = [model['model'] for model in response.get('models', [])]
            print(f"📦 Installed models: {installed_models}")
            
            # Check if required models are installed
            embedding_available = any(self.embedding_model in model for model in installed_models)
            chat_available = any(self.chat_model in model for model in installed_models)
            
            if not embedding_available:
                print(f"⚠️ Embedding model '{self.embedding_model}' not found")
                print(f"📌 Pulling model: ollama pull {self.embedding_model}")
                self.pull_model(self.embedding_model)
            else:
                print(f"✅ Embedding model available: {self.embedding_model}")
            
            if not chat_available:
                print(f"⚠️ Chat model '{self.chat_model}' not found")
                print(f"📌 Pulling model: ollama pull {self.chat_model}")
                self.pull_model(self.chat_model)
            else:
                print(f"✅ Chat model available: {self.chat_model}")
                
        except Exception as e:
            print(f"❌ Ollama connection error: {e}")
            print("\n📌 Please ensure:")
            print("  1. Ollama is installed (https://ollama.ai)")
            print("  2. Ollama is running (ollama serve)")
            print("  3. You have pulled the required models:")
            print(f"     ollama pull {self.embedding_model}")
            print(f"     ollama pull {self.chat_model}")
            sys.exit(1)
    
    def pull_model(self, model_name):
        """
        Pull an Ollama model
        """
        print(f"⬇️ Pulling {model_name}... This may take a few minutes...")
        
        try:
            # Use ollama pull command
            result = subprocess.run(['ollama', 'pull', model_name], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully pulled {model_name}")
                return True
            else:
                print(f"❌ Failed to pull {model_name}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error pulling {model_name}: {e}")
            return False
    
    def load_data_from_file(self):
        """
        Load project data from Excel file on C drive
        """
        print(f"📂 Loading data from: {self.data_file_path}")
        
        if not os.path.exists(self.data_file_path):
            print(f"❌ File not found: {self.data_file_path}")
            print("📝 Creating sample data file as template...")
            self.create_template_file()
            return True
        
        try:
            file_ext = os.path.splitext(self.data_file_path)[1].lower()
            
            if file_ext in ['.xlsx', '.xls']:
                self.projects_df = pd.read_excel(self.data_file_path)
                print(f"✅ Loaded Excel file with {len(self.projects_df)} records")
                
            elif file_ext == '.csv':
                self.projects_df = pd.read_csv(self.data_file_path)
                print(f"✅ Loaded CSV file with {len(self.projects_df)} records")
                
            else:
                print(f"❌ Unsupported file type: {file_ext}")
                return False
            
            if self.validate_data():
                print("✅ Data validation passed!")
                return True
            else:
                print("❌ Data validation failed.")
                return False
                
        except Exception as e:
            print(f"❌ Error loading file: {str(e)}")
            traceback.print_exc()
            return False
    
    def create_template_file(self):
        """
        Create a template Excel file with sample data
        """
        print("📝 Creating template file with sample data...")
        
        sample_data = self.generate_sample_data(50)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.data_file_path), exist_ok=True)
        sample_data.to_excel(self.data_file_path, index=False)
        
        print(f"✅ Template file created at: {self.data_file_path}")
        print("📌 Please update this file with your actual project data")
        
        self.projects_df = sample_data
        return True
    
    def generate_sample_data(self, num_projects=50):
        """
        Generate sample project data with realistic values
        """
        print(f"📊 Generating {num_projects} sample projects...")
        
        projects = []
        statuses = ['Planning', 'In Progress', 'Review', 'Completed', 'On Hold']
        departments = ['Engineering', 'Construction', 'Design', 'Management', 'Safety']
        
        for i in range(1, num_projects + 1):
            start_date = datetime.now() - timedelta(days=random.randint(0, 730))
            end_date = start_date + timedelta(days=random.randint(30, 365))
            
            budget = round(random.uniform(50000, 5000000), 2)
            actual_cost = round(budget * random.uniform(0.5, 1.2), 2)
            
            project = {
                'project_id': f'PRJ-{i:04d}',
                'project_name': f'Project {i}: {random.choice(["Construction", "Development", "Renovation", "Infrastructure"])}',
                'status': random.choice(statuses),
                'department': random.choice(departments),
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'budget': budget,
                'actual_cost': actual_cost,
                'completion_percentage': random.randint(0, 100),
                'project_manager': f'Manager {chr(65 + random.randint(0, 25))}{random.randint(1, 20)}',
                'priority': random.choice(['Low', 'Medium', 'High', 'Critical']),
                'description': f"This project involves {random.choice(['structural improvements', 'system upgrades', 'capacity expansion', 'safety enhancements'])}.",
                'cost_variance': round(actual_cost - budget, 2)
            }
            projects.append(project)
        
        df = pd.DataFrame(projects)
        print(f"✅ Generated {len(df)} sample projects")
        return df
    
    def validate_data(self):
        """
        Validate that the loaded data has required columns
        """
        required_columns = [
            'project_id', 'project_name', 'status', 'budget', 
            'actual_cost', 'completion_percentage'
        ]
        
        missing_columns = []
        for col in required_columns:
            if col not in self.projects_df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            print("📌 Required columns: project_id, project_name, status, budget, actual_cost, completion_percentage")
            return False
        
        if len(self.projects_df) == 0:
            print("❌ No data found in file")
            return False
        
        return True
    
    def prepare_documents(self):
        """
        Prepare documents from project data for embedding
        """
        print("📝 Preparing documents for indexing...")
        
        documents = []
        metadatas = []
        ids = []
        
        for idx, row in self.projects_df.iterrows():
            doc_text = f"""
            Project ID: {row.get('project_id', 'N/A')}
            Project Name: {row.get('project_name', 'N/A')}
            Status: {row.get('status', 'N/A')}
            Department: {row.get('department', 'N/A')}
            Start Date: {row.get('start_date', 'N/A')}
            End Date: {row.get('end_date', 'N/A')}
            Budget: ${row.get('budget', 0):,.2f}
            Actual Cost: ${row.get('actual_cost', 0):,.2f}
            Completion: {row.get('completion_percentage', 0)}%
            Project Manager: {row.get('project_manager', 'N/A')}
            Priority: {row.get('priority', 'N/A')}
            Description: {row.get('description', 'N/A')}
            Cost Variance: ${row.get('cost_variance', 0):,.2f}
            """
            
            documents.append(doc_text.strip())
            metadatas.append({
                'project_id': row.get('project_id', 'N/A'),
                'status': row.get('status', 'N/A'),
                'budget': row.get('budget', 0),
                'actual_cost': row.get('actual_cost', 0),
                'completion_percentage': row.get('completion_percentage', 0)
            })
            ids.append(row.get('project_id', f'PRJ-{idx}'))
        
        print(f"✅ Prepared {len(documents)} documents")
        return documents, metadatas, ids
    
    def generate_embeddings(self, texts):
        """
        Generate embeddings using Ollama with error handling
        """
        print("🧠 Generating embeddings using Ollama...")
        embeddings = []
        total = len(texts)
        
        for i, text in enumerate(texts):
            try:
                if (i + 1) % 10 == 0 or i == total - 1:
                    print(f"  Processing {i+1}/{total}...")
                
                response = ollama.embeddings(
                    model=self.embedding_model,
                    prompt=text
                )
                embeddings.append(response['embedding'])
                
            except Exception as e:
                print(f"⚠️ Error generating embedding for document {i}: {e}")
                # Use zero vector as fallback
                embeddings.append([0.0] * 768)
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        return embeddings
    
    def index_projects(self):
        """
        Main indexing function - prepare and store project data
        """
        print("📚 Indexing projects into vector database...")
        
        if self.projects_df is None or len(self.projects_df) == 0:
            print("❌ No data to index")
            return False
        
        try:
            documents, metadatas, ids = self.prepare_documents()
            embeddings = self.generate_embeddings(documents)
            
            # Clear existing data
            try:
                existing_data = self.collection.get()
                if existing_data and existing_data['ids']:
                    self.collection.delete(ids=existing_data['ids'])
                    print(f"🗑️ Cleared {len(existing_data['ids'])} existing documents")
            except Exception as e:
                print(f"Note: {e}")
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ Successfully indexed {len(documents)} projects")
            return True
            
        except Exception as e:
            print(f"❌ Error indexing projects: {e}")
            traceback.print_exc()
            return False
    
    def query(self, question, n_results=3):
        """
        Query the RAG system with a natural language question
        """
        print(f"🔍 Processing query: '{question}'")
        
        try:
            # Generate embedding for the question
            try:
                query_embedding = ollama.embeddings(
                    model=self.embedding_model,
                    prompt=question
                )['embedding']
            except Exception as e:
                print(f"❌ Error generating query embedding: {e}")
                return {
                    'question': question,
                    'response': f"Error: {str(e)}",
                    'relevant_docs': [],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Search for relevant documents
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            relevant_docs = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    relevant_docs.append({
                        'project_id': results['ids'][0][i],
                        'content': doc,
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })
            
            response = self.generate_response(question, relevant_docs)
            
            return {
                'question': question,
                'response': response,
                'relevant_docs': relevant_docs,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            traceback.print_exc()
            return {
                'question': question,
                'response': f"Error: {str(e)}",
                'relevant_docs': [],
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_response(self, question, relevant_docs):
        """
        Generate natural language response using Ollama
        """
        if not relevant_docs:
            return "No relevant project information found. Please try rephrasing your question."
        
        context = "Based on the project data, here are the most relevant projects:\n\n"
        for i, doc in enumerate(relevant_docs, 1):
            context += f"Project {i}:\n{doc['content']}\n\n"
        
        prompt = f"""You are AEC-RAG, an AI assistant for project managers.

The user asks: {question}

Here is the relevant project information:
{context}

Provide a clear, professional answer based ONLY on the project information provided.

Answer:"""
        
        try:
            response = ollama.chat(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": "You are a helpful project management assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response['message']['content']
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def show_project_stats(self):
        """
        Display summary statistics of loaded projects
        """
        if self.projects_df is None or len(self.projects_df) == 0:
            return {"error": "No project data available"}
        
        stats = {
            'total_projects': len(self.projects_df),
            'status_distribution': self.projects_df['status'].value_counts().to_dict(),
            'average_budget': float(self.projects_df['budget'].mean()),
            'average_completion': float(self.projects_df['completion_percentage'].mean()),
            'total_budget': float(self.projects_df['budget'].sum()),
            'total_cost': float(self.projects_df['actual_cost'].sum())
        }
        
        return stats

# ==================== INITIALIZE SYSTEM ====================

print("🏗️ Initializing AEC-RAG Web Interface...")

# Create the RAG system with the same Excel file path
rag = AECRAG("C:/AEC_Projects/project_data.xlsx")

# Load and index data
if not rag.load_data_from_file():
    print("❌ Could not load data")
    sys.exit(1)

if not rag.index_projects():
    print("❌ Could not index projects")
    sys.exit(1)

print("✅ System ready!")

# ==================== HTML TEMPLATE ====================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEC-RAG - Project Management Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 900px;
            height: 90vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid #e74c3c;
            flex-shrink: 0;
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 700;
        }
        
        .header h1 span {
            color: #f1c40f;
        }
        
        .header-info {
            display: flex;
            gap: 20px;
            font-size: 14px;
            opacity: 0.9;
        }
        
        .header-info .badge {
            background: rgba(255,255,255,0.2);
            padding: 5px 12px;
            border-radius: 20px;
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message.user {
            text-align: right;
        }
        
        .message .bubble {
            display: inline-block;
            padding: 12px 20px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
            text-align: left;
        }
        
        .message.user .bubble {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        .message.assistant .bubble {
            background: white;
            color: #2c3e50;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .message .sources {
            margin-top: 10px;
            font-size: 13px;
            background: #ecf0f1;
            padding: 10px 15px;
            border-radius: 10px;
            display: inline-block;
            width: 100%;
        }
        
        .message .sources strong {
            color: #2c3e50;
        }
        
        .message .sources .source-item {
            color: #3498db;
            margin: 3px 0;
            font-size: 12px;
        }
        
        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
            flex-shrink: 0;
        }
        
        .input-container input {
            flex: 1;
            padding: 12px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            transition: all 0.3s;
        }
        
        .input-container input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.2);
        }
        
        .input-container input:disabled {
            opacity: 0.6;
        }
        
        .input-container button {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
            white-space: nowrap;
        }
        
        .input-container button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .input-container button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .quick-questions {
            padding: 10px 20px;
            background: #f8f9fa;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            flex-shrink: 0;
        }
        
        .quick-questions button {
            padding: 6px 15px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 20px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s;
            color: #2c3e50;
        }
        
        .quick-questions button:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .typing-indicator {
            display: none;
            padding: 10px 20px;
            background: white;
            border-radius: 15px;
            margin-bottom: 15px;
        }
        
        .typing-indicator.active {
            display: inline-block;
        }
        
        .stats-bar {
            background: #ecf0f1;
            padding: 8px 20px;
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #7f8c8d;
            border-top: 1px solid #ddd;
            flex-shrink: 0;
        }
        
        .chat-container::-webkit-scrollbar {
            width: 6px;
        }
        
        .chat-container::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        .chat-container::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 3px;
        }
        
        .chat-container::-webkit-scrollbar-thumb:hover {
            background: #764ba2;
        }
        
        .error-message {
            color: #e74c3c;
            background: #fdf0ef;
            padding: 10px;
            border-radius: 10px;
            border-left: 4px solid #e74c3c;
        }
        
        .file-info {
            background: #e8f4f8;
            padding: 8px 20px;
            font-size: 12px;
            color: #2c3e50;
            border-bottom: 1px solid #d4e6f0;
            display: flex;
            justify-content: space-between;
            flex-shrink: 0;
        }
        
        .file-info span {
            font-family: monospace;
            font-size: 12px;
            color: #3498db;
        }
        
        @media (max-width: 768px) {
            .container {
                height: 100vh;
                border-radius: 0;
            }
            
            .header {
                padding: 15px;
                flex-direction: column;
                gap: 10px;
            }
            
            .header h1 {
                font-size: 20px;
            }
            
            .header-info {
                font-size: 12px;
                flex-wrap: wrap;
                justify-content: center;
            }
            
            .message .bubble {
                max-width: 90%;
            }
            
            .quick-questions {
                display: none;
            }
            
            .input-container button {
                padding: 12px 20px;
                font-size: 14px;
            }
            
            .file-info {
                font-size: 10px;
                flex-direction: column;
                align-items: center;
                gap: 5px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ AEC-<span>RAG</span></h1>
            <div class="header-info">
                <span class="badge" id="projectCount">📊 Loading...</span>
                <span class="badge" id="modelName">🤖 llama3.2</span>
                <span class="badge">🟢 Online</span>
            </div>
        </div>
        
        <div class="file-info">
            <span>📁 Data Source: {{ data_file }}</span>
            <span>📅 Last Updated: {{ last_updated }}</span>
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message assistant">
                <div class="bubble">
                    <strong>👋 Welcome to AEC-RAG!</strong><br><br>
                    I'm your project management assistant. I can help you query your project data using natural language.<br><br>
                    <strong>Try asking me:</strong><br>
                    • What projects are over budget?<br>
                    • Show me high priority projects<br>
                    • What is the total budget?<br>
                    • Which projects are behind schedule?<br><br>
                    <strong>📁 Data File:</strong> {{ data_file }}
                </div>
            </div>
        </div>
        
        <div class="quick-questions">
            <button onclick="askQuestion('What projects are over budget?')">💰 Over Budget</button>
            <button onclick="askQuestion('Show me high priority projects')">⚡ High Priority</button>
            <button onclick="askQuestion('What is the total budget?')">📊 Total Budget</button>
            <button onclick="askQuestion('Which projects are behind schedule?')">📅 Behind Schedule</button>
            <button onclick="askQuestion('Show me completed projects')">✅ Completed</button>
            <button onclick="askQuestion('Reload data from Excel file')">🔄 Reload</button>
        </div>
        
        <div class="stats-bar">
            <span>💬 Ask any question about your projects</span>
            <span>⚡ Fast responses • 🔒 Private • 🏠 Local</span>
        </div>
        
        <div class="input-container">
            <input type="text" id="questionInput" placeholder="Ask about your projects..." onkeypress="handleKeyPress(event)">
            <button id="sendButton" onclick="sendQuestion()">Send 🚀</button>
        </div>
    </div>
    
    <script>
        // Get elements
        var chatContainer = document.getElementById('chatContainer');
        var questionInput = document.getElementById('questionInput');
        var sendButton = document.getElementById('sendButton');
        
        // Load initial stats
        async function loadStats() {
            try {
                var response = await fetch('/api/stats');
                if (response.ok) {
                    var data = await response.json();
                    document.getElementById('projectCount').textContent = '📊 ' + data.total_projects + ' Projects';
                }
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        // Load stats on page load
        loadStats();
        
        // Add a message to the chat
        function addMessage(text, sender, sources) {
            var messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + sender;
            
            var bubble = document.createElement('div');
            bubble.className = 'bubble';
            
            // Format text with line breaks
            var formattedText = text.replace(/\\n/g, '<br>');
            bubble.innerHTML = formattedText;
            
            messageDiv.appendChild(bubble);
            
            // Add sources if available
            if (sources && sources.length > 0) {
                var sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'sources';
                sourcesDiv.innerHTML = '<strong>📎 Referenced Projects:</strong><br>';
                for (var i = 0; i < sources.length; i++) {
                    var source = sources[i];
                    var status = source.metadata ? source.metadata.status : 'Unknown';
                    sourcesDiv.innerHTML += '<div class="source-item">• ' + source.project_id + ' - ' + status + '</div>';
                }
                messageDiv.appendChild(sourcesDiv);
            }
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Show typing indicator
        function showTyping() {
            // Remove existing typing indicator
            removeTyping();
            
            var typingDiv = document.createElement('div');
            typingDiv.className = 'message assistant';
            typingDiv.id = 'typingIndicator';
            
            var bubble = document.createElement('div');
            bubble.className = 'bubble';
            bubble.innerHTML = '<div style="display: inline-block;"><span style="display: inline-block; width: 8px; height: 8px; background: #667eea; border-radius: 50%; margin: 0 3px; animation: typing 1.4s infinite;"></span><span style="display: inline-block; width: 8px; height: 8px; background: #667eea; border-radius: 50%; margin: 0 3px; animation: typing 1.4s infinite; animation-delay: 0.2s;"></span><span style="display: inline-block; width: 8px; height: 8px; background: #667eea; border-radius: 50%; margin: 0 3px; animation: typing 1.4s infinite; animation-delay: 0.4s;"></span></div><span style="margin-left: 10px; color: #7f8c8d;">Thinking...</span>';
            
            typingDiv.appendChild(bubble);
            chatContainer.appendChild(typingDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Remove typing indicator
        function removeTyping() {
            var typing = document.getElementById('typingIndicator');
            if (typing) {
                typing.remove();
            }
        }
        
        // Send question to backend
        async function sendQuestion() {
            var question = questionInput.value.trim();
            if (!question) return;
            
            // Check if it's a reload command
            if (question.toLowerCase() === 'reload data from excel file') {
                await reloadData();
                return;
            }
            
            // Disable input
            questionInput.disabled = true;
            sendButton.disabled = true;
            questionInput.style.opacity = '0.6';
            
            // Add user message
            addMessage(question, 'user', null);
            questionInput.value = '';
            
            // Show typing indicator
            showTyping();
            
            try {
                // Send to API
                var response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question: question })
                });
                
                // Remove typing indicator
                removeTyping();
                
                if (!response.ok) {
                    var errorData = await response.json();
                    throw new Error(errorData.error || 'Server error');
                }
                
                var data = await response.json();
                
                // Check if there was an error in the response
                if (data.error) {
                    addMessage('❌ ' + data.error, 'assistant', null);
                } else {
                    // Add assistant response
                    addMessage(data.response || 'No response generated', 'assistant', data.relevant_docs);
                }
                
            } catch (error) {
                removeTyping();
                addMessage('❌ Error: ' + error.message + '. Please check the server console for details.', 'assistant', null);
                console.error('Error:', error);
            }
            
            // Enable input
            questionInput.disabled = false;
            sendButton.disabled = false;
            questionInput.style.opacity = '1';
            questionInput.focus();
        }
        
        // Reload data from Excel file
        async function reloadData() {
            addMessage('🔄 Reloading data from Excel file...', 'user', null);
            
            try {
                var response = await fetch('/api/reload', {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    var errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to reload');
                }
                
                var data = await response.json();
                addMessage('✅ ' + data.message, 'assistant', null);
                
                // Update stats
                loadStats();
                
            } catch (error) {
                addMessage('❌ Error reloading data: ' + error.message, 'assistant', null);
            }
        }
        
        // Handle Enter key
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                sendQuestion();
            }
        }
        
        // Quick question button
        function askQuestion(question) {
            questionInput.value = question;
            sendQuestion();
        }
        
        // Auto-focus input on load
        window.onload = function() {
            questionInput.focus();
        };
    </script>
</body>
</html>
"""

# ==================== ROUTES ====================

@app.route('/')
def home():
    """Render the main page"""
    # Get file modification time
    last_updated = "Unknown"
    if os.path.exists(rag.data_file_path):
        mod_time = os.path.getmtime(rag.data_file_path)
        last_updated = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template_string(
        HTML_TEMPLATE,
        data_file=rag.data_file_path,
        last_updated=last_updated
    )

@app.route('/api/query', methods=['POST'])
def api_query():
    """API endpoint for queries"""
    try:
        data = request.json
        question = data.get('question', '')
        
        # Check for reload command
        if question.lower() == 'reload data from excel file':
            return jsonify({'message': 'Use /api/reload endpoint'})
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        result = rag.query(question)
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get project statistics"""
    try:
        if rag.projects_df is None:
            return jsonify({'error': 'No data loaded'}), 404
        
        stats = rag.show_project_stats()
        return jsonify(stats)
        
    except Exception as e:
        print(f"❌ Stats Error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reload', methods=['POST'])
def api_reload():
    """Reload data from Excel file"""
    try:
        if rag.load_data_from_file():
            rag.index_projects()
            return jsonify({'message': 'Data reloaded successfully from Excel file!'})
        else:
            return jsonify({'error': 'Failed to reload data'}), 400
    except Exception as e:
        print(f"❌ Reload Error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌐 AEC-RAG Web Interface")
    print("="*60)
    print(f"📍 URL: http://localhost:5000")
    print(f"📁 Data File: {rag.data_file_path}")
    print(f"📊 Projects: {len(rag.projects_df) if rag.projects_df is not None else 0}")
    print("="*60)
    print("\n🚀 Starting web server...")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)