import pandas as pd          # For handling project data in tables
import ollama               # For AI models (embeddings + text generation)
import chromadb             # For storing and searching vectors
from chromadb.config import Settings
import json                 # For handling data formats
import random               # For generating sample data
from datetime import datetime, timedelta  # For date handling
import time                 # For timing operations


class AECRAG:
    """AEC-RAG: Simple Project Management RAG System"""
    
    def __init__(self):
        """Initialize the RAG system"""
        print("🚀 Initializing AEC-RAG System...")
        
        # Initialize ChromaDB client with in-memory storage
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=None  # In-memory mode
        ))

        # Create or get collection for project data
        self.collection = self.client.get_or_create_collection(
            name="project_data",
            metadata={"hnsw:space": "cosine"}
        )

        # Store project data for reference
        self.projects_df = None
        
        print("✅ AEC-RAG initialized successfully!")

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