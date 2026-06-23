# Google OAuth2 Setup Guide for StarNews

## ✅ What's Configured

Your Django app now has:
- ✅ `python-decouple` installed for secure environment variables
- ✅ `.env` file with Google OAuth credentials
- ✅ `.gitignore` configured to protect `.env` (never commit credentials)
- ✅ `settings.py` updated to read from environment variables
- ✅ Google OAuth button already in login.html

## 🔑 Final Setup Steps (Admin Panel)

1. **Start your server:**
   ```bash
   python manage.py runserver
   ```

2. **Go to Django Admin:**
   - Navigate to: `http://localhost:8000/admin/`
   - Login with your admin credentials

3. **Configure Google OAuth App:**
   - Go to: **Sites** → Ensure you have `example.com` (or your domain)
   - Go to: **Social applications** → **Add Social Application**
   - Fill in these details:
     - **Provider:** Google
     - **Name:** Google OAuth
     - **Client id:** `529692688040-2n7fp3qmn4v6km0r91gf4vr14i6sarpm.apps.googleusercontent.com`
     - **Secret key:** (from your `.env` file or JSON)
     - **Sites:** Select your site and move it to "Chosen sites"
   - Click **Save**

4. **Update Google Console:**
   - Go to: https://console.cloud.google.com/
   - Find your project
   - Go to: **Credentials** → Edit your OAuth 2.0 Client
   - Add **Authorized redirect URIs:**
     ```
     http://localhost:8000/accounts/google/login/callback/
     http://yourdomain.com/accounts/google/login/callback/
     ```
   - Save changes

## 🧪 Test It

1. Go to: `http://localhost:8000/login/`
2. Click **"Continue with Google"**
3. Login with your Google account
4. You should be redirected to the home page (logged in)

## 🔒 Security Notes

- ✅ `.env` file is protected in `.gitignore`
- ✅ Credentials NOT committed to git
- ✅ Use environment variables in production
- ⚠️ Never share your `.env` file or client secret

## 📝 Environment Variables Used

```
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
DEBUG=True
SECRET_KEY=...
```

All configured in `.env` file (git-ignored)
