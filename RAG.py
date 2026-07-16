import sys
from flask import Flask, request, jsonify, render_template_string
import pandas as pd
from flask_cors import CORS
import ollama
import chromadb
import os
from datetime import datetime,timedelta
import time
import random
import subprocess
import traceback
app = Flask(__name__)
CORS(app)
# ---------------------------------------------------------
# 1. Initialize ChromaDB (Vector Database)
# ---------------------------------------------------------
# We use an ephemeral client here for testing. 
# Use chromadb.PersistentClient(path="./db") to save data to disk.
chroma_client = chromadb.Client()

collection=chroma_client.create_collection(name="excel_rag_collection")
# Define the local LLM model you are using with Ollama
LLM_MODEL = "llama3.2"
# ---------------------------------------------------------
# 2. Basic Frontend (Optional but helpful for testing)
# ---------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Excel RAG with Ollama</title>
    <style>body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }</style>
</head>
<body>
    <h2>1. Upload Excel Sheet</h2>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept=".xlsx, .xls">
        <button type="submit">Ingest Data</button>
    </form>

    <h2>2. Ask a Question</h2>
    <form id="askForm">
        <input type="text" id="query" placeholder="e.g., What is the total revenue?" style="width: 80%;">
        <button type="submit">Ask</button>
    </form>
    <h3>Answer:</h3>
    <p id="answer" style="white-space: pre-wrap; background: #f4f4f4; padding: 15px; border-radius: 5px;"></p>

    <script>
        document.getElementById('askForm').onsubmit = async function(e) {
            e.preventDefault();
            const query = document.getElementById('query').value;
            document.getElementById('answer').innerText = "Thinking...";
            
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });
            const data = await response.json();
            document.getElementById('answer').innerText = data.answer || data.error;
        };
    </script>
</body>
</html>
"""
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

# ---------------------------------------------------------
# 3. Ingestion Endpoint: Parse Excel to Vector DB
# ---------------------------------------------------------
@app.route('/upload', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400    
    try:
        # Read the excel dynamically into a pandas
        df = pd.read_excel(file)
        # clean the data 
        df=df.fillna('n/a')  # Fill NaN with empty string
        documents = []
        metadata = []
        ids = []
        #convert each row to a string and store it in the vector database
        for index,row in df.iterrows():
            # create string for columns
            row_text = " | ".join([f"{col}: {row[col]}" for col,val in row.items()])
            documents.append(row_text)
            #store metadata 
            metadata.append({"row_index": index,"source_file": file.filename})
            ids.append(f"doc_{index}_{int(time.time())}")      # Unique ID
        # clear old data
        if collection.count()>0:
            existing_ids = collection.get()['ids']
            collection.delete(ids=existing_ids)
        #add to chromdb
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadata,
                ids=ids
            )
        return f"Successfully ingested {len(documents)} rows from {file.filename}. Go back and ask a question!"
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500    
    

    # ---------------------------------------------------------
# 4. Query Endpoint: Retrieve & Generate (RAG)
# ---------------------------------------------------------
@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    query = data.get('query', '')
    if not query:
        return jsonify({"error": "Query is required"}), 400
    if collection.count() == 0:
        return jsonify({"error": "No data found. Please upload an Excel sheet first."}), 400
    try:
        # Step 1: Retrieve the top 5 most relevant rows from ChromaDB based on the user's query
        results = collection.query(
            query_texts=[query],
            n_results=5 
        )
        retrieved_docs = results['documents'][0]
        context = "\n".join(retrieved_docs)
        # Step 2: Build the prompt combining context and the user query
        prompt = f"""
        You are an expert data analyst assistant. Answer the user's question using ONLY the provided Context Data retrieved from an Excel spreadsheet. 
        If the answer is not contained within the Context Data, reply explicitly with: "I cannot answer this based on the provided spreadsheet."
        Context Data (Relevant Excel Rows):
        {context}
        Question:
        {query}
        """
        # Step 3: Pass the prompt to local Ollama
        response = ollama.chat(model=LLM_MODEL, messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ])
        answer = response['message']['content']
        return jsonify({
            "answer": answer,
            "context_used": retrieved_docs
        })
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500
if __name__ == '__main__':
    # Run the Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)