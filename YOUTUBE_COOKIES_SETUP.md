# YouTube Cookies Setup Guide

This guide explains how to set up YouTube cookies for enhanced video access, including age-restricted and region-locked content.

## 🍪 What Are YouTube Cookies For?

YouTube cookies allow your transcription service to:
- ✅ Access age-restricted videos
- ✅ Access region-locked content
- ✅ Access private/unlisted videos you have permission to view
- ✅ Bypass some rate limiting
- ✅ Access premium content if you have a subscription

## 📋 Setup Instructions

### Step 1: Export Your YouTube Cookies

**Option A: Browser Extension (Recommended)**
1. Install browser extension: "Get cookies.txt LOCALLY" or "cookies.txt"
2. Go to YouTube while logged in to your account
3. Click the extension icon
4. Export cookies as `cookies.txt` format

**Option B: Manual Export**
1. Open YouTube in your browser (logged in)
2. Open Developer Tools (F12)
3. Go to Application/Storage tab → Cookies → https://youtube.com
4. Export all cookies in Netscape format

### Step 2: Save Cookies File

1. Save your cookies as `cookies.txt` in the backend root directory:
   ```
   /home/kartar/CascadeProjects/dilan-ai-backend/cookies.txt
   ```

2. The file should look like this:
   ```
   # Netscape HTTP Cookie File
   .youtube.com	TRUE	/	TRUE	1778849422	LOGIN_INFO	AFmmF2swRAIg...
   .youtube.com	TRUE	/	FALSE	1793078348	HSID	Aq-0sUhMRfULUsQQt
   ...
   ```

### Step 3: Configure Environment Variable

Add this line to your `.env` file:
```env
YOUTUBE_COOKIES_FILE=cookies.txt
```

### Step 4: Restart Your Server

Restart your backend server to load the new configuration:
```bash
python main.py
```

## 🔒 Security Notes

- ✅ `cookies.txt` is automatically added to `.gitignore`
- ✅ Cookies are never logged or exposed in API responses
- ✅ File is only used locally by yt-dlp
- ⚠️ **Never share your cookies file** - it contains your login session
- ⚠️ **Regenerate cookies periodically** - they expire over time

## 🧪 Testing

After setup, test with a restricted video:
1. Find an age-restricted YouTube video
2. Try transcribing it through your app
3. Check logs for: `"Using cookies from: cookies.txt"`

## 🔧 Troubleshooting

### Cookies Not Working?
- Check file path is correct: `cookies.txt` in backend root
- Verify file format (Netscape HTTP Cookie File)
- Ensure you're logged in to YouTube when exporting
- Try re-exporting fresh cookies

### Still Getting Access Errors?
- Some videos may still be inaccessible due to other restrictions
- Try with a different video to test
- Check if your YouTube account has the necessary permissions

### Production Deployment

For production (Render/Heroku):
1. Upload `cookies.txt` to your server
2. Set environment variable: `YOUTUBE_COOKIES_FILE=/path/to/cookies.txt`
3. Ensure file permissions are correct (readable by app)

## 📊 How It Works

1. **Development**: Uses cookies file if available, falls back to no auth
2. **Production**: Skips browser cookies, uses file-based cookies only
3. **Fallback**: If no cookies or file missing, continues without auth

## 🔄 Cookie Maintenance

- **Expiration**: Cookies expire, re-export monthly or when issues arise
- **Updates**: Re-export after changing YouTube password
- **Multiple Accounts**: Use different cookie files for different accounts

---

**Current Status**: ✅ Cookies file created and configured
**Environment Variable**: `YOUTUBE_COOKIES_FILE=cookies.txt`
**Security**: ✅ Added to .gitignore
