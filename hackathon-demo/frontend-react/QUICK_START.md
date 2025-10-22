# Quick Start Guide

## Prerequisites

- Node.js 18+ installed
- npm installed
- AWS backend infrastructure deployed
- Mapbox account with access token

## Installation

```bash
# Navigate to frontend directory
cd infrastructure/frontend

# Install dependencies
npm install
```

## Configuration

1. Copy the environment template:
```bash
cp .env.example .env.local
```

2. Edit `.env.local` with your values:
```bash
# Get these from your AWS CDK deployment outputs
NEXT_PUBLIC_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/api/v1
NEXT_PUBLIC_APPSYNC_URL=https://your-appsync-id.appsync-api.us-east-1.amazonaws.com/graphql
NEXT_PUBLIC_APPSYNC_REGION=us-east-1
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
NEXT_PUBLIC_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_COGNITO_REGION=us-east-1

# Get this from Mapbox (https://account.mapbox.com/)
NEXT_PUBLIC_MAPBOX_TOKEN=pk.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Running Locally

```bash
# Development mode (with hot reload)
npm run dev

# Open browser to http://localhost:3000
```

## Building for Production

```bash
# Build the application
npm run build

# Start production server
npm start

# Open browser to http://localhost:3000
```

## Testing the Application

### 1. Login
- Navigate to http://localhost:3000
- You'll be redirected to the login page
- Enter your Cognito credentials
- Click "Sign in"

### 2. Submit a Report
- After login, you'll see the dashboard
- Map takes up 80% of the screen (left)
- Chat interface is 20% (right)
- Click "Submit Report" tab
- Select a domain (e.g., "Civic Complaints")
- Enter report text: "Pothole on Main Street near the library"
- Optionally upload images (max 5, 5MB each)
- Click "Submit Report"
- Watch real-time status updates
- See success message with job ID
- Incident appears on map

### 3. Ask a Question
- Click "Ask Question" tab
- Select same domain
- Enter question: "What are the trends in pothole complaints?"
- Click "Ask Question"
- Watch real-time agent execution
- See bullet point analysis
- Read summary
- Map updates if spatial data present

### 4. Create Custom Agent
- Click "Configure Agents" button in header
- Click "Create Agent" tab
- Fill in form:
  - Name: "Priority Scorer"
  - Type: Custom
  - System Prompt: "Score complaint priority 1-10 based on severity and time"
  - Tools: Select "Bedrock"
  - Output Schema:
    - priority_score: number
    - reasoning: string
    - urgency: string
    - recommended_action: string
    - timeline: string
  - Parent Agent: Select "Temporal Agent"
- Click "Create Agent"
- See success message

### 5. View Dependency Graph
- Click "Dependency Graph" tab
- See all agents as nodes
- Drag from one agent to another to create dependency
- System validates single-level constraint
- See error if multi-level attempted
- Click "Remove" to delete dependency

## Troubleshooting

### "Map not loading"
- Check `NEXT_PUBLIC_MAPBOX_TOKEN` is set correctly
- Verify token at https://account.mapbox.com/
- Check browser console for errors

### "Login fails"
- Verify Cognito User Pool ID and Client ID
- Check user exists in Cognito
- Ensure password meets requirements (8+ chars, upper, lower, number, special)

### "Real-time updates not working"
- Check AppSync URL and region
- Verify WebSocket connection in browser DevTools (Network tab)
- Ensure user is authenticated

### "API requests fail"
- Check API Gateway URL
- Verify backend is deployed
- Check CORS configuration
- Look for JWT token in request headers

### "Dependencies not installing"
- Clear npm cache: `npm cache clean --force`
- Delete node_modules: `rm -rf node_modules`
- Reinstall: `npm install`

## Development Tips

### Hot Reload
- Changes to files automatically reload the page
- No need to restart dev server

### TypeScript Errors
- Run type check: `npx tsc --noEmit`
- Fix errors before building

### Linting
- Run linter: `npm run lint`
- Auto-fix: `npm run lint -- --fix`

### Component Development
- Components are in `components/` directory
- Use TypeScript for type safety
- Follow existing patterns

### API Integration
- API client is in `lib/api-client.ts`
- Add new endpoints there
- Use type-safe responses

## Deployment Options

### Option 1: Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Follow prompts to configure
```

