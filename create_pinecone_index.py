#!/usr/bin/env python3
"""
Script to create the user-knowledge-base Pinecone index for Dilan AI
"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# Load environment variables
load_dotenv()

def create_user_knowledge_index():
    """Create the user-knowledge-base index in Pinecone"""
    
    # Get API key
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ PINECONE_API_KEY not found in .env file")
        print("Please add your Pinecone API key to the .env file:")
        print("PINECONE_API_KEY=your_api_key_here")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        
        # Index configuration
        index_name = "user-knowledge-base"
        dimension = 3072  # text-embedding-3-large dimensions
        
        # Check if index already exists
        existing_indexes = pc.list_indexes()
        index_names = [index.name for index in existing_indexes]
        
        if index_name in index_names:
            print(f"✅ Index '{index_name}' already exists!")
            return True
        
        print(f"🔨 Creating index '{index_name}'...")
        print(f"   Dimensions: {dimension}")
        print(f"   Metric: cosine")
        print(f"   Cloud: AWS")
        print(f"   Region: us-east-1")
        
        # Create the index
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        
        print(f"✅ Successfully created index '{index_name}'!")
        print("🎉 Your Dilan AI backend can now store and search user knowledge!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating index: {str(e)}")
        return False

def list_indexes():
    """List all existing Pinecone indexes"""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ PINECONE_API_KEY not found")
        return
    
    try:
        pc = Pinecone(api_key=api_key)
        indexes = pc.list_indexes()
        
        print("\n📋 Existing Pinecone Indexes:")
        if not indexes:
            print("   No indexes found")
        else:
            for index in indexes:
                print(f"   • {index.name} ({index.dimension} dimensions)")
        
    except Exception as e:
        print(f"❌ Error listing indexes: {str(e)}")

if __name__ == "__main__":
    print("🚀 Dilan AI - Pinecone Index Creator")
    print("=" * 50)
    
    # List existing indexes first
    list_indexes()
    
    # Create the user knowledge base index
    print("\n🔨 Creating User Knowledge Base Index...")
    success = create_user_knowledge_index()
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Restart your backend server")
        print("2. Upload documents through the knowledge base API")
        print("3. Your AI experts will be able to search uploaded documents!")
    else:
        print("\n❌ Index creation failed. Please check your Pinecone API key and try again.")
    
    print("\n✅ Script completed!")
