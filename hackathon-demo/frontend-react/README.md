# Multi-Agent Orchestration System - Frontend

Next.js web application for the Multi-Agent Orchestration System, featuring map-based visualization (80% of UI) and chat interface (20% of UI) for civic engagement and disaster response.

## Features

- **Authentication**: AWS Cognito integration with JWT token management
- **Map Visualization**: Mapbox GL JS for displaying incidents with clustering and popups
- **Ingestion Interface**: Submit reports with text and images (max 5, 5MB each)
- **Query Interface**: Ask natural language questions with multi-perspective analysis
- **Real-time Updates**: AppSync WebSocket for live status updates during processing
- **Agent Configuration**: Create custom agents with visual dependency graph editor
- **Responsive Design**: Tailwind CSS for modern, responsive UI

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Map**: Mapbox GL JS
- **Auth**: AWS Amplify (Cognito)
- **Real-time**: AWS AppSync (GraphQL WebSocket)
- **Graph Editor**: ReactFlow
- **State Management**: React Hooks

## Prerequisites

- Node.js 18+ and npm
- AWS account with deployed backend infrastructure
- Mapbox account and access token

## Environment Variables

Create a `.env.local` file in the `frontend` directory:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://your-api-gateway-url.amazonaws.com/api/v1

# AWS AppSync Configuration
NEXT_PUBLIC_APPSYNC_URL=https://your-appsync-api.appsync-api.us-east-1.amazonaws.com/graphql
NEXT_PUBLIC_APPSYNC_REGION=us-east-1

# AWS Cognito Configuration
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
NEXT_PUBLIC_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_COGNITO_REGION=us-east-1

