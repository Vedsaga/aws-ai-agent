# Quick Start - Command Center Dashboard

## 🚀 Get Running in 4 Steps

```bash
# 1. Navigate to project
cd command-center-dashboard

# 2. Install dependencies (if not already done)
npm install

# 3. Add Mapbox token to .env.local (see MAPBOX_SETUP.md)
# Get free token from: https://account.mapbox.com/access-tokens/
# Add to .env.local: NEXT_PUBLIC_MAPBOX_TOKEN=pk.your_token_here

# 4. Start development server
npm run dev
```

Open http://localhost:3000

⚠️ **IMPORTANT:** You need a Mapbox token for the map to work. See `MAPBOX_SETUP.md` for step-by-step instructions (takes 2 minutes).

## 📁 Project Files

### Core Application (7 files)
- `app/page.tsx` - Main application
- `components/MapComponent.tsx` - Map view
- `components/ChatPanel.tsx` - Chat interface
- `components/AlertsPanel.tsx` - Alerts display
- `components/TimelineSlider.tsx` - Timeline control
- `store/useStore.ts` - State management
- `services/mockApiService.ts` - Mock API

### Data Files (3 files)
- `data/initial_load.json` - Initial view
- `data/food_water_response.json` - Query response
- `data/update_poll.json` - Real-time update

### Documentation (5 files)
- `README.md` - Full documentation
- `SETUP.md` - Setup guide
- `IMPLEMENTATION_STATUS.md` - Task checklist
- `DEMO_SCRIPT.md` - Presentation guide
- `PROJECT_SUMMARY.md` - Complete overview

## 🎯 Key Features

✅ 80/20 split layout (Map + Panel)
✅ Real-time data polling (5 seconds)
✅ Chat with suggested actions
✅ Critical alerts panel
✅ 7-day timeline slider
✅ Session persistence (localStorage)
✅ Mock API with dummy data

## 🧪 Test It Out

1. **Initial Load**: See critical incidents on map
2. **Chat Query**: Type "Show me all food and water needs"
3. **Suggested Action**: Click button below agent response
4. **Timeline**: Drag slider to navigate simulation
5. **Real-time**: Wait 5 seconds for updates (30% chance)
6. **Persistence**: Refresh page to see saved state

## 🛠️ Tech Stack

- Next.js 15 + TypeScript
- Mapbox GL JS
- Zustand (state)
- ShadCN/UI (components)
- Tailwind CSS v4

## 📊 Build Status

✅ TypeScript: No errors
✅ Build: Passing
✅ All requirements: Implemented

## 🔗 Next Steps

- Add real Mapbox token to `.env.local`
- Replace mock API with real backend
- Deploy to Vercel

## 📖 More Info

- Full docs: `README.md`
- Setup help: `SETUP.md`
- Demo guide: `DEMO_SCRIPT.md`
- Status: `IMPLEMENTATION_STATUS.md`
- Overview: `PROJECT_SUMMARY.md`

---

**Ready for hackathon demo! 🎉**
