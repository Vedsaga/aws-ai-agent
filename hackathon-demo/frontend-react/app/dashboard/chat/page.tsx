'use client';

import { useEffect, useState } from 'react';
import IncidentChat from '@/components/IncidentChat';
import { getCurrentUser } from '@aws-amplify/auth';

export default function ChatPage() {
  const [token, setToken] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      try {
        const user = await getCurrentUser();
        const session = await user.getSession();
        setToken(session.getIdToken().getJwtToken());
      } catch (error) {
        console.error('Auth error:', error);
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 h-screen">
      <IncidentChat token={token} />
    </div>
  );
}
