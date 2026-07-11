# aec_rag_web.py - Complete Web Interface for AEC-RAG

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import os
import sys
from datetime import datetime
import pandas as pd
import ollama
import chromadb
import random
from datetime import datetime, timedelta
import time
import subprocess

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for API access

# AEC-RAG System Class (Same as CLI version)
class AECRAG:
    def __init__(self, data_file_path=None):
        print("🚀 Initializing AEC-RAG Web System...")
        
        if data_file_path is None:
            self.data_file_path = "C:/AEC_Projects/project_data.xlsx"
        else:
            self.data_file_path = data_file_path
        
        self.embedding_model = "nomic-embed-text"
        self.chat_model = "llama3.2:latest"
        
        # Check Ollama connection
        self.check_ollama_connection()
        
        # Initialize ChromaDB
        self.client = chromadb.EphemeralClient()
        self.collection = self.client.get_or_create_collection(
            name="project_data",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.projects_df = None
        print(f"✅ AEC-RAG Web initialized! Data source: {self.data_file_path}")
    
    def check_ollama_connection(self):
        """Check if Ollama is running"""
        try:
            ollama.list()
            print("✅ Ollama is running")
        except Exception as e:
            print(f"❌ Ollama connection error: {e}")
            print("📌 Starting Ollama service...")
            # Try to start Ollama
            try:
                subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)
            except:
                pass
    
    def load_data_from_file(self):
        """Load data from file"""
        print(f"📂 Loading data from: {self.data_file_path}")
        
        if not os.path.exists(self.data_file_path):
            print("❌ File not found. Creating template...")
            self.create_template_file()
            return False
        
        try:
            file_ext = os.path.splitext(self.data_file_path)[1].lower()
            
            if file_ext in ['.xlsx', '.xls']:
                self.projects_df = pd.read_excel(self.data_file_path)
                print(f"✅ Loaded Excel with {len(self.projects_df)} records")
            elif file_ext == '.csv':
                self.projects_df = pd.read_csv(self.data_file_path)
                print(f"✅ Loaded CSV with {len(self.projects_df)} records")
            else:
                print(f"❌ Unsupported file type: {file_ext}")
                return False
            
            if self.validate_data():
                print("✅ Data validation passed!")
                return True
            return False
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return False
    
    def create_template_file(self):
        """Create template file"""
        print("📝 Creating template file...")
        sample_data = self.generate_sample_data(100)
        os.makedirs(os.path.dirname(self.data_file_path), exist_ok=True)
        sample_data.to_excel(self.data_file_path, index=False)
        print(f"✅ Template created at: {self.data_file_path}")
        self.projects_df = sample_data
        return True
    
    def generate_sample_data(self, num_projects=100):
        """Generate sample data"""
        projects = []
        statuses = ['Planning', 'In Progress', 'Review', 'Completed', 'On Hold']
        departments = ['Engineering', 'Construction', 'Design', 'Management', 'Safety']
        
        for i in range(1, num_projects + 1):
            start_date = datetime.now() - timedelta(days=random.randint(0, 730))
            end_date = start_date + timedelta(days=random.randint(30, 365))
            
            project = {
                'project_id': f'PRJ-{i:04d}',
                'project_name': f'Project {i}',
                'status': random.choice(statuses),
                'department': random.choice(departments),
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'budget': round(random.uniform(50000, 5000000), 2),
                'actual_cost': round(random.uniform(30000, 4500000), 2),
                'completion_percentage': random.randint(0, 100),
                'project_manager': f'Manager {chr(65 + random.randint(0, 25))}{random.randint(1, 20)}',
                'priority': random.choice(['Low', 'Medium', 'High', 'Critical']),
                'description': f"Sample project {i}",
                'cost_variance': 0
            }
            project['cost_variance'] = round(project['actual_cost'] - project['budget'], 2)
            projects.append(project)
        
        return pd.DataFrame(projects)
    
    def validate_data(self):
        """Validate data structure"""
        required = ['project_id', 'project_name', 'status', 'budget', 'actual_cost', 'completion_percentage']
        missing = [col for col in required if col not in self.projects_df.columns]
        if missing:
            print(f"❌ Missing columns: {missing}")
            return False
        return True
    
    def prepare_documents(self):
        """Prepare documents for indexing"""
        documents = []
        metadatas = []
        ids = []
        
        for idx, row in self.projects_df.iterrows():
            doc_text = f"""
            Project ID: {row.get('project_id', 'N/A')}
            Project Name: {row.get('project_name', 'N/A')}
            Status: {row.get('status', 'N/A')}
            Department: {row.get('department', 'N/A')}
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
        
        return documents, metadatas, ids
    
    def generate_embeddings(self, texts):
        """Generate embeddings"""
        embeddings = []
        for i, text in enumerate(texts):
            try:
                response = ollama.embeddings(
                    model=self.embedding_model,
                    prompt=text
                )
                embeddings.append(response['embedding'])
            except Exception as e:
                print(f"⚠️ Error generating embedding: {e}")
                embeddings.append([0.0] * 768)
        return embeddings
    
    def index_projects(self):
        """Index projects in vector database"""
        print("📚 Indexing projects...")
        
        documents, metadatas, ids = self.prepare_documents()
        embeddings = self.generate_embeddings(documents)
        
        # Clear existing data
        try:
            existing = self.collection.get()
            if existing and existing['ids']:
                self.collection.delete(ids=existing['ids'])
        except:
            pass
        
        # Add to database
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"✅ Indexed {len(documents)} projects")
    
    def query(self, question, n_results=3):
        """Query the system"""
        print(f"🔍 Query: {question}")
        
        try:
            # Generate embedding
            query_embedding = ollama.embeddings(
                model=self.embedding_model,
                prompt=question
            )['embedding']
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Extract results
            relevant_docs = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    relevant_docs.append({
                        'project_id': results['ids'][0][i],
                        'content': doc,
                        'metadata': results['metadatas'][0][i]
                    })
            
            # Generate response
            response = self.generate_response(question, relevant_docs)
            
            return {
                'question': question,
                'response': response,
                'relevant_docs': relevant_docs,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'question': question,
                'response': f"Error: {str(e)}",
                'relevant_docs': [],
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_response(self, question, relevant_docs):
        """Generate response using Ollama"""
        if not relevant_docs:
            return "No relevant projects found for your question."
        
        context = "Here are the relevant projects:\n\n"
        for i, doc in enumerate(relevant_docs, 1):
            context += f"Project {i}:\n{doc['content']}\n\n"
        
        prompt = f"""You are AEC-RAG, an AI assistant for project managers.

