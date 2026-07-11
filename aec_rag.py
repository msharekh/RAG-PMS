import pandas as pd          # For handling project data in tables
import ollama               # For AI models (embeddings + text generation)
import chromadb             # For storing and searching vectors
from chromadb.config import Settings
import json                 # For handling data formats
import random               # For generating sample data
from datetime import datetime, timedelta  # For date handling
import time                 # For timing operations

import os
import sys
import subprocess



class AECRAG:
    """AEC-RAG: Simple Project Management RAG System"""
    
    def __init__(self):
        """Initialize the RAG system"""
        print("🚀 Initializing AEC-RAG System...")
        
        # # Initialize ChromaDB client with in-memory storage
        # self.client = chromadb.Client(Settings(
        #     chroma_db_impl="duckdb+parquet",
        #     persist_directory=None  # In-memory mode
        # ))
         # Initialize ChromaDB client with in-memory storage (FIXED)
        # Using ephemeral (in-memory) client to avoid persist_directory issues
        self.client = chromadb.EphemeralClient()

        # Create or get collection for project data
        self.collection = self.client.get_or_create_collection(
            name="project_data",
            metadata={"hnsw:space": "cosine"}
        )

        # Store project data for reference
        self.projects_df = None
        
        print("✅ AEC-RAG initialized successfully!")
        
        
        
    def ensure_models_available(self):
        """
        Check if required Ollama models are available, pull if not
        """
        print("🔍 Checking Ollama models...")
        
        try:
            # Get list of installed models
            installed_models = self.get_installed_models()
            
            # Check embedding model
            if self.embedding_model not in installed_models:
                print(f"📦 Pulling embedding model: {self.embedding_model}...")
                self.pull_model(self.embedding_model)
            else:
                print(f"✅ Embedding model available: {self.embedding_model}")
            
            # Check chat model
            if self.chat_model not in installed_models:
                print(f"📦 Pulling chat model: {self.chat_model}...")
                self.pull_model(self.chat_model)
            else:
                print(f"✅ Chat model available: {self.chat_model}")
                
        except Exception as e:
            print(f"⚠️ Error checking models: {e}")
            print("📌 Please ensure Ollama is running and models are available")
            print("📌 You can manually pull models with:")
            print(f"    ollama pull {self.embedding_model}")
            print(f"    ollama pull {self.chat_model}")
    
    def get_installed_models(self):
        """
        Get list of installed Ollama models
        """
        try:
            # Use ollama list command
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse the output to get model names
                lines = result.stdout.strip().split('\n')
                models = []
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
            else:
                print(f"⚠️ Could not get model list: {result.stderr}")
                return []
        except Exception as e:
            print(f"⚠️ Error getting installed models: {e}")
            return []
    
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
                print(f"📌 Please manually pull with: ollama pull {model_name}")
                return False
                
        except Exception as e:
            print(f"❌ Error pulling {model_name}: {e}")
            print(f"📌 Please manually pull with: ollama pull {model_name}")
            return False

    def generate_sample_data(self, num_projects=100):
        
        """
        Generate sample project data with realistic values
        """
        print(f"📊 Generating {num_projects} sample projects...")
        
        projects = []
        statuses = ['Planning', 'In Progress', 'Review', 'Completed', 'On Hold']
        departments = ['Engineering', 'Construction', 'Design', 'Management', 'Safety']

        for i in range(1, num_projects + 1):
            # Generate random dates
            start_date = datetime.now() - timedelta(days=random.randint(0, 730))
            end_date = start_date + timedelta(days=random.randint(30, 365))


            project = {
                'project_id': f'PRJ-{i:04d}',
                'project_name': f'Project {i}: {random.choice(["Construction", "Development", "Renovation", "Infrastructure"])} {random.choice(["Phase", "Stage", "Component"])} {random.randint(1, 10)}',
                'status': random.choice(statuses),
                'department': random.choice(departments),
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'budget': round(random.uniform(50000, 5000000), 2),
                'actual_cost': round(random.uniform(30000, 4500000), 2),
                'completion_percentage': random.randint(0, 100),
                'project_manager': f'Manager {chr(65 + random.randint(0, 25))}{random.randint(1, 20)}',
                'priority': random.choice(['Low', 'Medium', 'High', 'Critical']),
                'description': f"This project involves {random.choice(['structural improvements', 'system upgrades', 'capacity expansion', 'safety enhancements'])} for {random.choice(['existing facilities', 'new construction', 'renovation work'])}.",
                'cost_variance': 0  # Will calculate below
            }

            # Calculate cost variance
            project['cost_variance'] = round(project['actual_cost'] - project['budget'], 2)
            projects.append(project)

            # Convert to DataFrame
            self.projects_df = pd.DataFrame(projects)
            print(f"✅ Generated {len(self.projects_df)} sample projects")
            return self.projects_df


    def prepare_documents(self):
            """
            Prepare documents from project data for embedding
            Each project becomes a searchable document
            """
            print("📝 Preparing documents for indexing...")
            
            documents = []
            metadatas = []
            ids = []
            
            for idx, row in self.projects_df.iterrows():
                # Create a comprehensive text description for each project
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
            
            print(f"✅ Prepared {len(documents)} documents")
            return documents, metadatas, ids

    def generate_embeddings(self, texts):
            """
            Generate embeddings using Ollama
            """
            print("🧠 Generating embeddings using Ollama...")
            embeddings = []
            
            for text in texts:
                try:
                    # Use Ollama to generate embeddings
                    response = ollama.embeddings(
                        model="nomic-embed-text",  # Good for embeddings
                        prompt=text
                    )
                    embeddings.append(response['embedding'])
                except Exception as e:
                    print(f"❌ Error generating embedding: {e}")
                    # Use fallback embedding
                    embeddings.append([0.0] * 768)  # Default dimension
            
            print(f"✅ Generated {len(embeddings)} embeddings")
            return embeddings

    def index_projects(self):
            """
            Main indexing function - prepare and store project data
            """
            print("📚 Indexing projects into vector database...")
            
            # Prepare documents
            documents, metadatas, ids = self.prepare_documents()
            
            # Generate embeddings
            embeddings = self.generate_embeddings(documents)
            
            # Add to ChromaDB
            try:
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
            query_embedding = ollama.embeddings(
                model="nomic-embed-text",
                prompt=question
            )['embedding']
            
            # Search for relevant documents
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Extract relevant documents and context
            relevant_docs = []
            for i, doc in enumerate(results['documents'][0]):
                relevant_docs.append({
                    'project_id': results['ids'][0][i],
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            # Generate response using Ollama
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
            return "No relevant project information found for your question."
        
        # Prepare context from relevant documents
        context = "Here are the relevant projects based on your query:\n\n"
        for i, doc in enumerate(relevant_docs, 1):
            context += f"Project {i}:\n{doc['content']}\n\n"
        
        # Create prompt for Ollama
        prompt = f"""You are AEC-RAG, an AI assistant for project managers in the Architecture, Engineering, and Construction industry.
        
Question: {question}

Based on the following project information, provide a detailed answer. Focus on project status, budget, costs, and timelines.

Context:
{context}

Please provide a professional and helpful response that directly answers the question. If there are multiple relevant projects, summarize the key information. If the question asks for specific metrics (like budget or completion status), provide those clearly.

Answer:"""
        
        try:
            # Generate response using Ollama
            response = ollama.chat(
                model="llama3.2",  # Use any model you have pulled
                messages=[
                    {"role": "system", "content": "You are a helpful project management assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response['message']['content']
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
        

        # fix unformated text .. please

    def run_cli(self):
        """
        Run the command-line interface for the RAG system
        """
        print("\n" + "="*60)
        print("🏗️  AEC-RAG - Project Management Assistant")
        print("="*60)
        print("Type 'exit' to quit, 'help' for assistance")
        print("Example questions:")
        print("- What is the status of all projects?")
        print("- Show me projects with budget over $1M")
        print("- Which projects are behind schedule?")
        print("- What's the total cost variance?")
        print("- Show me projects managed by Manager A")
        print("="*60 + "\n")
        
        while True:
            try:
                question = input("🔍 Ask about your projects: ").strip()
                
                if question.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye!")
                    break
                elif question.lower() in ['help', '?']:
                    print("\n📌 Help:")
                    print("  - Ask questions about project status, budget, costs")
                    print("  - Be specific for better results")
                    print("  - The system will search 100 projects for answers")
                    print("  - Type 'exit' to quit\n")
                    continue
                elif not question:
                    continue
                
                # Process the query
                start_time = time.time()
                result = self.query(question)
                elapsed_time = time.time() - start_time
                
                # Display results
                print("\n" + "="*60)
                print("📋 Response: (Generated in {:.2f}s)".format(elapsed_time))
                print("="*60)
                print(result['response'])
                
                # Show relevant projects referenced
                if result['relevant_docs']:
                    print("\n📎 Referenced Projects:")
                    for doc in result['relevant_docs']:
                        print(f"  • {doc['project_id']} - {doc['metadata'].get('status', 'Status unknown')}")
                
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
    print("🏗️  AEC-RAG v1.0 Setup")
    print("="*60)
    
    # Initialize the RAG system
    rag = AECRAG()
    
    # Generate sample data
    rag.generate_sample_data(100)
    
    # Index projects
    rag.index_projects()
    
    # Start CLI interface
    rag.run_cli()

if __name__ == "__main__":
    main()