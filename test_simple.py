#!/usr/bin/env python3
"""
Simple Pinecone connection test
"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
load_dotenv()

def test_pinecone_basic():
    """Test basic Pinecone connection without search"""
    print("🔍 Testing Basic Pinecone Connection...")
    
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ PINECONE_API_KEY not found")
        return
    
    try:
        # Initialize Pinecone (v6.0.0 style)
        pc = Pinecone(api_key=api_key)
        print("✅ Pinecone initialized successfully")
        
        # List indexes
        indexes = pc.list_indexes()
        index_names = [idx.name for idx in indexes]
        print(f"📋 Available indexes: {index_names}")
        
        # Check if our indexes exist
        education_exists = "aido-v2-index" in index_names
        travel_exists = "travel-guide" in index_names
        
        print(f"📚 Education index exists: {education_exists}")
        print(f"✈️ Travel index exists: {travel_exists}")
        
        if education_exists:
            # Get index stats
            index = pc.Index("aido-v2-index")
            stats = index.describe_index_stats()
            print(f"📊 Education index stats: {stats}")
        
        if travel_exists:
            # Get index stats
            index = pc.Index("travel-guide")
            stats = index.describe_index_stats()
            print(f"📊 Travel index stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Simple Pinecone Test")
    print("=" * 30)
    test_pinecone_basic()