### Option 2: AWS Amplify Hosting
1. Go to AWS Amplify Console
2. Connect GitHub repository
3. Configure build settings:
   - Build command: `npm run build`
   - Output directory: `.next`
4. Add environment variables
5. Deploy

### Option 3: Docker
```bash
# Build Docker image
docker build -t multi-agent-frontend .

# Run container
docker run -p 3000:3000 multi-agent-frontend
```

### Option 4: S3 + CloudFront
```bash
# Build static export
npm run build

# Upload to S3
aws s3 sync .next/static s3://your-bucket/static

# Configure CloudFront distribution
```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | API Gateway endpoint | `https://abc123.execute-api.us-east-1.amazonaws.com/api/v1` |
| `NEXT_PUBLIC_APPSYNC_URL` | AppSync GraphQL endpoint | `https://xyz789.appsync-api.us-east-1.amazonaws.com/graphql` |
| `NEXT_PUBLIC_APPSYNC_REGION` | AWS region for AppSync | `us-east-1` |
| `NEXT_PUBLIC_COGNITO_USER_POOL_ID` | Cognito User Pool ID | `us-east-1_AbCdEfGhI` |
| `NEXT_PUBLIC_COGNITO_CLIENT_ID` | Cognito App Client ID | `1a2b3c4d5e6f7g8h9i0j` |
| `NEXT_PUBLIC_COGNITO_REGION` | AWS region for Cognito | `us-east-1` |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | Mapbox access token | `pk.eyJ1IjoiZXhhbXBsZSIsImEiOiJjbGV4YW1wbGUifQ.example` |

## File Structure

```
frontend/
├── app/                    # Next.js pages
│   ├── login/             # Login page
│   ├── dashboard/         # Main dashboard
│   ├── config/            # Agent configuration
│   └── page.tsx           # Home (redirects)
├── components/            # React components
│   ├── MapView.tsx        # Map visualization
│   ├── IngestionPanel.tsx # Report submission
│   ├── QueryPanel.tsx     # Question asking
│   ├── AgentCreationForm.tsx # Agent creation
│   └── DependencyGraphEditor.tsx # Graph editor
├── lib/                   # Utilities
│   ├── amplify-config.ts  # AWS Amplify setup
│   ├── appsync-client.ts  # WebSocket client
│   ├── api-client.ts      # REST API client
│   └── auth.ts            # Authentication
└── public/                # Static assets
```

## Next Steps

1. **Customize Domains**: Add your own domain configurations
2. **Create Agents**: Build custom agents for your use case
3. **Configure Playbooks**: Set up domain-specific workflows
4. **Test End-to-End**: Submit reports and query data
5. **Deploy**: Choose deployment option and go live

## Support

For issues or questions:
1. Check the main README.md
2. Review IMPLEMENTATION_SUMMARY.md
3. Check browser console for errors
4. Verify environment variables
5. Ensure backend is deployed and accessible

## Demo Checklist

Before the hackathon demo:
- [ ] Backend deployed and accessible
- [ ] Environment variables configured
- [ ] Mapbox token valid
- [ ] Test user created in Cognito
- [ ] Sample data loaded
- [ ] Login works
- [ ] Report submission works
- [ ] Query works
- [ ] Agent creation works
- [ ] Dependency graph works
- [ ] Map displays incidents
- [ ] Real-time updates working

## Performance Tips

- Use production build for demos (`npm run build && npm start`)
- Ensure good internet connection for map tiles
- Pre-load sample data for faster demo
- Test on target browser beforehand
- Have backup screenshots ready

Good luck with your demo! 🚀
