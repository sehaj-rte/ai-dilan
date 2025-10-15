#!/usr/bin/env python3
"""
Test script for web scraping API endpoint
"""

import requests
import json
import time

def test_api_scraping():
    """Test web scraping via API endpoint"""
    
    # API endpoint
    api_url = "http://localhost:8000/knowledge-base/scrape-website"
    test_url = "https://www.mayoclinic.org/diseases-conditions/obsessive-compulsive-disorder/symptoms-causes/syc-20354432"
    
    print(f"🌐 Testing API web scraping with URL: {test_url}")
    print("=" * 80)
    
    # Request payload
    payload = {
        "url": test_url,
        "folder_id": None,
        "custom_name": "OCD Mayo Clinic Article"
    }
    
    # Headers (you'll need to add proper auth headers in real usage)
    headers = {
        "Content-Type": "application/json",
        # Note: In real usage, you'd need proper authentication headers
        # "Authorization": "Bearer your_token_here"
    }
    
    try:
        print(f"📤 Sending POST request to: {api_url}")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        # Make the API request
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        print(f"📊 Response Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Request Successful!")
            print("=" * 80)
            print("📝 RESPONSE DATA:")
            print("=" * 80)
            print(json.dumps(result, indent=2))
            
        else:
            print(f"❌ API Request Failed!")
            print(f"Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - is the server running?")
    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_scraping()
