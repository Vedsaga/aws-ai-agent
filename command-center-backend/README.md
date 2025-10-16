# Command Center Backend

AWS CDK-based backend API for the Command Center disaster response dashboard.

## 🚀 Quick Start

```bash
# 1. Deploy everything (checks prerequisites, builds, deploys, populates database)
./deploy.sh

# 2. Test the API
./test-api.sh
```

**Time**: ~10-15 minutes for first deployment

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Project Structure](#-project-structure)
- [Key Features](#-key-features)
- [Common Commands](#-common-commands)
- [API Overview](#-api-overview)
- [Documentation](#-documentation)

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                                │
│                                                                   │
│  ┌──────────────┐      ┌─────────────────────────────────────┐ │
│  │              │      │                                       │ │
│  │  API Gateway │─────▶│  Lambda Functions                    │ │
│  │  (REST API)  │      │  ┌─────────────────────────────────┐ │ │
│  │              │      │  │ 1. UpdatesHandler               │ │ │
│  │  + API Key   │      │  │    - Query DynamoDB             │ │ │
│  │    Auth      │      │  │    - Return event updates       │ │ │
│  │              │      │  └─────────────────────────────────┘ │ │
│  └──────────────┘      │  ┌─────────────────────────────────┐ │ │
│         │              │  │ 2. QueryHandler                 │ │ │
│         │              │  │    - Invoke Bedrock Agent       │ │ │
│         │              │  │    - Process NL queries         │ │ │
│         │              │  └─────────────────────────────────┘ │ │
│         │              │  ┌─────────────────────────────────┐ │ │
│         │              │  │ 3. ActionHandler                │ │ │
│         │              │  │    - Execute pre-defined actions│ │ │
│         │              │  └─────────────────────────────────┘ │ │
│         │              │  ┌─────────────────────────────────┐ │ │
│         │              │  │ 4. DatabaseToolHandler          │ │ │
│         │              │  │    - Bedrock Agent tool         │ │ │
│         │              │  │    - Query database for agent   │ │ │
│         │              │  └─────────────────────────────────┘ │ │
│         │              └──────────────┬──────────────────────┘ │
│         │                             │                         │
│         │                             │                         │
│         ▼                             ▼                         │
│  ┌──────────────┐              ┌──────────────┐               │
│  │              │              │              │               │
│  │  DynamoDB    │◀─────────────│  Bedrock     │               │
│  │              │              │  Agent       │               │
│  │  - Events    │              │              │               │
│  │  - Timeline  │              │  + Claude 3  │               │
│  │  - GSI       │              │    Sonnet    │               │
│  │              │              │              │               │
│  └──────────────┘              └──────────────┘               │
│                                                                 │
│  ┌──────────────┐              ┌──────────────┐               │
│  │              │              │              │               │
│  │  CloudWatch  │              │  CloudWatch  │               │
│  │  Alarms      │              │  Logs        │               │
│  │              │              │              │               │
│  │  - Budget    │              │  - Lambda    │               │
│  │  - Costs     │              │  - API GW    │               │
│  │              │              │              │               │
│  └──────────────┘              └──────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
Frontend Dashboard
       │
       │ HTTPS + API Key
       ▼
┌─────────────────┐
│  API Gateway    │
│  /data/updates  │──┐
│  /agent/query   │  │
│  /agent/action  │  │
└─────────────────┘  │
                     │
       ┌─────────────┴─────────────┬─────────────────┐
       │                           │                 │
       ▼                           ▼                 ▼
┌──────────────┐          ┌──────────────┐   ┌──────────────┐
│ Updates      │          │ Query        │   │ Action       │
│ Handler      │          │ Handler      │   │ Handler      │
└──────┬───────┘          └──────┬───────┘   └──────┬───────┘
       │                         │                   │
       │ Query                   │ Invoke            │ Invoke
       ▼                         ▼                   ▼
┌──────────────┐          ┌──────────────────────────────────┐
│  DynamoDB    │          │      Bedrock Agent               │
│              │          │                                  │
│  Events by   │◀─────────│  + Action Group                  │
│  Day + Time  │  Tool    │  + Database Tool (Lambda)        │
│              │  Call    │  + Claude 3 Sonnet               │
└──────────────┘          └──────────────────────────────────┘
```

### DynamoDB Schema

```
Table: MasterEventTimeline
┌─────────────────────────────────────────────────────────┐
│ Partition Key: Day (String)    e.g., "DAY_0", "DAY_1"  │
│ Sort Key: Timestamp (String)   e.g., "2023-02-06T..."  │
├─────────────────────────────────────────────────────────┤
│ Attributes:                                             │
│  - eventId: String                                      │
│  - domain: String (MEDICAL, FIRE, STRUCTURAL, etc.)     │
│  - severity: String (CRITICAL, HIGH, MEDIUM, LOW)       │
│  - summary: String                                      │
│  - geojson: String (GeoJSON geometry)                   │
│  - resourcesNeeded: List<String>                        │
│  - affectedPopulation: Number                           │
│  - location: Map                                        │
└─────────────────────────────────────────────────────────┘

Global Secondary Index: DomainIndex
┌─────────────────────────────────────────────────────────┐
│ Partition Key: domain                                   │
│ Sort Key: Timestamp                                     │
│ Purpose: Query events by domain efficiently             │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

- **Node.js 18+** and npm
- **AWS CLI** configured with credentials
- **AWS CDK** installed globally: `npm install -g aws-cdk`
- **Bedrock Access**: Request Claude 3 Sonnet access in AWS Console (one-time)

Check prerequisites:
```bash
# The deploy script checks these automatically
./deploy.sh
```

---

## 📁 Project Structure

```
command-center-backend/
├── lib/
│   ├── command-center-backend-stack.ts  # CDK infrastructure
│   ├── lambdas/                         # Lambda handlers
│   │   ├── updatesHandler.ts            # GET /data/updates
│   │   ├── queryHandler.ts              # POST /agent/query
│   │   ├── actionHandler.ts             # POST /agent/action
│   │   └── databaseToolHandler.ts       # Bedrock Agent tool
│   ├── types/                           # TypeScript types
│   └── agent/                           # Bedrock Agent config
├── scripts/
│   ├── prepare-lambda-bundle.sh         # Bundle dependencies
│   ├── populate-database.ts             # Generate test data
│   └── generate-simulation-data.ts      # Simulation data generator
├── deploy.sh                            # Main deployment script
├── test-api.sh                          # API testing script
├── lambda-bundle/                       # Lambda deployment package (auto-generated)
├── .env.local                           # API credentials (auto-generated)
├── README.md                            # This file
├── DEPLOYMENT.md                        # Deployment guide
└── API.md                               # API documentation
```

---

## 🔧 Key Features

- **DynamoDB**: Event timeline storage with GSI for efficient queries
- **Lambda Functions**: 4 handlers (updates, query, action, database tool)
- **API Gateway**: REST API with API key authentication
- **Bedrock Agent**: AI-powered natural language query processing
- **Cost Monitoring**: Budget alarms and automatic alerts
- **Dependency Bundling**: Automatic bundling of node_modules for Lambda

---

## 🎯 Common Commands

```bash
# Deployment
./deploy.sh                      # Full deployment (build + deploy + populate)
./deploy.sh --skip-populate      # Deploy without populating database
./deploy.sh --stage prod         # Deploy to production

# Testing
./test-api.sh                    # Test all API endpoints
npm run test:api                 # Same as above

# Development
npm run build                    # Compile TypeScript
npm run bundle                   # Bundle Lambda code with dependencies
npm run deploy:quick             # Deploy without re-bundling
npm run populate-db              # Generate and insert simulation data

# Monitoring
aws logs tail /aws/lambda/CommandCenterBackend-Dev-QueryHandler --follow

# Cleanup
cdk destroy                      # Remove all AWS resources
```

---

## 🌐 API Overview

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/data/updates` | Get event updates since timestamp |
| POST | `/agent/query` | Natural language query processing |
| POST | `/agent/action` | Execute pre-defined actions |

### Authentication

All requests require an API key in the header:
```bash
x-api-key: your-api-key-here
```

### Quick Test

```bash
# Load credentials
source .env.local

# Test API
curl -X GET "${API_ENDPOINT}/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}"
```

**See [API.md](./API.md) for complete API documentation with sequence diagrams.**

---

## 📚 Documentation

| File | Description |
|------|-------------|
| **[DEPLOYMENT.md](./DEPLOYMENT.md)** | Complete deployment guide with troubleshooting |
| **[API.md](./API.md)** | API reference with examples and sequence diagrams |

### Quick Links

- **First-time setup**: See [DEPLOYMENT.md](./DEPLOYMENT.md#-quick-start-2-steps)
- **API integration**: See [API.md](./API.md#-endpoints)
- **Troubleshooting**: See [DEPLOYMENT.md](./DEPLOYMENT.md#-troubleshooting)
- **Testing**: Run `./test-api.sh`

---

## 🔐 API Credentials

After deployment, credentials are saved to `.env.local`:

```bash
API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/dev
API_KEY=xxxxxxxxxxxxx
```

Copy these to your frontend `.env.local`:
```bash
NEXT_PUBLIC_API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/dev
NEXT_PUBLIC_API_KEY=xxxxxxxxxxxxx
```

---

## 💰 Cost Estimate

- **Development**: ~$5-10/month
- **Production**: ~$20-50/month (with traffic)
- **Budget Alarm**: Set at $50 USD

Main costs: Bedrock Agent invocations, Lambda, DynamoDB

---

## ✅ Deployment Checklist

- [ ] Prerequisites installed
- [ ] AWS credentials configured
- [ ] Bedrock Claude 3 Sonnet access requested
- [ ] Run `./deploy.sh`
- [ ] Run `./test-api.sh`
- [ ] Share API credentials with frontend team

---

## 🆘 Support

- **Deployment Issues**: See [DEPLOYMENT.md](./DEPLOYMENT.md#-troubleshooting)
- **API Questions**: See [API.md](./API.md)
- **Check Logs**: `aws logs tail /aws/lambda/CommandCenterBackend-Dev-QueryHandler --follow`

---

**Version**: 2.0.0 (with dependency bundling fix)  
**Last Updated**: 2025-10-16
