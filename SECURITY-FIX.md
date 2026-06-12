# 🔒 Security Vulnerability Fix Guide

## Critical Issues to Fix Before Committing to GitHub

### 1. Remove Tracked Sensitive Files

Run these commands immediately to remove sensitive files from Git tracking:

```bash
# Remove frontend environment files from Git tracking
git rm --cached frontend/.env.local
git rm --cached frontend/.env.production
git rm --cached frontend/.env.staging

# Remove any other sensitive files
git rm --cached **/*.env.*
```

### 2. Update .gitignore

Add these lines to your .gitignore file:

```gitignore
# Frontend environment files
frontend/.env.local
frontend/.env.production
frontend/.env.staging
frontend/.env.development

# All environment files
**/.env
**/.env.*
!**/.env.example
!**/.env.template

# Firebase
firebase-admin-key.json
firebase-service-account.json
*firebase*.json
!firebase.json
!firebase-hosting-config.json

# Google Cloud
gcp-key.json
gcp-credentials.json
```

### 3. Fix Hardcoded Secrets in Code

#### File: app/core/config.py
Replace the hardcoded secret key fallback:

```python
# BEFORE (INSECURE):
SECRET_KEY: str = os.getenv("SECRET_KEY", "development-secret-key-change-in-production")

# AFTER (SECURE):
SECRET_KEY: str = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if ENVIRONMENT == "development":
        SECRET_KEY = "dev-only-" + os.urandom(32).hex()
    else:
        raise ValueError("SECRET_KEY must be set in production")
```

#### File: app/core/database.py
Remove hardcoded password fallback:

```python
# BEFORE (INSECURE):
except Exception as e:
    logger.error(f"Failed to retrieve database password: {e}")
    return "SecurePassword123!"

# AFTER (SECURE):
except Exception as e:
    logger.error(f"Failed to retrieve database password: {e}")
    if settings.ENVIRONMENT == "development":
        # Use local dev password from env
        return os.getenv("LOCAL_DB_PASSWORD", "")
    else:
        raise Exception("Cannot retrieve database password from Secret Manager")
```

### 4. Rotate Exposed Credentials

Since your Firebase API key has been exposed:

1. **Create new Firebase API keys:**
   - Go to Firebase Console → Project Settings
   - Add domain restrictions to the API key
   - Restrict API key to specific APIs only

2. **Update Secret Manager:**
   ```bash
   # Create new secret for any exposed credentials
   echo -n "new-secret-value" | gcloud secrets create new-secret-name --data-file=-
   ```

### 5. Set Up Environment Variables Properly

#### For Local Development
Create `.env.local` (but never commit it):
```env
SECRET_KEY=generate-with-openssl-rand-hex-32
LOCAL_DB_PASSWORD=local-dev-password
```

#### For Production (use Secret Manager or CI/CD)
```bash
# In Cloud Run
gcloud run services update motion-api \
  --set-env-vars SECRET_KEY=$(gcloud secrets versions access latest --secret=app-secret-key)
```

### 6. Verify Files Are Untracked

```bash
# Check that sensitive files are not tracked
git status --ignored

# Verify .env files are ignored
git check-ignore frontend/.env.local
git check-ignore frontend/.env.production
```

### 7. Security Best Practices Going Forward

1. **Never commit .env files** - Use .env.example as template
2. **Use Secret Manager** for all production secrets
3. **Rotate credentials regularly**
4. **Use different credentials** for dev/staging/prod
5. **Enable GitHub secret scanning** in repo settings
6. **Review commits before pushing** with `git diff --staged`

### 8. Pre-Commit Hook (Optional)

Add this to `.git/hooks/pre-commit` to prevent accidental commits:

```bash
#!/bin/bash
# Check for common secret patterns
if git diff --staged --name-only | xargs grep -E "(api[_-]?key|secret|password|token)" | grep -v example; then
    echo "⚠️  WARNING: Possible secrets detected in staged files!"
    echo "Review the changes carefully before committing."
    exit 1
fi
```

## Emergency Commands If Already Committed

If you've already committed sensitive data:

```bash
# Remove from history (requires force push)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch frontend/.env.production" \
  --prune-empty --tag-name-filter cat -- --all

# Or use BFG Repo Cleaner (easier)
bfg --delete-files .env.production
git push --force
```

## Validation Checklist

- [ ] All .env files removed from tracking
- [ ] .gitignore updated with sensitive file patterns
- [ ] Hardcoded secrets removed from code
- [ ] Firebase API keys have domain restrictions
- [ ] Secret Manager configured for production
- [ ] Pre-commit hooks installed (optional)
- [ ] Team notified about credential rotation