# Multi-Agent Orchestration System

A serverless, domain-agnostic multi-agent orchestration platform built on AWS for civic engagement, disaster response, and community data processing.

## 🎯 Project Overview

This system enables users to submit unstructured reports (text + images) which are processed by specialized AI agents to extract structured data. Users can then query this data through natural language questions, with responses generated from multiple analytical perspectives using interrogative-based query agents.

## 🏗️ Architecture

- **Frontend**: Next.js web app (80% map, 20% chat)
- **Backend**: AWS serverless (Lambda, Step Functions, API Gateway)
- **AI/ML**: AWS Bedrock (Claude 3), Comprehend, Location Service
- **Data**: RDS PostgreSQL, OpenSearch, DynamoDB, S3
- **Real-Time**: AWS AppSync (WebSocket)

## 📋 Key Features

### Ingestion Pipeline
- Domain selection (Civic Complaints, Agriculture, Disaster Response)
- Text + image submission
- Parallel agent execution with dependency support
- Real-time status updates
- Structured data extraction (max 5 keys per agent)

### Query Pipeline
- 11 interrogative query agents (When, Where, Why, How, What, Who, Which, How Many, How Much, From Where, What Kind)
- Multi-perspective analysis
- Bullet point responses (one per agent)
- AI-generated summary
- Map visualization updates

### Custom Agents
- User-defined agents via dashboard
- Tool selection from registry
- Output schema builder (max 5 keys)
- Single-level dependency graphs
- Visual n8n-style editor

## 🚀 Quick Start

### Prerequisites
- AWS Account with appropriate permissions
- Node.js 18+ and npm
- Python 3.11+
- AWS CDK CLI installed
- AWS CLI configured

### Deployment

```bash
# Install dependencies
npm install

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy all stacks
cdk deploy --all

# Seed sample data
npm run seed-data

# Run smoke tests
npm run test-deployment
```

### Local Development

```bash
# Start frontend
cd frontend
npm install
npm run dev

# Frontend runs on http://localhost:3000
```

## 📁 Project Structure

```
.
├── .kiro/
│   ├── specs/multi-agent-orchestration-system/
│   │   ├── requirements.md          # 17 requirements
│   │   ├── design.md                # Architecture & design
│   │   ├── tasks.md                 # Implementation plan
│   │   └── diagrams/                # 16 component diagrams
│   └── steering/                    # Development guidelines
├── infrastructure/                  # AWS CDK code
│   ├── lib/
│   │   ├── stacks/                 # CDK stacks
│   │   └── constructs/             # Reusable constructs
│   └── bin/app.ts                  # CDK app entry
├── backend/                        # Lambda functions
│   ├── agents/                     # Agent implementations
│   ├── api/                        # API handlers
│   └── orchestration/              # Step Functions logic
├── frontend/                       # Next.js web app
│   ├── components/                 # React components
│   ├── pages/                      # Next.js pages
│   └── lib/                        # Utilities
└── README.md
```

## 🎬 Demo Flow (9 minutes)

### Part 1: Existing System (2 min)
- Submit civic complaint with image
- Show real-time agent execution
- Show Severity Classifier custom agent
- Show map marker with incident details

### Part 2: Query Data (2 min)
- Ask "What are the trends in pothole complaints?"
- Show interrogative agents executing
- Show bullet point response + summary
- Show map visualization

### Part 3: Create Custom Agent Live (3 min)
- Open configuration dashboard
- Create "Priority Scorer" agent
- Define system prompt, tools, output schema
- Set dependency on Temporal Agent
- Add to Civic Complaints playbook

### Part 4: Test New Agent (2 min)
- Submit new complaint
- Show Priority Scorer executing
- Show priority score in structured data
- Highlight extensibility

## 🏆 Hackathon Judging Criteria

- **Technical Execution (50%)**: AWS services, well-architected, reproducible
- **Value/Impact (20%)**: Multi-domain, civic engagement, measurable impact
- **Functionality (10%)**: Agents working, scalable, extensible
- **Creativity (10%)**: Interrogative agents, dependency graphs, live customization
- **Demo Presentation (10%)**: Clear workflow, real-time updates

## 📚 Documentation

- [Requirements](/.kiro/specs/multi-agent-orchestration-system/requirements.md)
- [Design Document](/.kiro/specs/multi-agent-orchestration-system/design.md)
- [Implementation Tasks](/.kiro/specs/multi-agent-orchestration-system/tasks.md)
- [Component Diagrams](/.kiro/specs/multi-agent-orchestration-system/diagrams/)

## 🛠️ Built With

- **AWS Services**: Lambda, Step Functions, API Gateway, AppSync, Cognito, RDS, OpenSearch, DynamoDB, S3, Bedrock, Comprehend, Location Service, EventBridge, Secrets Manager
- **Frontend**: Next.js, React, TypeScript, Mapbox GL JS, Apollo Client
- **Backend**: Python 3.11, Boto3, AWS CDK (TypeScript)
- **AI/ML**: AWS Bedrock (Claude 3 Sonnet), AWS Comprehend

## 📝 License

This project is created for the AWS AI Agent Hackathon.

## 🤝 Contributing

This is a hackathon project. For questions or issues, please contact the team.

---

**Status**: 🚧 In Development - Spec Complete, Ready for Implementation

**Next Step**: Open `.kiro/specs/multi-agent-orchestration-system/tasks.md` and start with Task 1.1
