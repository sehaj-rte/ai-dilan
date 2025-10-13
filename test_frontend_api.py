#!/usr/bin/env python3
"""
Test script to verify frontend API endpoints
"""

import requests
import json

def test_knowledge_base_files():
    """Test the knowledge base files endpoint that frontend uses"""
    
    url = "http://localhost:8000/knowledge-base/files"
    
    try:
        print("🧪 Testing knowledge base files endpoint...")
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Files endpoint working!")
            print(f"Total files: {result.get('total', 0)}")
            
            if result.get('files'):
                print("\nFiles available for expert creation:")
                for i, file_info in enumerate(result['files'], 1):
                    print(f"{i}. {file_info['name']}")
                    print(f"   - Type: {file_info['type']}")
                    print(f"   - Size: {file_info['size']} bytes")
                    print(f"   - Status: {file_info['processing_status']}")
                    print(f"   - Created: {file_info['created_at']}")
                    print()
            else:
                print("No files found")
                
        else:
            print("❌ Files endpoint failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing files endpoint: {e}")

def test_experts_endpoint():
    """Test the experts endpoint"""
    
    url = "http://localhost:8000/experts/"
    
    try:
        print("🧪 Testing experts endpoint...")
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Experts endpoint working!")
            print(f"Total experts: {len(result.get('experts', []))}")
                
        else:
            print("❌ Experts endpoint failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing experts endpoint: {e}")

if __name__ == "__main__":
    test_knowledge_base_files()
    print("-" * 50)
    test_experts_endpoint()
