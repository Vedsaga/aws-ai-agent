'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { checkAuthStatus } from '@/lib/auth';
import { configureAmplify } from '@/lib/amplify-config';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    configureAmplify();
    
    checkAuthStatus().then((isAuthenticated) => {
      if (isAuthenticated) {
        router.push('/dashboard');
      } else {
        router.push('/login');
      }
    });
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-lg">Loading...</div>
    </div>
  );
}
