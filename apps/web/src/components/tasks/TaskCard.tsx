import type { HTMLAttributes, SyntheticEvent } from 'react';
import { CalendarDays, GripVertical, MoreVertical, Paperclip, Trash } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import type { ProjectStatus, Task } from '@/lib/api';
import { formatTaskDueDate } from '@/lib/dateOnly';
import { cn } from '@/lib/utils';

interface TaskCardProps {
  task: Task;
  statuses: ProjectStatus[];
  onOpen: (task: Task) => void;
  onDelete: (task: Task) => void;
  onToggleCompletion: (task: Task, completed: boolean) => void;
  dragHandleProps?: HTMLAttributes<HTMLButtonElement>;
  highlighted?: boolean;
  now?: Date;
}

const priorityClasses = {
  low: 'bg-sky-500/10 text-sky-700 dark:text-sky-300',
  medium: 'bg-amber-500/10 text-amber-700 dark:text-amber-300',
  high: 'bg-rose-500/10 text-rose-700 dark:text-rose-300',
};

const TaskCard = ({ task, statuses, onOpen, onDelete, onToggleCompletion, dragHandleProps, highlighted, now }: TaskCardProps) => {
  const completed = statuses.some((status) => status.status_id === task.status_id && status.is_completion);
  const due = task.due_date ? formatTaskDueDate(task.due_date, completed, now) : null;
  const completeSubtasks = task.subtasks.filter((subtask) => subtask.is_completed).length;
  const stop = (event: SyntheticEvent) => event.stopPropagation();

  return (
    <Card className={cn('group relative transition-all hover:shadow-md', completed && 'opacity-70', highlighted && 'ring-2 ring-primary animate-pulse')} data-task-id={task.task_id}>
      <CardContent className="p-3">
        <div className="flex items-start gap-2">
          <Checkbox aria-label={completed ? `Reopen ${task.name}` : `Complete ${task.name}`} checked={completed} onClick={stop} onCheckedChange={() => onToggleCompletion(task, !completed)} className="mt-1 shrink-0" />
          <div role="button" tabIndex={0} data-task-open-id={task.task_id} aria-label={`Open details for ${task.name}`} className="min-w-0 flex-1 cursor-pointer rounded-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" onClick={() => onOpen(task)} onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              onOpen(task);
            }
          }}>
            <h4 className={cn('text-sm font-medium leading-snug', completed && 'line-through text-muted-foreground')}>{task.name}</h4>
            {task.description && <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-muted-foreground">{task.description}</p>}
            <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
              {due && <span className={cn('inline-flex items-center gap-1', due.overdue && 'font-medium text-destructive')}><CalendarDays className="h-3 w-3" />{due.text}</span>}
              {task.priority !== 'none' && <Badge variant="outline" className={cn('px-1.5 py-0 text-[11px]', priorityClasses[task.priority])}>{task.priority[0].toUpperCase() + task.priority.slice(1)}</Badge>}
              {task.labels.slice(0, 2).map((label) => <Badge key={label.label_id} variant="secondary" className="px-1.5 py-0 text-[11px]">{label.name}</Badge>)}
              {task.labels.length > 2 && <span>+{task.labels.length - 2}</span>}
              {task.subtasks.length > 0 && <span>{completeSubtasks}/{task.subtasks.length}</span>}
              {task.attachment_count > 0 && <span className="inline-flex items-center gap-1"><Paperclip className="h-3 w-3" />{task.attachment_count}</span>}
            </div>
          </div>
          <div className="flex shrink-0 items-center" onClick={stop} onKeyDown={stop}>
            {dragHandleProps && <Button {...dragHandleProps} type="button" variant="ghost" size="icon" className="h-7 w-7 cursor-grab touch-none" aria-label={`Drag ${task.name}`}><GripVertical className="h-4 w-4" /></Button>}
            <DropdownMenu>
              <DropdownMenuTrigger asChild><Button type="button" variant="ghost" size="icon" className="h-7 w-7" aria-label={`Task actions for ${task.name}`}><MoreVertical className="h-4 w-4" /></Button></DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onOpen(task)}>Open details</DropdownMenuItem>
                <DropdownMenuItem onClick={() => onDelete(task)} className="text-destructive focus:text-destructive"><Trash className="mr-2 h-4 w-4" />Delete</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default TaskCard;
