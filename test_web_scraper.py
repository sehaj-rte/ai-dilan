#!/usr/bin/env python3
"""
Test script for web scraping functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.web_scraper_service import web_scraper_service
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_web_scraping():
    """Test web scraping with Mayo Clinic URL"""
    
    test_url = "https://www.mayoclinic.org/diseases-conditions/obsessive-compulsive-disorder/symptoms-causes/syc-20354432"
    
    print(f"🌐 Testing web scraping with URL: {test_url}")
    print("=" * 80)
    
    try:
        # Test the web scraper service
        result = web_scraper_service.scrape_url(test_url)
        
        print(f"✅ Success: {result['success']}")
        
        if result['success']:
            content = result['content']
            metadata = result['metadata']
            
            print(f"📄 Content length: {len(content)} characters")
            print(f"📋 Metadata keys: {list(metadata.keys())}")
            print(f"🏷️  Page title: {metadata.get('title', 'No title')}")
            print(f"🌍 Domain: {metadata.get('domain', 'No domain')}")
            print(f"📊 Word count: {metadata.get('word_count', 0)}")
            print(f"⏰ Scraped at: {metadata.get('scraped_at', 'No timestamp')}")
            
            print("\n" + "=" * 80)
            print("📝 FULL CONTENT:")
            print("=" * 80)
            print(content)
            
            print("\n" + "=" * 80)
            print("🔍 METADATA DETAILS:")
            print("=" * 80)
            for key, value in metadata.items():
                print(f"{key}: {value}")
                
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"💥 Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_scraping()
