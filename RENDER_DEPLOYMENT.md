# 🚀 Render.com Deployment Guide for Dilan AI

## Quick Deploy (5 Minutes)

### Step 1: Push to GitHub
```bash
cd /home/kartar/CascadeProjects/dilan-ai-backend
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### Step 2: Deploy Backend on Render

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com/
   - Sign up with GitHub (free)

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub account
   - Select repository: `ai-dilan`
   - Click "Connect"

3. **Configure Service**
   - **Name**: `dilan-ai-backend`
   - **Runtime**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

4. **Add Environment Variables**
   Click "Advanced" → "Add Environment Variable":
   
   ```
   ELEVENLABS_API_KEY=4b757c743f73858a0b19a8947b7742c3c2acbacc947374329ae264bb61d02c2d
   S3_BUCKET_NAME=ai-dilan
   S3_ACCESS_KEY_ID=AKIARI5UHVTG2CWAHQUG
   S3_SECRET_KEY=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
   S3_REGION=us-east-1
   PINECONE_API_KEY=pcsk_59xqiJ_BoJ5jvLse9dKTT1FzmbHLCGS6GV11gfCDyRRLJPWUeTmwNnLUJ1yY3XHj3tEFkj
   PINECONE_EDUCATION_INDEX=aido-v2-index
   PINECONE_TRAVEL_INDEX=travel-guide
   PINECONE_USER_KB_INDEX=user-knowledge-base
   OPENAI_API_KEY=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
   WEBHOOK_AUTH_TOKEN=dilan-ai-pinecone-webhook-2024
   DEBUG=False
   APP_NAME=Dilan AI Backend
   ```

5. **Create PostgreSQL Database**
   - In Render Dashboard, click "New +" → "PostgreSQL"
   - **Name**: `dilan-db`
   - **Plan**: Free
   - Click "Create Database"
   - Copy the "Internal Database URL"
   - Add to backend environment variables as `DATABASE_URL`

6. **Deploy**
   - Click "Create Web Service"
   - Wait 3-5 minutes for deployment
   - Your backend will be live at: `https://dilan-ai-backend.onrender.com`

### Step 3: Deploy Frontend on Vercel

1. **Go to Vercel**
   - Visit: https://vercel.com/
   - Sign up with GitHub (free)

2. **Import Project**
   - Click "Add New..." → "Project"
   - Select repository: `ai-dilan-frontend`
   - Click "Import"

3. **Configure Project**
   - **Framework Preset**: Next.js (auto-detected)
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

4. **Add Environment Variable**
   ```
   NEXT_PUBLIC_API_URL=https://dilan-ai-backend.onrender.com
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Your frontend will be live at: `https://your-project.vercel.app`

## ✅ Post-Deployment

### Update ElevenLabs Webhook URLs
After deployment, update your ElevenLabs agent webhook URLs to:
```
https://dilan-ai-backend.onrender.com/tools/search-user-knowledge
```

### Test Your Deployment
1. Visit your frontend URL
2. Register a new account
3. Create an expert
4. Upload files
5. Test chat functionality

## 🎉 You're Live!

- **Frontend**: https://your-project.vercel.app
- **Backend API**: https://dilan-ai-backend.onrender.com
- **API Docs**: https://dilan-ai-backend.onrender.com/docs

## 📝 Notes

- **Free Tier Limits**:
  - Render: 750 hours/month (enough for 1 service)
  - Vercel: Unlimited deployments
  - PostgreSQL: Free tier available

- **Cold Starts**: Free tier services sleep after 15 min of inactivity. First request may take 30-60 seconds.

- **Auto-Deploy**: Both platforms auto-deploy on git push to main branch.

## 🔧 Troubleshooting

**Database Connection Issues:**
- Ensure `DATABASE_URL` is set correctly
- Check database is running in Render dashboard

**Build Failures:**
- Check build logs in Render dashboard
- Ensure all dependencies are in requirements.txt

**Frontend API Errors:**
- Verify `NEXT_PUBLIC_API_URL` points to your Render backend
- Check CORS settings in backend

## 💡 Alternative: All-in-One Render Deployment

You can also deploy frontend on Render as a static site:
1. Create new "Static Site" in Render
2. Build Command: `npm run build`
3. Publish Directory: `out` (if using Next.js export)

This keeps everything in one platform!
