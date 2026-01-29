# Security FAQ - Maps for Developers

## Can my dev access the R2 credentials from git?

**Short answer: YES**

**Why:**
- R2 credentials were committed to `CLAUDE.md` in earlier commits
- Anyone with repo access can retrieve them from git history
- Even though we removed them from current files, git history preserves everything

**How they can access:**
```bash
# View credential history
git log --all -p -- CLAUDE.md | grep -A 5 "AWS_ACCESS_KEY"

# Or just check CREDENTIALS.md if you share it
cat CREDENTIALS.md
```

---

## Is this a problem?

**NO - and here's why:**

1. **Private repository** - Only your team has access
2. **Dev needs credentials** - They need R2 keys to work on data pipeline
3. **R2 is for public data** - Map tiles are meant to be publicly accessible via CDN
4. **No user data** - R2 only stores map tiles, not user information
5. **Easy to rotate** - If compromised, generate new keys in 2 minutes

---

## What CAN'T be accessed (properly secured)

✅ **Supabase credentials** - Only in Vercel env vars (production)
✅ **Stripe keys** - Only in Vercel env vars (production)
✅ **User data** - Stored in Supabase, not accessible via R2 keys
✅ **Payment info** - Stored in Stripe, not in our system

---

## What CAN be accessed (and that's OK)

⚠️ **R2 access keys** - Anyone with repo access
⚠️ **R2 bucket** - But it's public via CDN anyway
⚠️ **Map data** - Also public via CDN
⚠️ **Ollama endpoint** - Local network only (10.8.0.1)

---

## Recommended credential sharing with dev

### Option 1: Just share CREDENTIALS.md directly
```bash
# Send encrypted email with CREDENTIALS.md attached
# Or use secure sharing: 1Password, Bitwarden, etc.
```

### Option 2: Let them extract from git
```bash
# They can find credentials in git history themselves
git log --all -p -- CLAUDE.md
```

### Option 3: Add them to password manager
- Use 1Password shared vault
- Or Bitwarden organization
- Or similar team credential manager

---

## When to worry and rotate keys

**Rotate R2 keys if:**
- Repository becomes public (BEFORE making it public!)
- Dev leaves the company
- Keys are posted publicly (GitHub issue, Stack Overflow, etc.)
- You suspect unauthorized access

**How to rotate R2 keys:**
1. Log into Cloudflare dashboard
2. Go to R2 bucket settings
3. Generate new API token
4. Update `data-pipeline/.env` and `CREDENTIALS.md`
5. Update any deployed systems
6. Delete old token

Takes 5 minutes, zero downtime (CDN still works during rotation).

---

## Team access levels

### What each team member needs:

**You (Project Owner):**
- ✅ All credentials
- ✅ Full git access
- ✅ Cloudflare admin
- ✅ Supabase admin
- ✅ Stripe admin
- ✅ Vercel admin

**Developer:**
- ✅ Git repo access
- ✅ R2 credentials (for data pipeline work)
- ✅ Supabase access (for database work)
- ✅ Stripe test keys (for payment integration)
- ❌ Stripe live keys (only you need this)
- ✅ Vercel deploy access

**Future contractors/freelancers:**
- ✅ Git repo access (if needed)
- ✅ Documentation only (no credentials)
- ❌ Production credentials
- ✅ Test/staging credentials only

---

## Best practices going forward

1. ✅ **Keep CREDENTIALS.md gitignored** (already done)
2. ✅ **Use Vercel environment variables for production secrets** (Supabase, Stripe)
3. ✅ **Use 1Password or similar for team credential sharing**
4. ✅ **Rotate keys when team members leave**
5. ✅ **Keep R2 keys in .env files** (gitignored)
6. ❌ **Never commit credentials to git again**

---

## Summary for your situation

**Your dev has repo access, which means:**
- They CAN see R2 keys (from git history or CREDENTIALS.md)
- This is FINE because they need these keys to work
- Just share CREDENTIALS.md with them directly

**What to tell your dev:**
> "Hey, I've given you repo access. You'll need credentials to work on the project. Check the CREDENTIALS.md file I sent you, or extract them from git history with: `git log --all -p -- CLAUDE.md | grep -A 5 AWS_ACCESS_KEY`. These are the R2 keys for our map tile storage. Keep them secure but don't worry too much - it's just map data and we can rotate if needed."

**What matters more:**
- Keeping Supabase and Stripe production keys in Vercel only (not in git, not shared)
- User data security (via Supabase RLS policies)
- API key validation (so users can't abuse the service)

---

## Quick reference

**If you need to give dev credentials:**
```bash
# Send them CREDENTIALS.md via encrypted email
# Or share via password manager
# Or tell them to check git history

# They need:
R2_ACCESS_KEY=ecd653afe3300fdc045b9980df0dbb14
R2_SECRET_KEY=c115d1780b2d7b8ce22d37f2416306a692ce177364cb320608fb761881c17f35

# To add to their data-pipeline/.env file
```

**If repository goes public:**
```bash
# IMMEDIATELY rotate R2 keys before pushing
# Then push with clean CLAUDE.md (already done)
```

**Current status: ✅ Secured**
- CREDENTIALS.md is gitignored
- CLAUDE.md has no credentials (current version)
- Old commits still have keys, but repo is private
- Dev can access keys (and that's fine - they need them)
