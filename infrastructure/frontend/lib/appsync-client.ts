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
}

export const subscribeToStatusUpdates = (
  userId: string,
  onUpdate: (update: StatusUpdate) => void,
  onError?: (error: any) => void
) => {
  const subscription = appsyncClient.graphql({
    query: STATUS_UPDATE_SUBSCRIPTION,
    variables: { userId },
  }).subscribe({
    next: ({ data }: any) => {
      if (data?.onStatusUpdate) {
        onUpdate(data.onStatusUpdate);
      }
    },
    error: (error: any) => {
      console.error('AppSync subscription error:', error);
      if (onError) {
        onError(error);
      }
    },
  });

  return subscription;
};
