import os
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import numpy as np

class KnowledgeBase:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Create or get collection
        try:
            self.collection = self.client.get_collection("knowledge_base")
            print("Loaded existing knowledge base")
        except:
            self.collection = self.client.create_collection(
                name="knowledge_base",
                metadata={"description": "RAG Knowledge Base"}
            )
            print("Created new knowledge base")
    
    def add_documents(self, documents: List[Dict[str, str]]):
        """Add documents to the knowledge base"""
        texts = [doc["text"] for doc in documents]
        embeddings = self.embedding_model.encode(texts).tolist()
        ids = [f"doc_{i}" for i in range(len(documents))]
        
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=[{"source": doc.get("source", "unknown")} for doc in documents],
            ids=ids
        )
        print(f"Added {len(documents)} documents to knowledge base")
    
    def search(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        documents = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                documents.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0
                })
        
        return documents
    
    def load_sample_data(self):
        """Load sample knowledge base data"""
        sample_docs = [
            {
                "text": """Renewable energy sources like solar, wind, and hydroelectric power offer numerous benefits including reduced greenhouse gas emissions, energy independence, and long-term cost savings. Solar energy harnesses sunlight through photovoltaic panels, while wind energy uses turbines to convert wind motion into electricity. Hydroelectric power generates electricity from flowing water. These sources are sustainable and have minimal environmental impact compared to fossil fuels.""",
                "source": "renewable_energy"
            },
            {
                "text": """Climate change refers to long-term shifts in temperatures and weather patterns. Human activities, particularly burning fossil fuels like coal, oil, and gas, have been the main driver of climate change since the 1800s. The consequences include rising sea levels, more extreme weather events, and biodiversity loss. Mitigation strategies include transitioning to renewable energy, improving energy efficiency, and adopting sustainable agricultural practices.""",
                "source": "climate_change"
            },
            {
                "text": """Sustainability means meeting our own needs without compromising the ability of future generations to meet theirs. It has three pillars: environmental, social, and economic. Environmental sustainability involves reducing carbon footprint, conserving resources, and protecting ecosystems. Social sustainability focuses on human rights, labor rights, and community development. Economic sustainability involves creating long-term economic value without negative social or environmental impacts.""",
                "source": "sustainability"
            },
            {
                "text": """Solar power installation costs have decreased by over 80% in the past decade, making it increasingly competitive with traditional energy sources. The levelized cost of electricity from solar photovoltaics is now lower than fossil fuels in many regions. Government incentives and technological advancements continue to drive adoption of solar energy worldwide.""",
                "source": "solar_energy"
            },
            {
                "text": """Wind energy capacity has grown exponentially globally, with offshore wind farms becoming increasingly common. Modern wind turbines can generate enough electricity to power hundreds of homes. Wind power is now one of the cheapest energy sources in many markets and creates numerous jobs in manufacturing, installation, and maintenance.""",
                "source": "wind_energy"
            }
        ]
        
        self.add_documents(sample_docs)
        print("Sample knowledge base loaded successfully")

if __name__ == "__main__":
    kb = KnowledgeBase()
    kb.load_sample_data()