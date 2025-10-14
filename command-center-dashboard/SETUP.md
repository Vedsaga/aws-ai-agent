# Quick Setup Guide

## Step 1: Install Dependencies

```bash
cd command-center-dashboard
npm install
```

## Step 2: (Optional) Configure Mapbox

If you want to use a real Mapbox map instead of the placeholder:

1. Get a free token from [https://www.mapbox.com/](https://www.mapbox.com/)
2. Edit `.env.local` and replace the token:
```
NEXT_PUBLIC_MAPBOX_TOKEN=your_actual_token_here
```

## Step 3: Run the Development Server

```bash
npm run dev
```

## Step 4: Open in Browser

Navigate to [http://localhost:3000](http://localhost:3000)

## What You'll See

1. **Map (Left 80%)**: A dark-themed map centered on Nurdağı, Turkey showing critical incidents
2. **Control Panel (Right 20%)**:
   - Critical Alerts at the top
   - Chat interface in the middle
   - Timeline slider at the bottom

## Try These Actions

1. **Send a chat message**: Type "Show me all food and water needs" and press Send
2. **Click suggested actions**: Click the button below the agent's response
3. **Move the timeline**: Drag the slider at the bottom to navigate through the simulation
4. **Watch for updates**: Every 5 seconds, new data may appear on the map (30% chance)
5. **Refresh the page**: Your timeline position will be saved and restored

## Troubleshooting

### Map doesn't load
- Check browser console for errors
- Verify Mapbox token is valid (or use the placeholder for demo)
- Ensure you're using a modern browser (Chrome, Firefox, Safari, Edge)

### No data appears
- Check that JSON files exist in `/data/` directory
- Open browser DevTools Network tab to see API calls
- Check console for any JavaScript errors

### Styling looks broken
- Ensure Tailwind CSS is properly configured
- Try clearing browser cache
- Run `npm install` again to ensure all dependencies are installed

## Development Notes

- The app uses mock data from `/data/*.json` files
- Real-time polling happens every 5 seconds
- Map layers are managed by Zustand store
- All components are client-side rendered
- Session state is saved to localStorage

## Next Steps

Once you verify the mock-up works:

1. Replace `mockApiService.ts` with real API calls
2. Update data structures to match your backend
3. Add authentication if needed
4. Deploy to Vercel or your preferred hosting
