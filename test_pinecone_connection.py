#!/usr/bin/env python3
"""
Simple Pinecone connection test
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key (required for embeddings)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")

# Import after environment variables are set
from services.pinecone_service import PineconeService

def test_pinecone_connection():
    """Test Pinecone connection and index availability"""
    print("🔍 Testing Pinecone Connection and Indexes...")
    
    # Create Pinecone service instance
    service = PineconeService()
    
    # Check if service initialized properly
    if not service.pc:
        print("❌ Pinecone client failed to initialize")
        return False
    
    print("✅ Pinecone client initialized")
    
    # Check if user knowledge base index is available
    if service.user_kb_index:
        print("✅ User knowledge base index is available")
        print(f"   Index name: {service.user_kb_index_name}")
        return True
    else:
        print("❌ User knowledge base index is not available")
        print("   You need to create the index in your Pinecone dashboard")
        return False

if __name__ == "__main__":
    print("🚀 Pinecone Connection Test")
    print("=" * 30)
    
    # Check environment variables
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not pinecone_api_key:
        print("❌ PINECONE_API_KEY not found in environment variables")
        print("   Please add it to your .env file")
        exit(1)
    
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("   Please add it to your .env file")
        exit(1)
    
    print("✅ API keys found")
    
    # Test connection
    success = test_pinecone_connection()
    
    if success:
        print("\n🎉 Pinecone connection test successful!")
    else:
        print("\n💥 Pinecone connection test failed!")
        exit(1)