# Mapbox Configuration
NEXT_PUBLIC_MAPBOX_TOKEN=pk.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── app/                      # Next.js App Router pages
│   ├── login/               # Login page
│   ├── dashboard/           # Main dashboard (map + chat)
│   ├── config/              # Agent configuration page
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Home page (redirects)
│   └── globals.css          # Global styles
├── components/              # React components
│   ├── MapView.tsx          # Mapbox map with incident markers
│   ├── IngestionPanel.tsx   # Report submission interface
│   ├── QueryPanel.tsx       # Question asking interface
│   ├── AgentCreationForm.tsx # Custom agent creation form
│   └── DependencyGraphEditor.tsx # Visual dependency graph
├── lib/                     # Utility libraries
│   ├── amplify-config.ts    # AWS Amplify configuration
│   ├── appsync-client.ts    # AppSync WebSocket client
│   ├── api-client.ts        # REST API client
│   └── auth.ts              # Authentication utilities
└── public/                  # Static assets
```

## Key Components

### Dashboard (`/dashboard`)
- **Map View (80%)**: Displays incidents as markers with clustering
- **Chat Interface (20%)**: Tabbed interface for ingestion and queries
- Real-time status updates via AppSync WebSocket

### Login (`/login`)
- AWS Cognito authentication
- JWT token storage in secure cookies
- Automatic token refresh

### Configuration (`/config`)
- **Create Agent Tab**: Form for creating custom agents
  - Agent name, type, system prompt
  - Tool selection from registry
  - Output schema builder (max 5 fields)
  - Single-level dependency selection
- **Dependency Graph Tab**: Visual editor using ReactFlow
  - Drag-and-drop connections
  - Single-level dependency validation
  - Real-time error display

## Usage

### Submit a Report

1. Navigate to Dashboard
2. Select "Submit Report" tab
3. Choose domain (e.g., Civic Complaints)
4. Enter report description
5. Optionally upload images (max 5, 5MB each)
6. Click "Submit Report"
7. Watch real-time status updates
8. See incident appear on map

### Ask a Question

1. Navigate to Dashboard
2. Select "Ask Question" tab
3. Choose domain
4. Enter your question
5. Watch real-time agent execution
6. View bullet point analysis and summary
7. Map updates if spatial data is present

### Create Custom Agent

1. Navigate to Configuration page
2. Select "Create Agent" tab
3. Fill in agent details:
   - Name (e.g., "Priority Scorer")
   - Type (custom/ingestion/query)
   - System prompt
   - Select tools from registry
   - Define output schema (max 5 fields)
   - Optionally select parent agent
4. Click "Create Agent"
5. Switch to "Dependency Graph" tab to visualize

### Manage Dependencies

1. Navigate to Configuration page
2. Select "Dependency Graph" tab
3. View all agents as nodes
4. Drag from one agent to another to create dependency
5. System validates single-level constraint
6. Remove dependencies by clicking "Remove" button

## API Integration

The frontend communicates with the backend via:

1. **REST API** (`/api/v1/*`):
   - `/ingest` - Submit reports
   - `/query` - Ask questions
   - `/data` - Retrieve incidents
   - `/config` - Manage configurations
   - `/tools` - Access tool registry

2. **GraphQL WebSocket** (AppSync):
   - Real-time status updates
   - Agent execution progress
   - Job completion notifications

## Authentication Flow

1. User enters credentials on login page
2. AWS Cognito validates and returns JWT token
3. Token stored in secure HTTP-only cookie
4. Token included in all API requests via Authorization header
5. Token automatically refreshed before expiration
6. Logout clears tokens and redirects to login

## Real-time Updates

The system uses AppSync WebSocket subscriptions for real-time status:

```typescript
subscription OnStatusUpdate($userId: ID!) {
  onStatusUpdate(userId: $userId) {
    jobId
    agentName
    status
    message
    timestamp
  }
}
```

Status messages include:
- `loading_agents` - Loading playbook
- `invoking_{agent_name}` - Agent starting
- `calling_{tool_name}` - Tool invocation
- `agent_complete_{agent_name}` - Agent finished
- `validating` - Validation in progress
- `synthesizing` - Synthesis in progress
- `complete` - Job complete
- `error` - Error occurred

## Map Features

- **Markers**: Color-coded by incident type
- **Clustering**: Automatic clustering for performance
- **Popups**: Click marker to view details
  - Incident category and description
  - Structured data (first 3 fields)
  - Images (first 3, click to enlarge)
  - Timestamp
- **Auto-fit**: Map automatically fits to show all incidents
- **Refresh**: Manual refresh button to reload data

## Styling

The application uses Tailwind CSS with custom utilities:

- Responsive design for various screen sizes
- Custom scrollbar styling
- Indigo color scheme for primary actions
- Gray scale for neutral elements
- Red for errors and logout

## Development

```bash
# Run development server with hot reload
npm run dev

# Lint code
npm run lint

# Build for production
npm run build

# Test production build locally
npm run build && npm start
```

## Deployment

The frontend can be deployed to:

1. **Vercel** (recommended for Next.js):
   ```bash
   vercel deploy
   ```

2. **AWS Amplify Hosting**:
   - Connect GitHub repository
   - Configure build settings
   - Deploy automatically on push

3. **S3 + CloudFront**:
   ```bash
   npm run build
   # Upload .next/static to S3
   # Configure CloudFront distribution
   ```

## Troubleshooting

### Map not loading
- Check `NEXT_PUBLIC_MAPBOX_TOKEN` is set correctly
- Verify Mapbox token is valid and has appropriate permissions

### Authentication errors
- Verify Cognito User Pool ID and Client ID
- Check Cognito region matches configuration
- Ensure user exists in Cognito User Pool

### Real-time updates not working
- Verify AppSync URL and region
- Check WebSocket connection in browser DevTools
- Ensure user is authenticated

### API requests failing
- Check API Gateway URL is correct
- Verify JWT token is being sent in Authorization header
- Check CORS configuration on API Gateway

## Performance Optimization

- Map markers use clustering for large datasets
- Images lazy-loaded in popups
- Components code-split with dynamic imports
- React Flow graph virtualized for large dependency graphs
- API responses cached where appropriate

## Security

- JWT tokens stored in secure HTTP-only cookies
- All API requests require authentication
- CORS configured to allow only frontend domain
- Environment variables never exposed to client
- Input validation on all forms

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

Proprietary - Multi-Agent Orchestration System
