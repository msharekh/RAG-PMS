# aec_rag_web.py - Simple Web Interface for AEC-RAG

from flask import Flask, request, jsonify, render_template_string
import json
from aec_rag import AECRAG

app = Flask(__name__)
rag = AECRAG()

# Initialize with sample data
rag.generate_sample_data(100)
rag.index_projects()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AEC-RAG - Project Management Assistant</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 10px; }
        h1 { color: #2c3e50; }
        input[type="text"] { width: 70%; padding: 10px; margin: 10px 0; }
        button { padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .response { background: white; padding: 20px; border-radius: 5px; margin-top: 20px; }
        .loading { color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏗️ AEC-RAG</h1>
        <p>Project Management Assistant for Architecture, Engineering, and Construction</p>
        
        <form id="queryForm">
            <input type="text" id="question" placeholder="Ask about your projects..." required>
            <button type="submit">Ask</button>
        </form>
        
        <div id="response" class="response" style="display:none;">
            <h3>Response:</h3>
            <div id="answer"></div>
            <hr>
            <div id="sources"></div>
        </div>
    </div>
    
    <script>
        document.getElementById('queryForm').onsubmit = async function(e) {
            e.preventDefault();
            const question = document.getElementById('question').value;
            const responseDiv = document.getElementById('response');
            const answerDiv = document.getElementById('answer');
            const sourcesDiv = document.getElementById('sources');
            
            responseDiv.style.display = 'block';
            answerDiv.innerHTML = '<div class="loading">⏳ Processing your question...</div>';
            sourcesDiv.innerHTML = '';
            
            try {
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: question})
                });
                
                const data = await response.json();
                answerDiv.innerHTML = data.response.replace(/\n/g, '<br>');
                
                if (data.relevant_docs && data.relevant_docs.length > 0) {
                    sourcesDiv.innerHTML = '<h4>📎 Sources:</h4>';
                    data.relevant_docs.forEach(doc => {
                        sourcesDiv.innerHTML += `<p>• ${doc.project_id}: ${doc.metadata.status}</p>`;
                    });
                }
            } catch (error) {
                answerDiv.innerHTML = '❌ Error: ' + error.message;
            }
        };
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/query', methods=['POST'])
def query():
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    result = rag.query(question)
    return jsonify(result)

if __name__ == '__main__':
    print("🏗️ Starting AEC-RAG Web Interface...")
    app.run(debug=True, port=5000)