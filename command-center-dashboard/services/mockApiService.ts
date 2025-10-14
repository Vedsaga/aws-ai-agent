import initialLoadData from '../data/initial_load.json';
import foodWaterData from '../data/food_water_response.json';
import updatePollData from '../data/update_poll.json';

let queryCount = 0;

export const mockApiService = {
  async getInitialLoad() {
    await new Promise(resolve => setTimeout(resolve, 500));
    return initialLoadData;
  },

  async postQuery(query: string, timestamp: string) {
    await new Promise(resolve => setTimeout(resolve, 800));
    
    queryCount++;
    
    if (query.toLowerCase().includes('food') || query.toLowerCase().includes('water')) {
      return foodWaterData;
    }
    
    return initialLoadData;
  },

  async getUpdates(timestamp: string, activeDomainFilter: string) {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    if (Math.random() > 0.7) {
      return updatePollData;
    }
    
    return {
      latestTimestamp: timestamp,
      mapUpdates: null,
      criticalAlerts: []
    };
  }
};
