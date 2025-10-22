# DomainFlow Hackathon Demo - Documentation Index

## Quick Links

### Getting Started
- **[README.md](README.md)** - Start here! Overview and quick intro
- **[QUICK_START.md](QUICK_START.md)** - Step-by-step setup guide (30 min)
- **[quick-deploy.sh](quick-deploy.sh)** - Fastest deployment (5-10 min)
- **[CHANGES.md](CHANGES.md)** - Recent updates (multi-agent architecture)

### Demo Preparation
- **[DEMO_SCRIPT.md](DEMO_SCRIPT.md)** - Full 5-minute presentation script
- **[DEMO_CHECKLIST.md](DEMO_CHECKLIST.md)** - Pre-demo checklist and troubleshooting
- **[VISUAL_FLOW.md](VISUAL_FLOW.md)** - ASCII diagrams of complete flow

### Technical Documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and data flow
- **[COMPARISON.md](COMPARISON.md)** - Hackathon demo vs full system
- **[agent-definitions.json](agent-definitions.json)** - Agent prompts and configs

### Testing
- **[test-api.sh](test-api.sh)** - Shell script to test all endpoints
- **[test-client.py](test-client.py)** - Python test client with examples

### Code
- **[lambda/orchestrator.py](lambda/orchestrator.py)** - Main Lambda function
- **[cdk/app.py](cdk/app.py)** - Infrastructure as code
- **[frontend/index.html](frontend/index.html)** - Single-page UI

## Document Purpose Guide

### I want to...

**...understand the concept**
→ Read [README.md](README.md) sections: "What This Is" and "3 Meta Agent Classes"

**...deploy the demo**
→ Follow [QUICK_START.md](QUICK_START.md) steps 1-3

**...prepare for presentation**
→ Use [DEMO_SCRIPT.md](DEMO_SCRIPT.md) and [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md)

**...understand the architecture**
→ Read [ARCHITECTURE.md](ARCHITECTURE.md) and [VISUAL_FLOW.md](VISUAL_FLOW.md)

**...test the API**
→ Run [test-api.sh](test-api.sh) or [test-client.py](test-client.py)

**...compare to full system**
→ Read [COMPARISON.md](COMPARISON.md)

**...modify agent behavior**
→ Edit [agent-definitions.json](agent-definitions.json) or [lambda/orchestrator.py](lambda/orchestrator.py)

**...customize the UI**
→ Edit [frontend/index.html](frontend/index.html)

**...change infrastructure**
→ Edit [cdk/app.py](cdk/app.py)

## File Structure

```
hackathon-demo/
│
├── 📄 Documentation (you are here)
│   ├── INDEX.md                 ← Navigation guide
│   ├── README.md                ← Start here
│   ├── QUICK_START.md           ← Setup guide
│   ├── DEMO_SCRIPT.md           ← Presentation script
│   ├── DEMO_CHECKLIST.md        ← Pre-demo checklist
│   ├── ARCHITECTURE.md          ← Technical details
│   ├── COMPARISON.md            ← Demo vs full system
│   └── VISUAL_FLOW.md           ← Flow diagrams
│
├── 🔧 Configuration
│   ├── agent-definitions.json   ← Agent prompts
│   └── .gitignore               ← Git ignore rules
│
├── 🚀 Deployment
│   └── deploy.sh                ← One-command deploy
│
├── 🧪 Testing
│   ├── test-api.sh              ← Shell tests
│   └── test-client.py           ← Python tests
│
├── ☁️ Infrastructure (CDK)
│   └── cdk/
│       ├── app.py               ← Stack definition
│       ├── cdk.json             ← CDK config
│       └── requirements.txt     ← Python deps
│
├── ⚡ Backend (Lambda)
│   └── lambda/
│       ├── orchestrator.py      ← Main function
│       └── requirements.txt     ← Python deps
│
└── 🎨 Frontend (HTML)
    └── frontend/
        └── index.html           ← Single-page app
```

## Reading Order

### For First-Time Users
1. [README.md](README.md) - Understand the concept
2. [QUICK_START.md](QUICK_START.md) - Deploy the demo
3. [test-api.sh](test-api.sh) - Test it works
4. [frontend/index.html](frontend/index.html) - Try the UI

### For Presenters
1. [DEMO_SCRIPT.md](DEMO_SCRIPT.md) - Learn the script
2. [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md) - Prepare everything
3. [VISUAL_FLOW.md](VISUAL_FLOW.md) - Understand the flow
4. [ARCHITECTURE.md](ARCHITECTURE.md) - Know the details (for Q&A)

### For Developers
1. [ARCHITECTURE.md](ARCHITECTURE.md) - System design
2. [lambda/orchestrator.py](lambda/orchestrator.py) - Core logic
3. [cdk/app.py](cdk/app.py) - Infrastructure
4. [COMPARISON.md](COMPARISON.md) - What's missing

### For Decision Makers
1. [README.md](README.md) - Value proposition
2. [COMPARISON.md](COMPARISON.md) - Demo vs production
3. [ARCHITECTURE.md](ARCHITECTURE.md) - Cost & scale section

## Key Concepts

### 3 Meta Agent Classes
- **Data-Ingestion**: CREATE - Extract structured data from text
- **Data-Query**: READ - Answer questions about data
- **Data-Management**: UPDATE - Modify existing data

### Core Innovation
Traditional apps: Build new API for every feature
DomainFlow: Configure new agent with prompt

### Demo Limitations
- No authentication (would use Cognito)
- No multi-tenancy (would use tenant_id)
- Simple DynamoDB scan (would use GSI)
- Mock geocoding (would use AWS Location)

### Production Path
Demo → MVP (2 weeks) → Production (6 weeks) → Scale (12 weeks)

## Common Questions

**Q: How long to deploy?**
A: 5-10 minutes with `./deploy.sh`

**Q: What does it cost?**
A: ~$6/month for demo usage (100 requests/day)

**Q: Can I customize agents?**
A: Yes! Edit `agent-definitions.json` or `lambda/orchestrator.py`

**Q: How do I add a new domain?**
A: Change the agent prompts. Same code, different domain.

**Q: Is this production-ready?**
A: No. This is a demo. See [COMPARISON.md](COMPARISON.md) for what's missing.

**Q: Where's the full system?**
A: In the parent directory (`../infrastructure`)

**Q: Can I use this commercially?**
A: Check the license in the parent directory

## Support

### Issues During Setup
1. Check [QUICK_START.md](QUICK_START.md) troubleshooting section
2. Check [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md) technical troubleshooting
3. Review CloudWatch logs: `aws logs tail /aws/lambda/domainflow-orchestrator`

### Issues During Demo
1. Check [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md) backup plans
2. Have pre-recorded video ready
3. Show code/architecture instead

### Questions About Architecture
1. Read [ARCHITECTURE.md](ARCHITECTURE.md)
2. Check [VISUAL_FLOW.md](VISUAL_FLOW.md) diagrams
3. Review [COMPARISON.md](COMPARISON.md) for context

## Next Steps

After successful demo:
1. Share GitHub repo
2. Collect feedback
3. Consider production deployment (see [COMPARISON.md](COMPARISON.md))
4. Explore full system in parent directory

## Updates

This demo was created for hackathon/quick proof-of-concept purposes.

For the full production system, see:
- `../infrastructure` - Full CDK stacks
- `../diagrams` - Detailed architecture diagrams
- `../README.md` - Main project documentation

---

**Last Updated:** October 23, 2025
**Version:** 1.0 (Hackathon Demo)
**Status:** Ready for demo
