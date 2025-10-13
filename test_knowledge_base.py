#!/usr/bin/env python3
"""
Test script for the custom knowledge base system
This script tests the complete workflow from file upload to AI agent search
"""

import asyncio
import os
import sys
import requests
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from services.document_processor import document_processor
from services.embedding_service import embedding_service
from services.pinecone_service import pinecone_service

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user_123"

def test_document_processing():
    """Test document text extraction"""
    print("🧪 Testing document processing...")
    
    # Create a simple test document
    test_text = """
    This is a test document for the knowledge base system.
    It contains information about artificial intelligence and machine learning.
    The system should be able to extract this text and make it searchable.
    """
    
    # Test text extraction
    result = document_processor.extract_text(
        file_content=test_text.encode('utf-8'),
        content_type='text/plain',
        filename='test_document.txt'
    )
    
    if result["success"]:
        print("✅ Document processing successful")
        print(f"   Extracted {result['word_count']} words")
        return result["text"]
    else:
        print(f"❌ Document processing failed: {result['error']}")
        return None

async def test_embedding_generation(text):
    """Test text chunking and embedding generation"""
    print("🧪 Testing embedding generation...")
    
    result = embedding_service.process_document(
        text=text,
        file_id="test_file_123",
        filename="test_document.txt",
        user_id=TEST_USER_ID
    )
    
    if result["success"]:
        print("✅ Embedding generation successful")
        print(f"   Created {result['total_chunks']} chunks")
        return result["chunks"]
    else:
        print(f"❌ Embedding generation failed: {result['error']}")
        return None

async def test_pinecone_storage(chunks):
    """Test storing chunks in Pinecone"""
    print("🧪 Testing Pinecone storage...")
    
    result = await pinecone_service.store_document_chunks(
        chunks=chunks,
        user_id=TEST_USER_ID
    )
    
    if result["success"]:
        print("✅ Pinecone storage successful")
        print(f"   Stored {result['chunks_stored']} chunks")
        return True
    else:
        print(f"❌ Pinecone storage failed: {result['error']}")
        return False

async def test_knowledge_search():
    """Test searching the knowledge base"""
    print("🧪 Testing knowledge base search...")
    
    result = await pinecone_service.search_user_knowledge(
        query="artificial intelligence machine learning",
        user_id=TEST_USER_ID,
        top_k=3
    )
    
    if result["success"]:
        print("✅ Knowledge base search successful")
        print(f"   Found {len(result['results'])} results")
        for i, item in enumerate(result['results']):
            print(f"   Result {i+1}: Score {item['score']:.3f}")
        return True
    else:
        print(f"❌ Knowledge base search failed: {result['error']}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("🧪 Testing API endpoints...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test knowledge base endpoints
        response = requests.get(f"{BASE_URL}/knowledge-base/files")
        if response.status_code == 200:
            print("✅ Knowledge base files endpoint working")
        else:
            print(f"❌ Knowledge base files endpoint failed: {response.status_code}")
        
        # Test tools health endpoint
        response = requests.get(f"{BASE_URL}/tools/pinecone-search/health")
        if response.status_code == 200:
            print("✅ Tools health endpoint working")
            data = response.json()
            print(f"   User KB available: {data.get('user_kb_available', False)}")
        else:
            print(f"❌ Tools health endpoint failed: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure the server is running.")
        return False
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

def test_webhook_endpoint():
    """Test the search webhook endpoint"""
    print("🧪 Testing search webhook...")
    
    try:
        payload = {
            "query": "artificial intelligence",
            "top_k": 3
        }
        
        response = requests.post(
            f"{BASE_URL}/tools/search-user-knowledge?user_id={TEST_USER_ID}",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Search webhook working")
            data = response.json()
            print(f"   Response length: {len(data.get('response', ''))}")
            return True
        else:
            print(f"❌ Search webhook failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook test failed: {str(e)}")
        return False

async def run_complete_test():
    """Run the complete test suite"""
    print("🚀 Starting Custom Knowledge Base System Test")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["OPENAI_API_KEY", "PINECONE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set these in your .env file")
        return False
    
    print("✅ Environment variables configured")
    
    # Test 1: Document Processing
    text = test_document_processing()
    if not text:
        return False
    
    # Test 2: Embedding Generation
    chunks = await test_embedding_generation(text)
    if not chunks:
        return False
    
    # Test 3: Pinecone Storage
    storage_success = await test_pinecone_storage(chunks)
    if not storage_success:
        return False
    
    # Test 4: Knowledge Search
    search_success = await test_knowledge_search()
    if not search_success:
        return False
    
    # Test 5: API Endpoints
    api_success = test_api_endpoints()
    if not api_success:
        print("⚠️  API tests failed - make sure server is running with: python main.py")
        return False
    
    # Test 6: Webhook Endpoint
    webhook_success = test_webhook_endpoint()
    if not webhook_success:
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Custom Knowledge Base System is working correctly.")
    print("\n📋 Next Steps:")
    print("1. Upload documents via the API or frontend")
    print("2. Create experts with ElevenLabs integration")
    print("3. Chat with experts - they'll automatically search your knowledge base")
    print("4. Monitor logs for search activity")
    
    return True

def print_usage():
    """Print usage instructions"""
    print("Custom Knowledge Base Test Script")
    print("=" * 40)
    print("Usage: python test_knowledge_base.py")
    print("\nBefore running:")
    print("1. Set up your .env file with required API keys")
    print("2. Start the server: python main.py")
    print("3. Run this test script")
    print("\nRequired environment variables:")
    print("- OPENAI_API_KEY")
    print("- PINECONE_API_KEY")
    print("- PINECONE_USER_KB_INDEX")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print_usage()
    else:
        asyncio.run(run_complete_test())
