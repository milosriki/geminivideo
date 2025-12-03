# Deploying GeminiVideo Frontend to Vercel

This guide walks you through deploying the GeminiVideo frontend application to Vercel.

## Prerequisites

- A Vercel account (sign up at https://vercel.com)
- Your GitHub repository with the GeminiVideo project
- Backend API deployed and accessible (e.g., on Google Cloud Run)
- Supabase project set up with URL and anon key
- Firebase project configured

## Step 1: Connect GitHub Repository to Vercel

1. **Log in to Vercel**
   - Go to https://vercel.com and sign in with your GitHub account

2. **Import Project**
   - Click "Add New..." → "Project"
   - Select "Import Git Repository"
   - Find and select your `geminivideo` repository
   - Click "Import"

3. **Configure Project Root**
   - Set the root directory to `frontend`
   - Vercel should automatically detect it's a Vite project

## Step 2: Configure Build Settings

Vercel should automatically detect these settings from `vercel.json`, but verify:

- **Framework Preset**: Vite
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

## Step 3: Set Environment Variables

In the Vercel project settings, add the following environment variables:

### Required Variables

1. **VITE_API_URL**
   - **Value**: Your backend API URL (e.g., `https://api.your-domain.run.app`)
   - **Description**: The base URL for your backend API service

2. **VITE_SUPABASE_URL**
   - **Value**: Your Supabase project URL (e.g., `https://xxxxx.supabase.co`)
   - **Description**: Find this in your Supabase project settings
   - **Location**: Supabase Dashboard → Settings → API → Project URL

3. **VITE_SUPABASE_ANON_KEY**
   - **Value**: Your Supabase anonymous/public key
   - **Description**: Safe to use in the browser, provides row-level security
   - **Location**: Supabase Dashboard → Settings → API → Project API keys → `anon` `public`

4. **VITE_FIREBASE_API_KEY**
   - **Value**: Your Firebase Web API key
   - **Description**: Find this in Firebase project settings
   - **Location**: Firebase Console → Project Settings → General → Web API Key

5. **VITE_FIREBASE_PROJECT_ID**
   - **Value**: Your Firebase project ID
   - **Location**: Firebase Console → Project Settings → General → Project ID

### How to Add Environment Variables in Vercel

1. Go to your project in Vercel
2. Click "Settings" → "Environment Variables"
3. For each variable:
   - Enter the **Name** (e.g., `VITE_API_URL`)
   - Enter the **Value** (e.g., `https://api.your-domain.run.app`)
   - Select which environments to apply it to:
     - ✓ Production
     - ✓ Preview
     - ✓ Development (optional)
4. Click "Save"

### Using Vercel Secrets (Recommended)

For sensitive values, use Vercel's secret references:

```bash
# Install Vercel CLI
npm i -g vercel

# Add secrets
vercel secrets add api_url https://api.your-domain.run.app
vercel secrets add supabase_url https://xxxxx.supabase.co
vercel secrets add supabase_anon_key your-actual-anon-key
```

Then in Vercel dashboard, reference them as:
- `@api_url`
- `@supabase_url`
- `@supabase_anon_key`

## Step 4: Deploy

1. **Initial Deployment**
   - After configuring settings and environment variables, click "Deploy"
   - Vercel will build and deploy your application
   - This usually takes 1-3 minutes

2. **Monitor Build Logs**
   - Watch the deployment logs for any errors
   - Common issues:
     - Missing environment variables
     - Build command failures
     - Dependency installation errors

3. **Access Your Deployment**
   - Once complete, Vercel provides a URL (e.g., `your-project.vercel.app`)
   - Test all functionality to ensure API connections work

## Step 5: Custom Domain Setup (Optional)

1. **Add Custom Domain**
   - Go to Project Settings → Domains
   - Click "Add Domain"
   - Enter your domain (e.g., `geminivideo.com` or `app.geminivideo.com`)

2. **Configure DNS**
   - Vercel will provide DNS configuration instructions
   - Add the required DNS records to your domain registrar:
     - **A Record** or **CNAME Record** as specified by Vercel

3. **Example DNS Configuration**
   ```
   Type: CNAME
   Name: app (or @ for root domain)
   Value: cname.vercel-dns.com
   ```

4. **SSL Certificate**
   - Vercel automatically provisions SSL certificates
   - This may take a few minutes after DNS propagation

5. **Update CORS Settings**
   - Update your backend API to allow requests from your custom domain
   - Add the domain to allowed origins in your API CORS configuration

## Step 6: Continuous Deployment

Vercel automatically deploys on git push:

- **Production**: Pushes to `main` branch → production deployment
- **Preview**: Pushes to other branches → preview deployment with unique URL
- **Pull Requests**: Automatic preview deployments for each PR

### Configure Branch Deployments

1. Go to Settings → Git
2. Configure:
   - **Production Branch**: `main` (or your default branch)
   - **Preview Branches**: Enable for all branches or specific patterns

## Troubleshooting

### Build Fails

**Issue**: Build command fails
**Solution**:
- Check build logs for specific errors
- Verify all dependencies are in `package.json`
- Ensure Node.js version compatibility
- Check for TypeScript errors

### Environment Variables Not Working

**Issue**: App can't connect to backend/services
**Solution**:
- Verify all `VITE_*` prefixed variables are set
- Redeploy after adding variables (environment changes require redeployment)
- Check variable names match exactly (case-sensitive)
- Ensure variables are set for the correct environment (Production/Preview)

### API Requests Failing

**Issue**: Frontend can't reach backend API
**Solution**:
- Verify `VITE_API_URL` is correct and accessible
- Check backend CORS settings allow your Vercel domain
- Inspect network tab in browser DevTools
- Ensure backend API is deployed and running

### 404 on Refresh

**Issue**: Direct URL navigation returns 404
**Solution**:
- The `vercel.json` rewrites should handle this
- Verify `vercel.json` is in the `frontend` directory
- Check that Vercel detected the configuration

### Blank Page

**Issue**: App loads but shows blank page
**Solution**:
- Check browser console for errors
- Verify all environment variables are set
- Check that Firebase/Supabase configs are correct
- Ensure API endpoint is accessible

## Vercel CLI Commands

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Link local project to Vercel project
cd frontend
vercel link

# Test build locally
vercel build

# Deploy to preview
vercel

# Deploy to production
vercel --prod

# View deployment logs
vercel logs

# List environment variables
vercel env ls

# Pull environment variables to local .env
vercel env pull
```

## Security Best Practices

1. **Never commit secrets to git**
   - Use `.env.production` template only
   - Add actual values in Vercel dashboard

2. **Restrict API Keys**
   - Use Supabase Row Level Security (RLS)
   - Configure Firebase security rules
   - Implement backend authentication

3. **Security Headers**
   - Already configured in `vercel.json`
   - Includes XSS protection, frame options, etc.

4. **HTTPS Only**
   - Vercel enforces HTTPS automatically
   - Never allow HTTP traffic in production

## Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vite Deployment Guide](https://vitejs.dev/guide/static-deploy.html#vercel)
- [Environment Variables in Vercel](https://vercel.com/docs/concepts/projects/environment-variables)
- [Custom Domains on Vercel](https://vercel.com/docs/concepts/projects/custom-domains)

## Support

If you encounter issues:

1. Check [Vercel Status](https://www.vercel-status.com/)
2. Review [Vercel Documentation](https://vercel.com/docs)
3. Check deployment logs in Vercel dashboard
4. Inspect browser console for client-side errors
5. Contact Vercel Support for platform-specific issues
