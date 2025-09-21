# Deployment Guide for ThakhinMala Train Booking System

## Deploy to Render

### Prerequisites
1. GitHub account
2. Render account (free tier available)
3. Your Neon PostgreSQL database URL

### Step 1: Push to GitHub
1. Create a new repository on GitHub
2. Push your `fastapi-project` folder to the repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - ThakhinMala Train Booking System"
   git branch -M main
   git remote add origin https://github.com/yourusername/thakhinmala-train-booking.git
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Go to [render.com](https://render.com) and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select your `thakhinmala-train-booking` repository
5. Configure the deployment:
   - **Name**: `thakhinmala-train-booking`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: Leave empty (or `fastapi-project` if it's in a subdirectory)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

### Step 3: Set Environment Variables
In Render dashboard, go to your service → Environment:

1. **DATABASE_URL**: Your Neon PostgreSQL connection string
   ```
   postgresql+asyncpg://username:password@host:port/database
   ```

2. **SECRET_KEY**: Generate a secure secret key
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **ALGORITHM**: `HS256`

4. **ACCESS_TOKEN_EXPIRE_MINUTES**: `30`

### Step 4: Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy your application
3. You'll get a URL like: `https://thakhinmala-train-booking.onrender.com`

### Step 5: Verify Deployment
- API Documentation: `https://your-app.onrender.com/docs`
- Health Check: `https://your-app.onrender.com/`
- Stations API: `https://your-app.onrender.com/api/stations/`

### Alternative: Manual Deployment
If you prefer manual configuration instead of render.yaml:

1. Skip the render.yaml file
2. Manually configure in Render dashboard
3. Use the environment variables listed above

### Database Setup
Your Neon PostgreSQL database should already have all the data from our previous setup:
- ✅ All BTS stations with codes
- ✅ Route segments and intersections
- ✅ Line station orders
- ✅ Complete route management system

### Troubleshooting
- Check logs in Render dashboard if deployment fails
- Ensure DATABASE_URL is correctly formatted for asyncpg
- Verify all environment variables are set
- Check that requirements.txt includes all dependencies

### Free Tier Limitations
- Service sleeps after 15 minutes of inactivity
- 750 hours/month free (sufficient for testing)
- Consider upgrading for production use