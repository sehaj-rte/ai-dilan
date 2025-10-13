#!/usr/bin/env python3
"""
Debug script to test DOCX processing
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from services.document_processor import document_processor

def test_docx_processing():
    """Test DOCX document processing"""
    
    print("🔍 Debug: Testing DOCX Document Processing")
    print("="*50)
    
    # Test with a sample DOCX file if it exists
    test_files = [
        "/home/sehaj/Documents/dilan-new-project/ai-dilan/CBT+Therapist+and+Client+Example+Sessions.docx",
        "/tmp/test.docx"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"📄 Found test file: {test_file}")
            
            try:
                with open(test_file, 'rb') as f:
                    file_content = f.read()
                
                print(f"📊 File size: {len(file_content)} bytes")
                
                # Test extraction
                result = document_processor.extract_text(
                    file_content=file_content,
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    filename=os.path.basename(test_file)
                )
                
                print(f"\n📊 Extraction result: {result.get('success', False)}")
                
                if result.get("success"):
                    text = result.get("text", "")
                    print(f"✅ Success! Extracted {len(text)} characters")
                    print(f"📊 Word count: {result.get('word_count', 0)}")
                    print(f"📝 Text preview: {text[:200]}...")
                else:
                    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
                return result
                
            except Exception as e:
                print(f"💥 Exception with {test_file}: {str(e)}")
                import traceback
                traceback.print_exc()
    
    print("❌ No test DOCX files found")
    return None

if __name__ == "__main__":
    test_docx_processing()
