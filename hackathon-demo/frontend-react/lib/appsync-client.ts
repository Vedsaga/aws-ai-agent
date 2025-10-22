import { generateClient } from 'aws-amplify/api';

export const appsyncClient = generateClient();

export const STATUS_UPDATE_SUBSCRIPTION = `
  subscription OnStatusUpdate($userId: ID!) {
    onStatusUpdate(userId: $userId) {
      jobId
      agentName
      status
      message
      timestamp
    }
  }
`;

export interface StatusUpdate {
  jobId: string;
  agentName: string;
  status: string;
  message: string;
  timestamp: string;
  confidence?: number;
}

export interface SubscriptionHandle {
  unsubscribe: () => void;
}

/**
 * Subscribe to status updates for a specific user
 * Filters updates by jobId if provided
 */
export const subscribeToStatusUpdates = (
  userId: string,
  onUpdate: (update: StatusUpdate) => void,
  onError?: (error: any) => void,
  jobIdFilter?: string
): SubscriptionHandle => {
  try {
    const subscription = appsyncClient.graphql({
      query: STATUS_UPDATE_SUBSCRIPTION,
      variables: { userId },
    }) as any;

    if (subscription.subscribe) {
      return subscription.subscribe({
        next: ({ data }: any) => {
          if (data?.onStatusUpdate) {
            const update = data.onStatusUpdate;
            
            // Filter by jobId if specified
            if (jobIdFilter && update.jobId !== jobIdFilter) {
              return;
            }
            
            // Parse confidence from message if present
            try {
              const messageData = JSON.parse(update.message);
              if (messageData.confidence !== undefined) {
                update.confidence = messageData.confidence;
              }
            } catch (e) {
              // Message is not JSON, ignore
            }
            
            onUpdate(update);
          }
        },
        error: (error: any) => {
          console.error('AppSync subscription error:', error);
          if (onError) {
            onError(error);
          }
        },
      });
    }
  } catch (error) {
    console.error('Failed to create subscription:', error);
    if (onError) {
      onError(error);
    }
  }

  return { unsubscribe: () => {} };
};

/**
 * Subscribe to status updates for a specific job
 * This is a convenience wrapper around subscribeToStatusUpdates
 */
export const subscribeToJobStatus = (
  userId: string,
  jobId: string,
  onUpdate: (update: StatusUpdate) => void,
  onError?: (error: any) => void
): SubscriptionHandle => {
  return subscribeToStatusUpdates(userId, onUpdate, onError, jobId);
};
