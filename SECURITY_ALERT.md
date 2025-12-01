# 🚨 SECURITY ALERT: Immediate Action Required

## Exposed Firebase API Key

**Severity:** HIGH
**Status:** ⚠️ REQUIRES IMMEDIATE ACTION
**Date Detected:** 2025-12-01

---

## Issue Description

A Firebase API key was found hardcoded in your codebase:

- **File:** `frontend/src/firebaseConfig.ts`
- **Exposed Key:** `AIzaSyCamMhfOYNAqnKnK-nQ78f1u5o8VDx9IaU`
- **Project:** `ptd-fitness-demo`

This key has been **publicly exposed in your Git repository** and should be considered compromised.

---

## Immediate Actions Required

### 1. Rotate Firebase API Key (HIGH PRIORITY)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project: `ptd-fitness-demo`
3. Navigate to: **Project Settings** → **General**
4. Under **Your apps** → **Web app**, click **Regenerate API Key**
5. Copy the new API key

### 2. Update Environment Variables

Add the new API key to your environment variables:

```bash
# .env file (DO NOT COMMIT THIS FILE)
VITE_FIREBASE_API_KEY=your_new_api_key_here
VITE_FIREBASE_AUTH_DOMAIN=ptd-fitness-demo.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=ptd-fitness-demo
VITE_FIREBASE_STORAGE_BUCKET=ptd-fitness-demo.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=489769736562
VITE_FIREBASE_APP_ID=1:489769736562:web:08dab8e996d315949665eb
VITE_FIREBASE_MEASUREMENT_ID=G-B005380N01
```

### 3. Verify .gitignore

Ensure `.env` files are never committed:

```bash
# Add to .gitignore
.env
.env.local
.env.production
.env.development
*.env
```

### 4. Review Firebase Security Rules

Check your Firebase security rules to ensure they properly restrict access:

```bash
# Firestore rules example
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

---

## What Has Been Fixed

✅ Removed all hardcoded Firebase credentials from `firebaseConfig.ts`
✅ Added environment variable validation with helpful error messages
✅ Created `.env.example` template files
✅ Updated code to fail fast if credentials are missing

**Note:** The old API key is still in Git history. Consider these actions:

1. **Rotate the key** (as described above)
2. **Optional:** Rewrite Git history to remove the key (advanced, use with caution)
3. **Monitor:** Check Firebase Analytics for unusual activity

---

## Security Best Practices Going Forward

### Never Hardcode Credentials

❌ **NEVER DO THIS:**
```typescript
const apiKey = "AIzaSyCamMhfOYNAqnKnK-nQ78f1u5o8VDx9IaU"; // Hardcoded
```

✅ **ALWAYS DO THIS:**
```typescript
const apiKey = import.meta.env.VITE_FIREBASE_API_KEY; // From env
if (!apiKey) throw new Error("Missing VITE_FIREBASE_API_KEY");
```

### Use Environment-Specific Configs

- **Development:** `.env.development`
- **Staging:** `.env.staging`
- **Production:** `.env.production`

### Deployment Platforms

- **Vercel:** Add env vars in project settings
- **Netlify:** Use environment variables dashboard
- **Cloud Run:** Set via `gcloud run services update --set-env-vars`

### Secret Scanning

Enable GitHub secret scanning:
1. Go to repository **Settings**
2. Navigate to **Security & analysis**
3. Enable **Secret scanning**

---

## Verification Checklist

- [ ] Firebase API key rotated in Firebase Console
- [ ] New key added to `.env` file (not committed)
- [ ] `.env` files added to `.gitignore`
- [ ] Vercel/deployment platform updated with new env vars
- [ ] Firebase security rules reviewed and tightened
- [ ] Monitored Firebase Analytics for unusual activity
- [ ] Secret scanning enabled on GitHub

---

## Additional Exposed Credentials to Check

While fixing the Firebase key, please also verify these are NOT hardcoded:

- ✅ PostgreSQL connection strings (fixed)
- ✅ Redis URLs (fixed)
- ⚠️ Meta Ads access tokens (check `services/meta-publisher/`)
- ⚠️ AI API keys (Gemini, Claude, OpenAI) - ensure they're in env vars

---

## Questions or Issues?

If you need help rotating credentials or have questions about security:

1. Check Firebase documentation: https://firebase.google.com/docs/projects/api-keys
2. Review security best practices: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html

---

**Remember:** Security is not optional. Taking 10 minutes now to rotate this key can save hours of cleanup later.

🔒 Stay secure!