Question: {question}

Based on this project information:
{context}

Provide a clear, professional answer based ONLY on the project data above.

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

# Initialize the RAG system
print("🏗️ Starting AEC-RAG Web Interface...")
rag = AECRAG()

# Load and index data
if not rag.load_data_from_file():
    print("❌ Could not load data")
    sys.exit(1)

rag.index_projects()
print("✅ System ready!")

# ===================== HTML TEMPLATE =====================
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
        
        .message .metadata {
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 5px;
        }
        
        .message .sources {
            margin-top: 10px;
            font-size: 13px;
            background: #ecf0f1;
            padding: 10px 15px;
            border-radius: 10px;
            display: inline-block;
        }
        
        .message .sources strong {
            color: #2c3e50;
        }
        
        .message .sources .source-item {
            color: #3498db;
            margin: 3px 0;
        }
        
        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
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
            display: none;
        }
        
        .typing-indicator.active {
            display: inline-block;
        }
        
        .typing-indicator span {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #667eea;
            border-radius: 50%;
            margin: 0 3px;
            animation: typing 1.4s infinite;
        }
        
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-10px);
            }
        }
        
        .stats-bar {
            background: #ecf0f1;
            padding: 8px 20px;
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #7f8c8d;
            border-top: 1px solid #ddd;
        }
        
        /* Scrollbar Styling */
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
        
        /* Loading animation for response */
        .loading-dots {
            display: inline-block;
        }
        
        .loading-dots span {
            display: inline-block;
            width: 6px;
            height: 6px;
            background: #667eea;
            border-radius: 50%;
            margin: 0 2px;
            animation: dotPulse 1.4s infinite;
        }
        
        .loading-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .loading-dots span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes dotPulse {
            0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
            40% { transform: scale(1.2); opacity: 1; }
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
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🏗️ AEC-<span>RAG</span></h1>
            <div class="header-info">
                <span class="badge">📊 {{ total_projects }} Projects</span>
                <span class="badge">🤖 {{ model_name }}</span>
                <span class="badge">🟢 Online</span>
            </div>
        </div>
        
        <!-- Chat Container -->
        <div class="chat-container" id="chatContainer">
            <!-- Welcome Message -->
            <div class="message assistant">
                <div class="bubble">
                    <strong>👋 Welcome to AEC-RAG!</strong><br><br>
                    I'm your project management assistant. I can help you query your project data using natural language.<br><br>
                    <strong>Try asking me:</strong><br>
                    • What projects are over budget?<br>
                    • Show me high priority projects<br>
                    • What is the total budget?<br>
                    • Which projects are behind schedule?
                </div>
            </div>
        </div>
        
        <!-- Quick Questions -->
        <div class="quick-questions">
            <button onclick="askQuestion('What projects are over budget?')">💰 Over Budget</button>
            <button onclick="askQuestion('Show me high priority projects')">⚡ High Priority</button>
            <button onclick="askQuestion('What is the total budget?')">📊 Total Budget</button>
            <button onclick="askQuestion('Which projects are behind schedule?')">📅 Behind Schedule</button>
            <button onclick="askQuestion('Show me completed projects')">✅ Completed</button>
        </div>
        
        <!-- Stats Bar -->
        <div class="stats-bar">
            <span>💬 Ask any question about your projects</span>
            <span>⚡ Fast responses • 🔒 Private • 🏠 Local</span>
        </div>
        
        <!-- Input Area -->
        <div class="input-container">
            <input type="text" id="questionInput" placeholder="Ask about your projects..." onkeypress="handleKeyPress(event)">
            <button id="sendButton" onclick="sendQuestion()">Send 🚀</button>
        </div>
    </div>
    
    <script>
        // Get elements
        const chatContainer = document.getElementById('chatContainer');
        const questionInput = document.getElementById('questionInput');
        const sendButton = document.getElementById('sendButton');
        
        // Add a message to the chat
        function addMessage(text, sender, sources = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const bubble = document.createElement('div');
            bubble.className = 'bubble';
            
            // Format text with line breaks
            const formattedText = text.replace(/\n/g, '<br>');
            bubble.innerHTML = formattedText;
            
            messageDiv.appendChild(bubble);
            
            // Add sources if available
            if (sources && sources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'sources';
                sourcesDiv.innerHTML = '<strong>📎 Referenced Projects:</strong><br>';
                sources.forEach(source => {
                    sourcesDiv.innerHTML += `<div class="source-item">• ${source.project_id} - ${source.metadata.status}</div>`;
                });
                messageDiv.appendChild(sourcesDiv);
            }
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Show typing indicator
        function showTyping() {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message assistant';
            typingDiv.id = 'typingIndicator';
            
            const bubble = document.createElement('div');
            bubble.className = 'bubble';
            bubble.innerHTML = `
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
            
            typingDiv.appendChild(bubble);
            chatContainer.appendChild(typingDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Remove typing indicator
        function removeTyping() {
            const typing = document.getElementById('typingIndicator');
            if (typing) {
                typing.remove();
            }
        }
        
        // Send question to backend
        async function sendQuestion() {
            const question = questionInput.value.trim();
            if (!question) return;
            
            // Disable input
            questionInput.disabled = true;
            sendButton.disabled = true;
            
            // Add user message
            addMessage(question, 'user');
            questionInput.value = '';
            
            // Show typing indicator
            showTyping();
            
            try {
                // Send to API
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question: question })
                });
                
                const data = await response.json();
                
                // Remove typing indicator
                removeTyping();
                
                // Add assistant response
                addMessage(data.response, 'assistant', data.relevant_docs);
                
            } catch (error) {
                removeTyping();
                addMessage(`❌ Error: ${error.message}`, 'assistant');
            }
            
            // Enable input
            questionInput.disabled = false;
            sendButton.disabled = false;
            questionInput.focus();
        }
        
        // Handle Enter key
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
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

# ===================== ROUTES =====================

@app.route('/')
def home():
    """Render the main page"""
    return render_template_string(
        HTML_TEMPLATE,
        total_projects=len(rag.projects_df) if rag.projects_df is not None else 0,
        model_name=rag.chat_model
    )

@app.route('/api/query', methods=['POST'])
def api_query():
    """API endpoint for queries"""
    try:
        data = request.json
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Process query
        result = rag.query(question)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get project statistics"""
    if rag.projects_df is None:
        return jsonify({'error': 'No data loaded'}), 404
    
    stats = {
        'total_projects': len(rag.projects_df),
        'status_distribution': rag.projects_df['status'].value_counts().to_dict(),
        'average_budget': rag.projects_df['budget'].mean(),
        'average_completion': rag.projects_df['completion_percentage'].mean(),
        'total_budget': rag.projects_df['budget'].sum(),
        'total_cost': rag.projects_df['actual_cost'].sum()
    }
    
    return jsonify(stats)

@app.route('/api/reload', methods=['POST'])
def api_reload():
    """Reload data from file"""
    try:
        if rag.load_data_from_file():
            rag.index_projects()
            return jsonify({'message': 'Data reloaded successfully'})
        else:
            return jsonify({'error': 'Failed to reload data'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===================== MAIN =====================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌐 AEC-RAG Web Interface")
    print("="*60)
    print("📍 URL: http://localhost:5000")
    print("📁 Data: " + rag.data_file_path)
    print("📊 Projects: " + str(len(rag.projects_df)))
    print("="*60)
    print("\n🚀 Starting web server...")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)