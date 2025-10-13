#!/usr/bin/env python3
"""
Test script for knowledge base file upload
"""

import requests
import json

def test_upload():
    """Test file upload endpoint"""
    
    # Create a simple test file
    test_content = "This is a test document for the knowledge base system.\n\nIt contains some sample text to verify that file uploads are working correctly."
    
    # Prepare the file for upload
    files = {
        'file': ('test_document.txt', test_content, 'text/plain')
    }
    
    # Make the upload request
    url = "http://localhost:8000/knowledge-base/upload"
    
    try:
        print("🧪 Testing file upload...")
        response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(json.dumps(result, indent=2))
        else:
            print("❌ Upload failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during upload: {e}")

def test_get_files():
    """Test get files endpoint"""
    
    url = "http://localhost:8000/knowledge-base/files"
    
    try:
        print("\n🧪 Testing get files...")
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Get files successful!")
            print(f"Total files: {result.get('total', 0)}")
            if result.get('files'):
                for file_info in result['files'][:3]:  # Show first 3 files
                    print(f"- {file_info['name']} ({file_info['type']}) - {file_info['processing_status']}")
        else:
            print("❌ Get files failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting files: {e}")

if __name__ == "__main__":
    test_upload()
    test_get_files()
