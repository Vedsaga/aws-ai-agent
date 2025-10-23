# 🏙️ Civic Sense - AI-Powered Civic Engagement Platform

Multi-agent orchestration system for civic issue reporting, querying, and management.

## ✅ Status: READY TO DEMO

- **Backend**: Deployed & Tested ✅
- **Frontend**: Configured & Ready ✅
- **API**: https://tzbw0aw913.execute-api.us-east-1.amazonaws.com/prod/

## 🚀 Quick Start (2 Steps)

### 1. Get Mapbox Token (1 minute)
```bash
# Visit: https://account.mapbox.com/access-tokens/
# Sign up (free tier: 50k loads/month)
# Copy your token
```

### 2. Start Frontend
```bash
cd frontend-react

# Edit .env.local and paste your Mapbox token
nano .env.local

# Install and run
npm install
npm run dev

# Open: http://localhost:3000
```

## 🎯 Features

### 📝 Report Mode
- Citizens report civic issues
- AI extracts location, entity, severity
- Real-time agent execution visible
- Pins drop on map automatically

### 🔍 Query Mode
- Natural language queries
- Multi-agent analysis
- AI-generated summaries
- Filtered map visualization

### ⚙️ Manage Mode
- Assign reports to teams
- Update status
- Real-time map updates
- Status rings on pins

## 🗺️ Map Features

**Severity Pins:**
- 🔴 Critical (red)
- 🟠 High (orange)
- 🟡 Medium (yellow)
- 🟢 Low (green)

**Status Rings:**
- 🟡 Amber = Pending
- 🔵 Blue = In Progress
- 🟢 Green = Resolved

**Smart Features:**
- Auto-fit bounds for multiple reports
- Click pins for detailed popups
- Navigation controls
- Fullscreen mode

## 🤖 AI Orchestration

**Ingestion Agents:**
- Geo Agent (location extraction)
- Entity Agent (issue identification)
- Severity Agent (urgency assessment)
- Verifier (confidence checking)

**Query Agents:**
- What Agent (incident analysis)
- Where Agent (location analysis)
- When Agent (temporal patterns)
- Verifier (answer synthesis)

**Management:**
- Command parsing
- Database updates
- Status tracking

## 🏗️ Architecture

**Backend:**
- AWS Lambda (Python 3.11)
- DynamoDB (storage)
- API Gateway (REST)
- EventBridge (real-time)
- Bedrock Nova Pro/Lite (AI)

**Frontend:**
- Next.js 14
- Mapbox GL JS
- Tailwind CSS
- TypeScript

## 📁 Project Structure

```
hackathon-demo/
├── cdk/                    # Backend infrastructure
├── lambda/                 # Lambda functions
├── frontend-react/         # Frontend app
├── deploy-backend.sh       # Deploy script
├── test-backend.sh         # Test script
└── START_FRONTEND.sh       # Frontend launcher
```

## 🧪 Testing

### Backend
```bash
./test-backend.sh
```

### Frontend Manual Test
1. Open http://localhost:3000
2. Report: "Pothole at 789 Pine Street, urgent"
3. Watch agents execute
4. See pin on map
5. Query: "Show all reports"
6. Manage: "Assign report [ID] to Team A"

## 📚 Documentation

- `COMPLETE_SETUP.txt` - Full setup guide
- `FRONTEND_GUIDE.txt` - Frontend details
- `DEPLOYMENT_SUCCESS.txt` - Backend verification

## 🎓 Demo Script

See `COMPLETE_SETUP.txt` for a complete demo walkthrough.

## 💡 Sample Queries

**Report Mode:**
- "Broken streetlight at 123 Main St"
- "Pothole on Oak Street, very dangerous"
- "Graffiti on building wall, needs cleanup"

**Query Mode:**
- "Show me all high severity issues"
- "What reports are on Main Street?"
- "How many critical issues do we have?"

**Manage Mode:**
- "Assign report [ID] to Team B"
- "Mark report [ID] as in progress"
- "Set report [ID] due in 48 hours"

## 🔧 Troubleshooting

**Map not showing?**
- Check Mapbox token in `.env.local`

**No pins?**
- Create a report first
- Check browser console

**Backend errors?**
- Run `./test-backend.sh`
- Check API URL in `.env.local`

## 📊 Current Data

3 sample reports in database:
1. Pothole on Oak Street (high)
2. Broken streetlight at 456 Elm Street (medium, Team B)
3. Graffiti on Main Street (low)

## 🎨 Layout

- **80% Left**: Interactive map with real-time pins
- **20% Right**: AI chat assistant
- **Top Left**: Domain selector (Civic Sense)
- **Bottom Right**: Mode selector with icons

## 🌟 Key Highlights

- ✅ Single-page application
- ✅ Real-time agent transparency
- ✅ Color-coded severity system
- ✅ Status tracking with visual rings
- ✅ Auto-fit map bounds
- ✅ Multi-agent orchestration
- ✅ Natural language interface
- ✅ Serverless architecture

---

**Ready to demo!** 🚀
