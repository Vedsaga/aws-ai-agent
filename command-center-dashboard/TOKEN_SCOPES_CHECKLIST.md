# Mapbox Token Scopes Checklist

When creating your Mapbox token, make sure these scopes are checked:

## ✅ Public Scopes (Required)

Based on your screenshot, check these boxes:

```
Public scopes:
☑ STYLES:READ        (styles:read)
☑ FONTS:READ         (fonts:read)  
☑ DATASETS:READ      (datasets:read)
```

## ❌ Secret Scopes (NOT Needed)

Leave these UNCHECKED:

```
Secret scopes:
☐ SCOPES:LIST
☐ USER:WRITE
☐ ... (all others)
```

## Visual Guide

Your token creation screen should look like this:

```
┌─────────────────────────────────────────┐
│ Token name                              │
│ [command-center-dashboard        ] 24/128│
├─────────────────────────────────────────┤
│ Token scopes                            │
│                                         │
│ Public scopes                           │
│ ☑ STYLES:READ                          │
│ ☐ VISION:READ                          │
│ ☑ FONTS:READ                           │
│ ☐ SCOPES:LIST                          │
│ ☑ DATASETS:READ                        │
│                                         │
│ Secret scopes                           │
│ ☐ SCOPES:LIST                          │
│ ☐ USER:WRITE                           │
│ ... (leave all unchecked)              │
└─────────────────────────────────────────┘
```

## Important Notes

1. **Only check PUBLIC scopes** - The three listed above
2. **Leave SECRET scopes unchecked** - Not needed for browser use
3. **Token will start with `pk.`** - This confirms it's a public token
4. **Never use `sk.` tokens** - Those are secret tokens for servers only

## After Creating Token

Your token will look like:
```
pk.eyJ1IjoieW91cnVzZXJuYW1lIiwiYSI6ImNsZXhhbXBsZSJ9.example_rest_of_token
```

Copy the ENTIRE token and paste it into `.env.local`:
```
NEXT_PUBLIC_MAPBOX_TOKEN=pk.eyJ1IjoieW91cnVzZXJuYW1lIiwiYSI6ImNsZXhhbXBsZSJ9.example_rest_of_token
```

## Verification

✅ Token starts with `pk.`
✅ Token is on one line (no line breaks)
✅ No spaces before or after token
✅ File is named `.env.local` (note the dot at start)
✅ File is in project root (same folder as package.json)

## Restart Required

After adding the token:
```bash
# Stop the server (Ctrl+C)
npm run dev
```

The map should now load successfully! 🎉
