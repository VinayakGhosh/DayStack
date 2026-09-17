import { useEffect, useState } from 'react';

import TodayTaskSections from '@/components/today/TodayTaskSections';
import DashboardLayout from '@/components/layout/DashboardLayout';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { useToast } from '@/hooks/use-toast';
import { Today, todayApi } from '@/lib/api';

const TodayPage = () => {
  const [today, setToday] = useState<Today | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  const loadToday = async () => {
    const response = await todayApi.get();
    if (response.data) setToday(response.data);
    else toast({ title: 'Failed to load Today', description: response.error, variant: 'destructive' });
  };

  useEffect(() => { void loadToday(); }, []);

  const mutate = async (request: () => ReturnType<typeof todayApi.add> | ReturnType<typeof todayApi.reorder> | ReturnType<typeof todayApi.remove>) => {
    setIsSaving(true);
    const response = await request();
    if (response.data) setToday(response.data);
    else if (response.errorCode !== undefined || response.error) {
      toast({ title: 'Could not update Today', description: response.error, variant: 'destructive' });
      if (response.errorCode === 'today_limit_reached') void loadToday();
    }
    if (!response.data) await loadToday();
    setIsSaving(false);
  };

  return (
    <DashboardLayout>
      {!today ? <div className="flex h-64 items-center justify-center"><LoadingSpinner size="lg" /></div> : (
        <TodayTaskSections
          today={today}
          isSaving={isSaving}
          onAdd={(taskId) => void mutate(() => todayApi.add(taskId))}
          onRemove={(taskId) => void mutate(() => todayApi.remove(taskId))}
          onReorder={(taskIds) => void mutate(() => todayApi.reorder(taskIds))}
        />
      )}
    </DashboardLayout>
  );
};

export default TodayPage;
