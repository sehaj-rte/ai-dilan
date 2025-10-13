#!/usr/bin/env python3
"""
Test script for user knowledge base functionality with Pinecone
This script tests the complete workflow for user-specific knowledge base operations
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from services.document_processor import document_processor
from services.embedding_service import embedding_service
from services.pinecone_service import pinecone_service

# Test configuration
TEST_USER_ID = "test_user_123"
TEST_FILE_ID = "test_file_456"

def test_document_processor():
    """Test document processing service"""
    print("🧪 Testing Document Processor Service...")
    
    # Create test content
    test_content = """
    Artificial Intelligence and Machine Learning
    ==========================================
    
    Artificial Intelligence (AI) is a branch of computer science that aims to create 
    software or machines that exhibit human-like intelligence. This can include learning 
    from experience, understanding natural language, solving problems, and recognizing 
    patterns.
    
    Machine Learning (ML) is a subset of AI that focuses on algorithms and statistical 
    models that enable computers to improve at tasks with experience. Instead of being 
    explicitly programmed, ML systems learn from data.
    
    Deep Learning is a further subset of ML that uses neural networks with multiple 
    layers to model complex patterns in data. It's particularly effective for image 
    and speech recognition tasks.
    """.encode('utf-8')
    
    # Test text extraction
    result = document_processor.extract_text(
        file_content=test_content,
        content_type='text/plain',
        filename='ai_ml_basics.txt'
    )
    
    if result["success"]:
        print("✅ Document processor working correctly")
        print(f"   Extracted {len(result['text'])} characters")
        print(f"   Word count: {result['word_count']}")
        return result["text"]
    else:
        print(f"❌ Document processor failed: {result['error']}")
        return None

def test_embedding_service(text):
    """Test embedding generation service"""
    print("\n🧪 Testing Embedding Service...")
    
    result = embedding_service.process_document(
        text=text,
        file_id=TEST_FILE_ID,
        filename="ai_ml_basics.txt",
        user_id=TEST_USER_ID
    )
    
    if result["success"]:
        print("✅ Embedding service working correctly")
        print(f"   Created {result['total_chunks']} chunks")
        print(f"   Original word count: {result['original_word_count']}")
        print(f"   Processed word count: {result['processed_word_count']}")
        return result["chunks"]
    else:
        print(f"❌ Embedding service failed: {result['error']}")
        return None

async def test_pinecone_storage(chunks):
    """Test Pinecone storage operations"""
    print("\n🧪 Testing Pinecone Storage...")
    
    # Test storing chunks
    result = await pinecone_service.store_document_chunks(
        chunks=chunks,
        user_id=TEST_USER_ID
    )
    
    if result["success"]:
        print("✅ Pinecone storage successful")
        print(f"   Stored {result['chunks_stored']} vectors")
        print(f"   Namespace: {result['namespace']}")
        return True
    else:
        print(f"❌ Pinecone storage failed: {result['error']}")
        return False

async def test_pinecone_search():
    """Test Pinecone search operations"""
    print("\n🧪 Testing Pinecone Search...")
    
    # Test searching user knowledge base
    result = await pinecone_service.search_user_knowledge(
        query="What is machine learning?",
        user_id=TEST_USER_ID,
        top_k=3
    )
    
    if result["success"]:
        print("✅ Pinecone search successful")
        print(f"   Found {len(result['results'])} results")
        for i, item in enumerate(result['results']):
            print(f"   Result {i+1}:")
            print(f"     Score: {item['score']:.3f}")
            print(f"     Filename: {item['filename']}")
            print(f"     Text preview: {item['text'][:100]}...")
        return True
    else:
        print(f"❌ Pinecone search failed: {result['error']}")
        return False

async def test_pinecone_deletion():
    """Test Pinecone deletion operations"""
    print("\n🧪 Testing Pinecone Deletion...")
    
    # Test deleting user document
    result = await pinecone_service.delete_user_document(
        file_id=TEST_FILE_ID,
        user_id=TEST_USER_ID
    )
    
    if result["success"]:
        print("✅ Pinecone deletion successful")
        print(f"   Deleted {result['deleted_chunks']} chunks")
        return True
    else:
        print(f"❌ Pinecone deletion failed: {result['error']}")
        return False

async def run_user_knowledge_base_tests():
    """Run all user knowledge base tests"""
    print("🚀 Starting User Knowledge Base Tests")
    print("=" * 40)
    
    # Check required environment variables
    required_vars = ["OPENAI_API_KEY", "PINECONE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set these in your .env file")
        return False
    
    print("✅ Environment variables configured")
    
    # Test 1: Document Processing
    text = test_document_processor()
    if not text:
        return False
    
    # Test 2: Embedding Generation
    chunks = test_embedding_service(text)
    if not chunks:
        return False
    
    # Test 3: Pinecone Storage
    storage_success = await test_pinecone_storage(chunks)
    if not storage_success:
        return False
    
    # Test 4: Pinecone Search
    search_success = await test_pinecone_search()
    if not search_success:
        return False
    
    # Test 5: Pinecone Deletion
    deletion_success = await test_pinecone_deletion()
    if not deletion_success:
        return False
    
    print("\n" + "=" * 40)
    print("🎉 All User Knowledge Base Tests Passed!")
    print("The Pinecone integration is working correctly.")
    return True

def print_usage():
    """Print usage instructions"""
    print("User Knowledge Base Test Script")
    print("=" * 35)
    print("Usage: python test_user_knowledge_base.py")
    print("\nBefore running:")
    print("1. Set up your .env file with required API keys:")
    print("   - OPENAI_API_KEY")
    print("   - PINECONE_API_KEY")
    print("2. Ensure Pinecone index is created")
    print("3. Run this test script")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print_usage()
    else:
        asyncio.run(run_user_knowledge_base_tests())
