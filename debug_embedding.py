#!/usr/bin/env python3
"""
Debug script to test embedding service directly
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from services.embedding_service import embedding_service
import openai

def test_embedding_service():
    """Test the embedding service with a simple document"""
    
    print("🔍 Debug: Testing Embedding Service")
    print("="*50)
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ OpenAI API Key found: {api_key[:20]}...")
    else:
        print("❌ OpenAI API Key not found!")
        return
    
    # Test simple text
    test_text = """
    This is a test document for the embedding service.
    It contains multiple sentences to test the chunking and embedding process.
    The document should be processed into smaller chunks and each chunk should get an embedding.
    This will help us verify that the embedding service is working correctly.
    """
    
    print(f"📝 Test text length: {len(test_text)} characters")
    print(f"📝 Test text word count: {len(test_text.split())} words")
    
    try:
        print("\n🚀 Starting embedding process...")
        
        result = embedding_service.process_document(
            text=test_text,
            file_id="test_file_123",
            filename="test_document.txt",
            user_id="test_user"
        )
        
        print(f"\n📊 Result: {result.get('success', False)}")
        
        if result.get("success"):
            print(f"✅ Success! Generated {result.get('total_chunks', 0)} chunks")
            print(f"📊 Processed {result.get('processed_word_count', 0)} words")
            
            chunks = result.get("chunks", [])
            if chunks:
                print(f"\n🔍 First chunk preview:")
                first_chunk = chunks[0]
                print(f"  - ID: {first_chunk.get('id', 'N/A')}")
                print(f"  - Text length: {len(first_chunk.get('text', ''))}")
                print(f"  - Embedding dimensions: {len(first_chunk.get('embedding', []))}")
                print(f"  - Text preview: {first_chunk.get('text', '')[:100]}...")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_embedding_service()
