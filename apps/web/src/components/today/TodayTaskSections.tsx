import { useState } from 'react';
import { ArrowDown, ArrowUp, CalendarDays, Plus, Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Today } from '@/lib/api';

interface TodayTaskSectionsProps {
  today: Today;
  onAdd: (taskId: string) => void;
  onRemove: (taskId: string) => void;
  onReorder: (taskIds: string[]) => void;
  isSaving?: boolean;
}

const TodayTaskSections = ({ today, onAdd, onRemove, onReorder, isSaving = false }: TodayTaskSectionsProps) => {
  const [taskToAdd, setTaskToAdd] = useState('');
  const selected = today.selected_tasks;
  const atLimit = selected.length >= 3;

  const move = (index: number, direction: -1 | 1) => {
    const nextIndex = index + direction;
    if (nextIndex < 0 || nextIndex >= selected.length) return;
    const ids = selected.map((item) => item.task.task_id);
    [ids[index], ids[nextIndex]] = [ids[nextIndex], ids[index]];
    onReorder(ids);
  };

  const add = () => {
    if (!taskToAdd) return;
    onAdd(taskToAdd);
    setTaskToAdd('');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Today</h1>
          <p className="mt-1 text-muted-foreground">Your focused shortlist for {today.local_date}.</p>
        </div>
        <div className="flex gap-2">
          <select
            aria-label="Add a Task to Today"
            className="h-10 min-w-48 rounded-md border border-input bg-background px-3 text-sm"
            disabled={atLimit || isSaving || today.available_tasks.length === 0}
            value={taskToAdd}
            onChange={(event) => setTaskToAdd(event.target.value)}
          >
            <option value="">Add a Task</option>
            {today.available_tasks.map((task) => <option key={task.task_id} value={task.task_id}>{task.name}</option>)}
          </select>
          <Button onClick={add} disabled={!taskToAdd || atLimit || isSaving}><Plus className="mr-2 h-4 w-4" />Add</Button>
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle>Focus list ({selected.length}/3)</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {selected.length === 0 ? <p className="text-sm text-muted-foreground">Start with up to three active Tasks.</p> : selected.map((item, index) => (
            <div key={item.task.task_id} className="flex items-center gap-2 rounded-md border p-3">
              <span className="w-5 text-sm text-muted-foreground">{index + 1}</span>
              <CalendarDays className="h-4 w-4 text-primary" />
              <span className="flex-1 font-medium">{item.task.name}</span>
              <Button variant="ghost" size="icon" aria-label={`Move ${item.task.name} up`} disabled={index === 0 || isSaving} onClick={() => move(index, -1)}><ArrowUp className="h-4 w-4" /></Button>
              <Button variant="ghost" size="icon" aria-label={`Move ${item.task.name} down`} disabled={index === selected.length - 1 || isSaving} onClick={() => move(index, 1)}><ArrowDown className="h-4 w-4" /></Button>
              <Button variant="ghost" size="icon" aria-label={`Remove ${item.task.name} from Today`} disabled={isSaving} onClick={() => onRemove(item.task.task_id)}><Trash2 className="h-4 w-4" /></Button>
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <TaskGroup title="Due today" tasks={today.due_today} emptyMessage="No Tasks are due today." />
        <TaskGroup title="Overdue" tasks={today.overdue} emptyMessage="No overdue Tasks." />
      </div>
    </div>
  );
};

const TaskGroup = ({ title, tasks, emptyMessage }: { title: string; tasks: Today['due_today']; emptyMessage: string }) => (
  <Card>
    <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
    <CardContent className="space-y-2">
      {tasks.length === 0 ? <p className="text-sm text-muted-foreground">{emptyMessage}</p> : tasks.map((task) => (
        <div key={task.task_id} className="rounded-md border p-3">
          <p className="font-medium">{task.name}</p>
          {task.due_date && <p className="text-sm text-muted-foreground">Due {task.due_date}</p>}
        </div>
      ))}
    </CardContent>
  </Card>
);

export default TodayTaskSections;
