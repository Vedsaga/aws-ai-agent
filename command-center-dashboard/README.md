# Command Center Dashboard MVP

A real-time disaster response simulation dashboard built with Next.js, Mapbox GL, and Zustand.

## Features

- 80/20 split layout with interactive map and control panel
- Real-time data polling every 5 seconds
- Chat interface with suggested actions
- Critical alerts panel
- Timeline slider for navigating through 7-day simulation
- Session persistence using localStorage
- Mock API service with dummy data

## Getting Started

### Prerequisites

- Node.js 18+ installed
- A Mapbox public access token (free, required - see MAPBOX_SETUP.md)

### Installation

1. Install dependencies:
```bash
npm install
```

2. **REQUIRED:** Add your Mapbox token to `.env.local`:
```
NEXT_PUBLIC_MAPBOX_TOKEN=pk.your_public_token_here
```
See `MAPBOX_SETUP.md` for detailed instructions (takes 2 minutes)

### Running the Application

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
command-center-dashboard/
├── app/
│   ├── page.tsx          # Main application page
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles
├── components/
│   ├── MapComponent.tsx       # Mapbox GL map
│   ├── ChatPanel.tsx          # Chat interface
│   ├── AlertsPanel.tsx        # Critical alerts display
│   ├── TimelineSlider.tsx     # Timeline control
│   ├── InteractionPanel.tsx   # Right panel container
│   └── ui/                    # ShadCN UI components
├── store/
│   └── useStore.ts       # Zustand state management
├── services/
│   └── mockApiService.ts # Mock API with dummy data
└── data/
    ├── initial_load.json      # Initial view data
    ├── food_water_response.json # Query response example
    └── update_poll.json       # Real-time update example
```

## How It Works

### Data Flow

1. **Initial Load**: On page load, fetches `initial_load.json` and displays critical incidents
2. **User Queries**: When user sends a message, the mock API returns relevant data (e.g., food/water needs)
3. **Real-Time Updates**: Every 5 seconds, polls for new data and appends to the map
4. **Timeline Navigation**: Dragging the slider triggers a full data refresh for that time

### State Management

The Zustand store manages:
- `simulationTime`: Current time in simulation
- `timestamp`: ISO timestamp for API calls
- `activeDomainFilter`: Current context (CRITICAL, FOOD_WATER, etc.)
- `mapAction`: REPLACE or APPEND layers
- `mapLayers`: Array of GeoJSON layers to display
- `chatHistory`: Conversation messages
- `criticalAlerts`: Array of critical alerts
- `suggestedActions`: Clickable action buttons

### Mock API

The mock API service simulates backend responses:
- `getInitialLoad()`: Returns default critical incidents view
- `postQuery(query, timestamp)`: Returns context-specific data based on query
- `getUpdates(timestamp, filter)`: Returns incremental updates (30% chance)

## Customization

### Adding New Data

1. Create a new JSON file in `/data/` following the response structure
2. Update `mockApiService.ts` to return your data based on conditions
3. The map will automatically render Point, Polygon, and LineString geometries

### Styling

- Tailwind CSS classes are used throughout
- Dark theme is default
- Modify `globals.css` for global style changes
- Component-specific styles are inline with Tailwind

## Requirements Checklist

- [x] R1: Map Display
  - [x] R1.1: Centered on Nurdağı, Turkey
  - [x] R1.2: Multiple data layers
  - [x] R1.3: GeoJSON rendering (Point, Polygon, LineString)
  - [x] R1.4: Auto-zoom to bounds
- [x] R2: Chat Interface
  - [x] R2.1: Conversation history
  - [x] R2.2: Text input
  - [x] R2.3: Suggested action buttons
- [x] R3: Real-Time Data Flow
  - [x] R3.1: Initial load
  - [x] R3.2: 5-second polling
  - [x] R3.3: Context-aware data appending
  - [x] R3.4: Critical alerts panel
- [x] R4: Timeline Control
  - [x] R4.1: 7-day slider
  - [x] R4.2: Time-based data refresh
- [x] R5: Session Persistence
  - [x] R5.1: localStorage for timestamp
  - [x] R5.2: Resume on page refresh

## Next Steps

To connect to a real backend:

1. Replace `mockApiService.ts` with a real API service using axios
2. Update endpoints to match your backend API
3. Add error handling and loading states
4. Implement authentication if needed
5. Add your Mapbox token for production use

## License

MIT
