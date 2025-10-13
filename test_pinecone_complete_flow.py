#!/usr/bin/env python3
"""
Complete Pinecone workflow test - from document processing to search
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key (required for embeddings)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")

from services.document_processor import document_processor
from services.embedding_service import embedding_service
from services.pinecone_service import pinecone_service

async def test_complete_flow():
    """Test the complete Pinecone workflow"""
    print("🚀 Testing Complete Pinecone Workflow")
    print("=" * 40)
    
    # Check API keys
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY not found in environment variables")
        return False
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment variables")
        return False
    
    print("✅ API keys configured")
    
    # Step 1: Process a document
    print("\n📝 Step 1: Document Processing")
    test_document = """
    The History of Artificial Intelligence
    ================================
    
    Artificial Intelligence (AI) has a rich history spanning several decades. 
    The field was formally founded in 1956 at the Dartmouth Conference.
    
    Early AI Research (1950s-1970s)
    -------------------------------
    In the 1950s and 1960s, researchers were optimistic about AI's potential. 
    They developed early algorithms for problem-solving and symbolic reasoning.
    
    The AI Winter (1970s-1980s)
    --------------------------
    Due to unmet expectations and funding cuts, AI research experienced periods 
    of reduced interest known as "AI winters."
    
    Modern AI (1990s-Present)
    -------------------------
    With the advent of machine learning, neural networks, and big data, AI has 
    experienced a renaissance. Deep learning breakthroughs have enabled 
    applications like image recognition, natural language processing, and 
    autonomous vehicles.
    """.encode('utf-8')
    
    extraction_result = document_processor.extract_text(
        file_content=test_document,
        content_type='text/plain',
        filename='ai_history.txt'
    )
    
    if not extraction_result["success"]:
        print(f"❌ Document processing failed: {extraction_result['error']}")
        return False
    
    print("✅ Document processed successfully")
    print(f"   Extracted {extraction_result['word_count']} words")
    
    # Step 2: Generate embeddings
    print("\n🧠 Step 2: Embedding Generation")
    embedding_result = embedding_service.process_document(
        text=extraction_result["text"],
        file_id="test_doc_001",
        filename="ai_history.txt",
        user_id="test_user"
    )
    
    if not embedding_result["success"]:
        print(f"❌ Embedding generation failed: {embedding_result['error']}")
        return False
    
    print("✅ Embeddings generated successfully")
    print(f"   Created {embedding_result['total_chunks']} chunks")
    
    # Step 3: Store in Pinecone
    print("\n💾 Step 3: Pinecone Storage")
    storage_result = await pinecone_service.store_document_chunks(
        chunks=embedding_result["chunks"],
        user_id="test_user"
    )
    
    if not storage_result["success"]:
        print(f"❌ Pinecone storage failed: {storage_result['error']}")
        return False
    
    print("✅ Data stored in Pinecone successfully")
    print(f"   Stored {storage_result['chunks_stored']} vectors")
    print(f"   Namespace: {storage_result['namespace']}")
    
    # Step 4: Search Pinecone
    print("\n🔍 Step 4: Pinecone Search")
    search_result = await pinecone_service.search_user_knowledge(
        query="When was AI formally founded?",
        user_id="test_user",
        top_k=3
    )
    
    if not search_result["success"]:
        print(f"❌ Pinecone search failed: {search_result['error']}")
        return False
    
    print("✅ Pinecone search completed successfully")
    print(f"   Found {len(search_result['results'])} results")
    
    # Display results
    for i, result in enumerate(search_result["results"]):
        print(f"\n   Result {i+1}:")
        print(f"     Score: {result['score']:.3f}")
        print(f"     Content: {result['text'][:200]}...")
    
    # Step 5: Clean up (delete the test data)
    print("\n🗑 Step 5: Pinecone Cleanup")
    delete_result = await pinecone_service.delete_user_document(
        file_id="test_doc_001",
        user_id="test_user"
    )
    
    if not delete_result["success"]:
        print(f"❌ Pinecone deletion failed: {delete_result['error']}")
        return False
    
    print("✅ Test data cleaned up successfully")
    print(f"   Deleted {delete_result['deleted_chunks']} vectors")
    
    print("\n" + "=" * 40)
    print("🎉 Complete Pinecone Workflow Test Passed!")
    print("All components are working together correctly.")
    return True

if __name__ == "__main__":
    asyncio.run(test_complete_flow())
