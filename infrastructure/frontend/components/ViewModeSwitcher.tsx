'use client';

import { useRouter, usePathname } from 'next/navigation';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

export type ViewMode = 'use' | 'manage';

interface ViewModeSwitcherProps {
  className?: string;
}

export default function ViewModeSwitcher({ className }: ViewModeSwitcherProps) {
  const router = useRouter();
  const pathname = usePathname();

  // Determine current mode based on pathname
  const currentMode: ViewMode = pathname.startsWith('/manage') ? 'manage' : 'use';

  const handleModeChange = (mode: string) => {
    if (mode === 'use') {
      router.push('/dashboard');
    } else if (mode === 'manage') {
      router.push('/manage');
    }
  };

  return (
    <Tabs value={currentMode} onValueChange={handleModeChange} className={className}>
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="use">Use Domain</TabsTrigger>
        <TabsTrigger value="manage">Manage Domain</TabsTrigger>
      </TabsList>
    </Tabs>
  );
}
