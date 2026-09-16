import { Task, ProjectStatus } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { MoreVertical, Pencil, Trash } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';

interface TaskCardProps {
  task: Task;
  statuses: ProjectStatus[];
  onEdit: (task: Task) => void;
  onDelete: (task: Task) => void;
  onStatusChange: (task: Task, statusId: string) => void;
}

const STATUS_BADGE_COLORS = [
  'bg-slate-500/15 text-slate-600 dark:text-slate-400',
  'bg-blue-500/15 text-blue-600 dark:text-blue-400',
  'bg-violet-500/15 text-violet-600 dark:text-violet-400',
  'bg-amber-500/15 text-amber-600 dark:text-amber-400',
  'bg-orange-500/15 text-orange-600 dark:text-orange-400',
  'bg-green-500/15 text-green-600 dark:text-green-400',
];

const TaskCard = ({ task, statuses, onEdit, onDelete, onStatusChange }: TaskCardProps) => {
  const statusIndex = statuses.findIndex((s) => s.status_id === task.status_id);
  const badgeColor =
    statusIndex >= 0
      ? STATUS_BADGE_COLORS[Math.min(statusIndex, STATUS_BADGE_COLORS.length - 1)]
      : STATUS_BADGE_COLORS[0];

  const isLastStatus = statuses.length > 0 && task.status_id === statuses[statuses.length - 1].status_id;
  const isFirstStatus = statuses.length > 0 && task.status_id === statuses[0].status_id;

  const handleCheckboxChange = () => {
    if (!statuses.length) return;
    if (isLastStatus) {
      onStatusChange(task, statuses[0].status_id);
    } else {
      onStatusChange(task, statuses[statuses.length - 1].status_id);
    }
  };

  return (
    <Card className={cn('group transition-all hover:shadow-md', isLastStatus && 'opacity-70')}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <Checkbox
            checked={isLastStatus}
            onCheckedChange={handleCheckboxChange}
            className="mt-0.5 shrink-0"
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <h4
                className={cn(
                  'font-medium text-foreground text-sm leading-snug',
                  isLastStatus && 'line-through text-muted-foreground'
                )}
              >
                {task.name}
              </h4>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 -mr-1"
                  >
                    <MoreVertical className="h-3.5 w-3.5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onEdit(task)}>
                    <Pencil className="mr-2 h-4 w-4" />
                    Edit
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => onDelete(task)}
                    className="text-destructive focus:text-destructive"
                  >
                    <Trash className="mr-2 h-4 w-4" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            {task.description && (
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2 leading-relaxed">
                {task.description}
              </p>
            )}

            {task.status_name && (
              <div className="mt-2.5">
                <Badge variant="outline" className={cn('text-xs font-medium', badgeColor)}>
                  {task.status_name}
                </Badge>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default TaskCard;
