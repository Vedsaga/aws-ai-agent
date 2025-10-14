# Troubleshooting Guide

## ✅ Fixes Applied

1. **Removed turbopack** - Was causing CSS compilation issues
2. **Removed tw-animate-css** - Incompatible with Tailwind v4
3. **Simplified CSS** - Using standard Tailwind v4 syntax
4. **Added dark class** - Properly enables dark theme
5. **Build succeeds** - No compilation errors

## 🚀 How to Start the App

### Step 1: Clean Start
```bash
cd command-center-dashboard

# Remove old build files
rm -rf .next

# Start the dev server
npm run dev
```

### Step 2: Open Browser
Go to: http://localhost:3000

## 🔍 What to Check

### If you see a black screen:
1. Open browser DevTools (F12)
2. Check the Console tab for errors
3. Check the Network tab to see if files are loading

### If map shows error message:
✅ This is EXPECTED! The error message will guide you to add the Mapbox token.
- Your token is already in `.env.local`
- Just restart the dev server: `npm run dev`

### If you see "Module not found" errors:
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## 📋 Checklist

Before starting, verify:

- [ ] You're in the `command-center-dashboard` directory
- [ ] `.env.local` has your Mapbox token (starts with `pk.`)
- [ ] No other process is using port 3000
- [ ] Node.js version is 18 or higher: `node --version`

## 🐛 Common Issues

### Issue: Port 3000 already in use
```bash
# Find and kill the process
lsof -ti:3000 | xargs kill -9

# Or use a different port
npm run dev -- -p 3001
```

### Issue: CSS not loading
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

### Issue: TypeScript errors
```bash
# Check for errors
npm run build

# If build succeeds, the app will work
```

### Issue: Map not loading
1. Check `.env.local` has the token
2. Token should start with `pk.` not `sk.`
3. Restart dev server after adding token
4. Check browser console for Mapbox errors

## 📊 Expected Behavior

### On First Load:
1. Dark themed UI appears
2. Right panel shows:
   - Empty alerts section
   - Chat with welcome message
   - Timeline slider at bottom
3. Left side shows:
   - Either the map with data
   - OR helpful error message about token

### After Adding Token:
1. Map loads with dark theme
2. Critical incidents appear as red circles
3. Chat shows welcome message
4. Everything is interactive

## 🎯 Quick Test

After starting the server, you should see:

✅ Dark background (not white)
✅ Visible text (light colored)
✅ Buttons with borders
✅ Input field you can type in
✅ Timeline slider at bottom

If you see all of these, the UI is working!

## 🔧 Advanced Debugging

### Check if Next.js is running:
```bash
ps aux | grep next
```

### Check what's on port 3000:
```bash
curl http://localhost:3000
```

### View full build output:
```bash
npm run build
```

### Check environment variables:
```bash
cat .env.local
```

## 📞 Still Having Issues?

1. **Take a screenshot** of:
   - The browser window
   - Browser DevTools Console tab
   - Terminal where `npm run dev` is running

2. **Check these files exist**:
   - `app/page.tsx`
   - `app/layout.tsx`
   - `app/globals.css`
   - `.env.local`
   - `components/MapComponent.tsx`

3. **Verify the build works**:
   ```bash
   npm run build
   ```
   If this succeeds, the app will work in dev mode too.

## ✨ Success Indicators

You'll know it's working when:

1. Terminal shows: `✓ Ready in X ms`
2. Browser shows dark UI with visible text
3. No red errors in browser console
4. Map either loads OR shows helpful setup message

---

**The app is ready to run!** Just start it with `npm run dev` and open http://localhost:3000
