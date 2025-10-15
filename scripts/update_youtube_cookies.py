#!/usr/bin/env python3
"""
YouTube Cookies Update Script

This script helps you update your YouTube cookies for better video access.
Run this script when you encounter authentication errors with YouTube videos.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🍪 YouTube Cookies Update Helper")
    print("=" * 40)
    
    # Get the backend directory
    backend_dir = Path(__file__).parent.parent
    cookies_file = backend_dir / "cookies.txt"
    
    print(f"Backend directory: {backend_dir}")
    print(f"Cookies file location: {cookies_file}")
    
    print("\n📋 Instructions:")
    print("1. Open your browser and go to YouTube")
    print("2. Make sure you're logged in to your YouTube account")
    print("3. Install a browser extension like 'Get cookies.txt LOCALLY'")
    print("4. Export cookies for youtube.com in Netscape format")
    print("5. Save the file as 'cookies.txt' in the backend directory")
    
    print(f"\n💾 Save your cookies file to: {cookies_file}")
    
    # Check if cookies file exists
    if cookies_file.exists():
        print(f"✅ Cookies file found: {cookies_file}")
        
        # Check file size
        file_size = cookies_file.stat().st_size
        if file_size < 100:
            print("⚠️  Warning: Cookies file seems very small. It might be incomplete.")
        else:
            print(f"📊 File size: {file_size} bytes")
        
        # Check if it contains YouTube cookies
        try:
            with open(cookies_file, 'r') as f:
                content = f.read()
                if 'youtube.com' in content:
                    print("✅ File contains YouTube cookies")
                else:
                    print("❌ File doesn't seem to contain YouTube cookies")
        except Exception as e:
            print(f"❌ Error reading cookies file: {e}")
    else:
        print(f"❌ Cookies file not found: {cookies_file}")
        print("Please create the cookies file following the instructions above.")
    
    print("\n🔧 Testing cookies...")
    
    # Try to test with a simple YouTube video
    try:
        import yt_dlp
        
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - usually accessible
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        if cookies_file.exists():
            ydl_opts['cookiefile'] = str(cookies_file)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            print(f"✅ Test successful! Retrieved info for: {info.get('title', 'Unknown')}")
    
    except ImportError:
        print("⚠️  yt-dlp not available for testing")
    except Exception as e:
        error_msg = str(e)
        if "Sign in to confirm you're not a bot" in error_msg:
            print("❌ Authentication required - please update your cookies")
        else:
            print(f"❌ Test failed: {error_msg}")
    
    print("\n🔄 Next steps:")
    print("1. If cookies are working, restart your backend server")
    print("2. If not working, export fresh cookies from your browser")
    print("3. Make sure you're logged into YouTube when exporting")
    print("4. Try the transcription again")

if __name__ == "__main__":
    main()
