'use client';

import { useState } from 'react';
import { useStore } from '@/store/useStore';
import { mockApiService } from '@/services/mockApiService';
import { Slider } from '@/components/ui/slider';

const TIMELINE_DAYS = 7;
const HOURS_PER_DAY = 24;
const TOTAL_HOURS = TIMELINE_DAYS * HOURS_PER_DAY;

export default function TimelineSlider() {
  const { simulationTime, setIsLoading, updateFromResponse, addChatMessage } = useStore();
  const [sliderValue, setSliderValue] = useState([4]);

  const handleSliderChange = async (value: number[]) => {
    setSliderValue(value);
    const hours = value[0];
    const day = Math.floor(hours / 24);
    const hour = hours % 24;
    
    const newTime = `Day ${day}, ${hour.toString().padStart(2, '0')}:00`;
    
    setIsLoading(true);
    
    try {
      const response = await mockApiService.getInitialLoad();
      
      const agentMessage = {
        role: 'agent' as const,
        content: `Timeline updated to ${newTime}. ${response.chatResponse}`,
        timestamp: response.timestamp
      };
      
      addChatMessage(agentMessage);
      updateFromResponse({
        ...response,
        simulationTime: newTime
      });
    } catch (error) {
      console.error('Error updating timeline:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 border-t border-slate-700">
      <div className="mb-2 flex justify-between items-center">
        <span className="text-sm font-semibold">Timeline</span>
        <span className="text-xs text-slate-400">{simulationTime}</span>
      </div>
      <Slider
        value={sliderValue}
        onValueChange={setSliderValue}
        onValueCommit={handleSliderChange}
        max={TOTAL_HOURS - 1}
        step={1}
        className="w-full"
      />
      <div className="flex justify-between text-xs text-slate-400 mt-1">
        <span>Day 0</span>
        <span>Day 7</span>
      </div>
    </div>
  );
}
