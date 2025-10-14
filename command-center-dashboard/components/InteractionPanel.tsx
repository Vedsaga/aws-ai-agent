'use client';

import ChatPanel from './ChatPanel';
import AlertsPanel from './AlertsPanel';
import TimelineSlider from './TimelineSlider';

export default function InteractionPanel() {
  return (
    <div className="h-full flex flex-col bg-slate-900 border-l border-slate-700">
      <div className="flex-1 flex flex-col min-h-0">
        <AlertsPanel />
        <div className="flex-1 border-t border-slate-700 min-h-0">
          <ChatPanel />
        </div>
      </div>
      <TimelineSlider />
    </div>
  );
}
