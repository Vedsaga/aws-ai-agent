# Mapbox Token Setup Guide

## Quick Fix for Map Error

The map needs a valid Mapbox public token. Here's how to get one (takes 2 minutes):

### Step 1: Create a Mapbox Account (if needed)
1. Go to https://www.mapbox.com/
2. Click "Sign up" (it's free!)
3. Verify your email

### Step 2: Create a Public Token
1. Go to https://account.mapbox.com/access-tokens/
2. Click "Create a token" button
3. Give it a name: `command-center-dashboard`

### Step 3: Select Required Scopes
In the "Public scopes" section, make sure these are checked:
- ✅ **STYLES:READ** (styles:read)
- ✅ **FONTS:READ** (fonts:read)
- ✅ **DATASETS:READ** (datasets:read)

See the screenshot you provided - these are the ones you need!

### Step 4: Create and Copy Token
1. Scroll down and click "Create token"
2. Copy the token (it starts with `pk.`)

### Step 5: Add to Your Project
1. Open `.env.local` in the project root
2. Replace the line:
   ```
   NEXT_PUBLIC_MAPBOX_TOKEN=
   ```
   with:
   ```
   NEXT_PUBLIC_MAPBOX_TOKEN=pk.your_actual_token_here
   ```

### Step 6: Restart Dev Server
```bash
# Stop the current server (Ctrl+C)
# Then restart:
npm run dev
```

## Important Notes

⚠️ **Never use secret tokens (sk.*) in browser code!**
- Secret tokens are for server-side use only
- Public tokens (pk.*) are safe for browser use
- The error you saw was because a secret token was used

✅ **Your token is safe to commit**
- Public tokens are designed for client-side use
- They're restricted by URL and scope
- Still, you can add `.env.local` to `.gitignore` if you prefer

## Troubleshooting

### "Invalid token" error
- Make sure you copied the entire token
- Token should start with `pk.`
- No extra spaces before or after

### Map still not loading
- Clear browser cache
- Check browser console for errors
- Verify token scopes are correct

### Token not found
- Make sure `.env.local` is in the project root (same folder as `package.json`)
- Restart the dev server after adding the token
- Check that the variable name is exactly `NEXT_PUBLIC_MAPBOX_TOKEN`

## Alternative: Use Demo Mode

If you want to demo without a map temporarily, you can modify the app to show a placeholder. But getting a real token only takes 2 minutes and makes the demo much better!

## Free Tier Limits

Mapbox free tier includes:
- 50,000 map loads per month
- More than enough for development and demos
- No credit card required

---

Need help? The error message in the browser will guide you through these steps!
