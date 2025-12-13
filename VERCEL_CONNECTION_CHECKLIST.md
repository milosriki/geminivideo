# ✅ Vercel Connection Checklist

## Quick Action Items

### 🔍 1. Verify Current Status
- [ ] Check which Vercel account currently has the `geminivideo` project
- [ ] Determine the correct Vercel account (personal/team/org)
- [ ] Document the current deployment URL
- [ ] Check if project exists in multiple Vercel accounts

### 🔐 2. Access & Authentication
- [ ] Confirm login credentials for correct Vercel account
- [ ] Verify GitHub repository access from correct Vercel account
- [ ] Ensure Vercel CLI is installed: `npm i -g vercel`
- [ ] Login to Vercel CLI with correct account: `vercel login`

### 🗑️ 3. Clean Up Wrong Connection (If Needed)
- [ ] Login to wrong Vercel account
- [ ] Go to Dashboard → Find `geminivideo` project
- [ ] Export any important data/settings
- [ ] Delete or archive the project from wrong account
- [ ] Verify project is removed

### 🔗 4. Connect to Correct Account
- [ ] Login to correct Vercel account (Dashboard or CLI)
- [ ] Import GitHub repository: `milosriki/geminivideo`
- [ ] Set root directory to: `frontend`
- [ ] Verify framework detection: Vite
- [ ] Configure build settings (should auto-detect)
- [ ] Deploy the project

### ⚙️ 5. Configure Environment Variables
Add these in Vercel Dashboard → Settings → Environment Variables:

**Required Variables (All Environments):**
- [ ] `VITE_SUPABASE_URL` = `https://akhirugwpozlxfvtqmvj.supabase.co`
- [ ] `VITE_SUPABASE_ANON_KEY` = `sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG`

**Optional Variables:**
- [ ] `VITE_API_URL` = (Your backend API URL)
- [ ] `VITE_FIREBASE_API_KEY` = (If using Firebase)
- [ ] `VITE_FIREBASE_PROJECT_ID` = (If using Firebase)
- [ ] `VITE_ENVIRONMENT` = `production` / `preview` / `development`

### 🔄 6. Update Supabase Configuration
In Supabase Dashboard: https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj

**Authentication → URL Configuration:**
- [ ] Update Site URL to new Vercel deployment URL
- [ ] Add redirect URL: `https://<your-project>.vercel.app`
- [ ] Add redirect URL: `https://<your-project>.vercel.app/**`
- [ ] Add redirect URL: `https://<your-project>-*.vercel.app`
- [ ] Add redirect URL: `https://<your-project>-*.vercel.app/**`
- [ ] Save changes

### 🔌 7. Reconnect Integrations
- [ ] Go to Supabase → Settings → Integrations
- [ ] Disconnect old Vercel integration (if exists)
- [ ] Click "Connect" on Vercel integration
- [ ] Authorize with correct Vercel account
- [ ] Select project: `geminivideo`
- [ ] Enable environments: Production, Preview, Development
- [ ] Verify environment variables synced to Vercel

### 🧪 8. Test Deployment
- [ ] Visit new Vercel URL
- [ ] Check browser console (F12) for errors
- [ ] Test frontend loads correctly
- [ ] Test Supabase connection (check network tab)
- [ ] Test authentication (sign up/login)
- [ ] Test API calls to backend services
- [ ] Verify CORS is working correctly

### 📝 9. Update Documentation
- [ ] Update internal docs with new Vercel URL
- [ ] Update team members on new deployment URL
- [ ] Update any hardcoded URLs in external systems
- [ ] Document the account used for future reference

### ✅ 10. Final Verification
- [ ] All environment variables present in Vercel
- [ ] Deployment successful (green checkmark)
- [ ] No errors in deployment logs
- [ ] Frontend accessible via Vercel URL
- [ ] Authentication working
- [ ] Backend API calls successful
- [ ] CORS headers correct
- [ ] SSL certificate active (https)

---

## 🚨 Common Issues & Solutions

### Issue: Build fails
**Solution:** 
- Check deployment logs in Vercel Dashboard
- Verify all dependencies in `package.json`
- Ensure Node.js version compatibility

### Issue: Environment variables not working
**Solution:**
- Verify variables are set for correct environment (Production/Preview)
- Redeploy after adding variables
- Check variable names match exactly (case-sensitive)
- Ensure `VITE_` prefix is used

### Issue: CORS errors
**Solution:**
- Add Vercel URL to backend CORS configuration
- Set `ALLOWED_ORIGINS` environment variable in backend
- Check backend service is running and accessible

### Issue: Supabase connection fails
**Solution:**
- Verify `VITE_SUPABASE_URL` is correct
- Verify `VITE_SUPABASE_ANON_KEY` is correct
- Check Supabase redirect URLs include Vercel URL
- Look for network errors in browser DevTools

### Issue: 404 on page refresh
**Solution:**
- Verify `vercel.json` exists in `frontend` directory
- Check rewrites configuration in `vercel.json`
- Ensure Vercel detected the configuration

---

## 📞 Support Contacts

**Vercel:**
- Dashboard: https://vercel.com/dashboard
- Documentation: https://vercel.com/docs
- Support: https://vercel.com/support

**Supabase:**
- Dashboard: https://supabase.com/dashboard
- Documentation: https://supabase.com/docs
- Support: https://supabase.com/support

**GitHub Repository:**
- URL: https://github.com/milosriki/geminivideo
- Issues: https://github.com/milosriki/geminivideo/issues

---

## 📊 Status Tracking

**Current Status:** 🟡 Action Required

**Last Updated:** December 12, 2024

**Completed Steps:** 
- ✅ Documentation cleanup
- ✅ Issue identification
- ✅ Guide creation

**Pending Steps:**
- ⏳ Determine correct Vercel account
- ⏳ Reconnect to correct account
- ⏳ Update Supabase configuration
- ⏳ Test deployment

---

## 🎯 Quick Commands Reference

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Link project (from frontend directory)
cd frontend
vercel link

# Deploy to production
vercel --prod

# Add environment variable
vercel env add VITE_SUPABASE_URL production

# List environment variables
vercel env ls

# Pull environment variables
vercel env pull

# View deployment logs
vercel logs

# List projects
vercel list

# Get project info
vercel inspect
```

---

**Follow this checklist step-by-step to ensure smooth Vercel account migration!** ✅
