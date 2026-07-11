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

