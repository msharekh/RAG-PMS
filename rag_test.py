# aec_rag_file.py - AEC-RAG with Correct Model Names

import pandas as pd
import ollama
import chromadb
import os
from datetime import datetime, timedelta
import time
import random
import sys
import subprocess

class AECRAG:
    """
    AEC-RAG: Project Management RAG System
    Loads data from a file on C drive each time it runs
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
        # Alternative: use "llama3.2:3b" for smaller size
        
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
        Load project data from file on C drive
        """
        print(f"📂 Loading data from: {self.data_file_path}")
        
        if not os.path.exists(self.data_file_path):
            print(f"❌ File not found: {self.data_file_path}")
            print("📝 Creating sample data file as template...")
            self.create_template_file()
            return False
        
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
            return False
    
    def create_template_file(self):
        """
        Create a template Excel file with sample data
        """
        print("📝 Creating template file with sample data...")
        
        sample_data = self.generate_sample_data(100)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.data_file_path), exist_ok=True)
        sample_data.to_excel(self.data_file_path, index=False)
        
        print(f"✅ Template file created at: {self.data_file_path}")
        print("📌 Please update this file with your actual project data")
        
        self.projects_df = sample_data
        return True
    
    def generate_sample_data(self, num_projects=100):
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
                'description': f"This project involves {random.choice(['structural improvements', 'system upgrades', 'capacity expansion', 'safety enhancements'])}."
            }
            
            project['cost_variance'] = round(project['actual_cost'] - project['budget'], 2)
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
            print("📊 No project data available")
            return
        
        print("\n" + "="*60)
        print("📊 Project Statistics")
        print("="*60)
        print(f"Total Projects: {len(self.projects_df)}")
        print(f"Status Distribution:")
        for status, count in self.projects_df['status'].value_counts().items():
            print(f"  • {status}: {count}")
        print(f"Average Budget: ${self.projects_df['budget'].mean():,.2f}")
        print(f"Average Completion: {self.projects_df['completion_percentage'].mean():.1f}%")
        print("="*60 + "\n")
    
    def run_cli(self):
        """
        Run the command-line interface
        """
        print("\n" + "="*60)
        print("🏗️  AEC-RAG - Project Management Assistant")
        print("="*60)
        print(f"📁 Data Source: {self.data_file_path}")
        print(f"📊 Total Projects: {len(self.projects_df) if self.projects_df is not None else 0}")
        print(f"🤖 Models: {self.embedding_model} + {self.chat_model}")
        print("="*60)
        print("Commands:")
        print("  • Ask any question about your projects")
        print("  • 'stats' - Show project statistics")
        print("  • 'reload' - Reload data from file")
        print("  • 'help' - Show this help")
        print("  • 'exit' - Quit")
        print("="*60)
        print("\nExample questions:")
        print("  • What is the status of all projects?")
        print("  • Show me projects with budget over $1M")
        print("  • Which projects are behind schedule?")
        print("="*60 + "\n")
        
        while True:
            try:
                question = input("🔍 Ask: ").strip()
                
                if question.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye!")
                    break
                elif question.lower() in ['help', '?']:
                    print("\n📌 Commands:")
                    print("  - Ask any question about your projects")
                    print("  - Type 'stats' for project statistics")
                    print("  - Type 'reload' to refresh data from file")
                    print("  - Type 'exit' to quit\n")
                    continue
                elif question.lower() in ['stats']:
                    self.show_project_stats()
                    continue
                elif question.lower() in ['reload', 'refresh']:
                    print("🔄 Reloading data from file...")
                    if self.load_data_from_file():
                        self.index_projects()
                        print("✅ Data reloaded successfully!")
                    continue
                elif not question:
                    continue
                
                start_time = time.time()
                result = self.query(question)
                elapsed_time = time.time() - start_time
                
                print("\n" + "="*60)
                print(f"📋 Response: (Generated in {elapsed_time:.2f}s)")
                print("="*60)
                print(result['response'])
                
                if result['relevant_docs']:
                    print("\n📎 Referenced Projects:")
                    for doc in result['relevant_docs']:
                        status = doc['metadata'].get('status', 'Status unknown')
                        print(f"  • {doc['project_id']} - {status}")
                
                print("\n" + "-"*60 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")

def main():
    """
    Main function to run the AEC-RAG system
    """
    print("🏗️  AEC-RAG v1.0 - File-Based Data Loading")
    print("="*60)
    
    # You can change this path to your Excel file
    data_file = "C:/AEC_Projects/project_data.xlsx"
    
    rag = AECRAG(data_file)
    
    if not rag.load_data_from_file():
        print("❌ Failed to load data.")
        print("📌 A template file has been created at:", data_file)
        print("📌 Please update it with your project data and run again.")
        return
    
    rag.index_projects()
    rag.run_cli()

if __name__ == "__main__":
    main()