import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  useDroppable,
} from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { projectsApi, projectStatusApi, tasksApi, Project, Task, ProjectStatus } from '@/lib/api';
import { ArrowLeft, Plus, Settings2, Trash2, Pencil, X, Check, AlertTriangle } from 'lucide-react';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import TaskCard from '@/components/tasks/TaskCard';
import TaskModal from '@/components/tasks/TaskModal';
import { useToast } from '@/hooks/use-toast';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { cn } from '@/lib/utils';

const MAX_STATUSES = 6;

const COLUMN_BORDER_COLORS = [
  'border-slate-400',
  'border-blue-500',
  'border-violet-500',
  'border-amber-500',
  'border-orange-500',
  'border-green-500',
];

const COLUMN_COUNT_COLORS = [
  'bg-slate-500/10 text-slate-600',
  'bg-blue-500/10 text-blue-600',
  'bg-violet-500/10 text-violet-600',
  'bg-amber-500/10 text-amber-600',
  'bg-orange-500/10 text-orange-600',
  'bg-green-500/10 text-green-600',
];

// Sortable task wrapper for dnd-kit
const SortableTaskCard = ({
  task,
  statuses,
  onEdit,
  onDelete,
  onStatusChange,
}: {
  task: Task;
  statuses: ProjectStatus[];
  onEdit: (t: Task) => void;
  onDelete: (t: Task) => void;
  onStatusChange: (t: Task, statusId: string) => void;
}) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: task.task_id,
    data: { type: 'task', task },
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="touch-none">
      <TaskCard
        task={task}
        statuses={statuses}
        onEdit={onEdit}
        onDelete={onDelete}
        onStatusChange={onStatusChange}
      />
    </div>
  );
};

// Droppable column wrapper
const DroppableColumn = ({
  statusId,
  children,
}: {
  statusId: string;
  children: React.ReactNode;
}) => {
  const { setNodeRef, isOver } = useDroppable({
    id: statusId,
    data: { type: 'column', statusId },
  });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex-1 space-y-2.5 overflow-y-auto pr-1 transition-colors rounded-lg',
        isOver && 'bg-accent/50'
      )}
      style={{ minHeight: '4rem' }}
    >
      {children}
    </div>
  );
};

const ProjectDetailsPage = () => {
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();

  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [statuses, setStatuses] = useState<ProjectStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [deletingTask, setDeletingTask] = useState<Task | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Status management panel
  const [statusPanelOpen, setStatusPanelOpen] = useState(false);
  const [newStatusName, setNewStatusName] = useState('');
  const [editingStatus, setEditingStatus] = useState<ProjectStatus | null>(null);
  const [editingStatusName, setEditingStatusName] = useState('');
  const [deletingStatus, setDeletingStatus] = useState<ProjectStatus | null>(null);
  const [statusSubmitting, setStatusSubmitting] = useState(false);

  // Drag state
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const dragOriginStatusId = useRef<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  const fetchData = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);

    const [projectRes, tasksRes, statusesRes] = await Promise.all([
      projectsApi.getById(id),
      tasksApi.getByProject(id),
      projectStatusApi.getAll(id),
    ]);

    if (projectRes.error || !projectRes.data) {
      setIsLoading(false);
      return;
    }

    setProject(projectRes.data);
    setStatuses(statusesRes.data || []);
    setTasks(tasksRes.data || []);
    setIsLoading(false);
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ── Task CRUD ──────────────────────────────────────────────────────────────

  const handleCreateTask = async (data: { name: string; description?: string }) => {
    if (!id) return;
    setIsSubmitting(true);

    const { data: newTask, error } = await tasksApi.create({
      project_id: id,
      name: data.name,
      description: data.description,
    });

    setIsSubmitting(false);

    if (newTask) {
      setTasks((prev) => [newTask, ...prev]);
      setModalOpen(false);
      toast({ title: 'Task created' });
    } else {
      toast({ title: 'Failed to create task', description: error, variant: 'destructive' });
    }
  };

  const handleEditTask = async (data: { name: string; description?: string }) => {
    if (!editingTask) return;
    setIsSubmitting(true);

    const { data: updatedTask, error } = await tasksApi.update(editingTask.task_id, {
      name: data.name,
      description: data.description,
    });

    setIsSubmitting(false);

    if (updatedTask) {
      setTasks((prev) => prev.map((t) => (t.task_id === editingTask.task_id ? updatedTask : t)));
      setEditingTask(null);
      toast({ title: 'Task updated' });
    } else {
      toast({ title: 'Failed to update task', description: error, variant: 'destructive' });
    }
  };

  const handleDeleteTask = async () => {
    if (!deletingTask) return;
    const { error } = await tasksApi.delete(deletingTask.task_id);

    if (!error) {
      setTasks((prev) => prev.filter((t) => t.task_id !== deletingTask.task_id));
      toast({ title: 'Task deleted' });
    } else {
      toast({ title: 'Failed to delete task', description: error, variant: 'destructive' });
    }
    setDeletingTask(null);
  };

  const handleStatusChange = async (task: Task, statusId: string) => {
    // Optimistic update
    setTasks((prev) =>
      prev.map((t) => {
        if (t.task_id !== task.task_id) return t;
        const newStatus = statuses.find((s) => s.status_id === statusId);
        return { ...t, status_id: statusId, status_name: newStatus?.name ?? t.status_name };
      })
    );

    const { data, error } = await tasksApi.moveStatus(task.task_id, statusId);
    if (error) {
      // Revert
      setTasks((prev) => prev.map((t) => (t.task_id === task.task_id ? task : t)));
      toast({ title: 'Failed to update status', description: error, variant: 'destructive' });
    } else if (data) {
      // Sync status_name from server response
      setTasks((prev) =>
        prev.map((t) =>
          t.task_id === task.task_id
            ? { ...t, status_id: data.status_id, status_name: data.status_name }
            : t
        )
      );
    }
  };

  // ── Drag and Drop ──────────────────────────────────────────────────────────

  const handleDragStart = (event: DragStartEvent) => {
    const task = tasks.find((t) => t.task_id === event.active.id);
    if (task) {
      setActiveTask(task);
      dragOriginStatusId.current = task.status_id;
    }
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeTask = tasks.find((t) => t.task_id === active.id);
    if (!activeTask) return;

    // Dropped over a column (status_id as droppable id)
    const overStatus = statuses.find((s) => s.status_id === over.id);
    if (overStatus && activeTask.status_id !== overStatus.status_id) {
      setTasks((prev) =>
        prev.map((t) => {
          if (t.task_id !== activeTask.task_id) return t;
          return { ...t, status_id: overStatus.status_id, status_name: overStatus.name };
        })
      );
    }

    // Dropped over another task
    const overTask = tasks.find((t) => t.task_id === over.id);
    if (overTask && overTask.status_id !== activeTask.status_id) {
      setTasks((prev) =>
        prev.map((t) => {
          if (t.task_id !== activeTask.task_id) return t;
          const targetStatus = statuses.find((s) => s.status_id === overTask.status_id);
          return { ...t, status_id: overTask.status_id, status_name: targetStatus?.name ?? t.status_name };
        })
      );
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTask(null);
    if (!over) return;

    const dragged = tasks.find((t) => t.task_id === active.id);
    if (!dragged) return;

    // Determine the target status_id
    let targetStatusId: string | null = null;
    const overStatus = statuses.find((s) => s.status_id === over.id);
    if (overStatus) {
      targetStatusId = overStatus.status_id;
    } else {
      const overTask = tasks.find((t) => t.task_id === over.id);
      if (overTask) targetStatusId = overTask.status_id;
    }

    if (targetStatusId && targetStatusId !== dragOriginStatusId.current) {
      // Persist the status change
      const { data, error } = await tasksApi.moveStatus(dragged.task_id, targetStatusId);
      if (error) {
        toast({ title: 'Failed to move task', description: error, variant: 'destructive' });
        fetchData(); // Revert to server state
      } else if (data) {
        // Sync status_name from server response
        setTasks((prev) =>
          prev.map((t) =>
            t.task_id === dragged.task_id
              ? { ...t, status_id: data.status_id, status_name: data.status_name }
              : t
          )
        );
      }
    }
  };

  // ── Status CRUD ────────────────────────────────────────────────────────────

  const handleCreateStatus = async () => {
    if (!id || !newStatusName.trim()) return;
    if (statuses.length >= MAX_STATUSES) return;
    setStatusSubmitting(true);

    const { data: created, error } = await projectStatusApi.create(id, { name: newStatusName.trim() });
    setStatusSubmitting(false);

    if (created) {
      setStatuses((prev) => [...prev, created]);
      setNewStatusName('');
      toast({ title: `Status "${created.name}" created` });
    } else {
      toast({ title: 'Failed to create status', description: error, variant: 'destructive' });
    }
  };

  const handleUpdateStatus = async () => {
    if (!id || !editingStatus || !editingStatusName.trim()) return;
    setStatusSubmitting(true);

    const { data: updated, error } = await projectStatusApi.update(id, editingStatus.status_id, {
      name: editingStatusName.trim(),
    });
    setStatusSubmitting(false);

    if (updated) {
      setStatuses((prev) => prev.map((s) => (s.status_id === updated.status_id ? updated : s)));
      setTasks((prev) =>
        prev.map((t) =>
          t.status_id === updated.status_id ? { ...t, status_name: updated.name } : t
        )
      );
      setEditingStatus(null);
      toast({ title: 'Status updated' });
    } else {
      toast({ title: 'Failed to update status', description: error, variant: 'destructive' });
    }
  };

  const handleDeleteStatus = async () => {
    if (!id || !deletingStatus) return;
    const { error } = await projectStatusApi.delete(id, deletingStatus.status_id);

    if (!error) {
      setStatuses((prev) => prev.filter((s) => s.status_id !== deletingStatus.status_id));
      toast({ title: `Status "${deletingStatus.name}" deleted` });
    } else {
      toast({
        title: 'Cannot delete status',
        description: error,
        variant: 'destructive',
      });
    }
    setDeletingStatus(null);
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </DashboardLayout>
    );
  }

  if (!project) {
    return (
      <DashboardLayout>
        <div className="text-center py-16">
          <h2 className="text-xl font-semibold text-foreground mb-2">Project not found</h2>
          <Link to="/projects">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Projects
            </Button>
          </Link>
        </div>
      </DashboardLayout>
    );
  }

  const totalTasks = tasks.length;
  const doneTasks = statuses.length > 0
    ? tasks.filter((t) => t.status_id === statuses[statuses.length - 1].status_id).length
    : 0;
  const progressPct = totalTasks > 0 ? Math.round((doneTasks / totalTasks) * 100) : 0;

  return (
    <DashboardLayout>
      <div className="space-y-6 w-full min-w-0 overflow-hidden">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <Link
            to="/projects"
            className="inline-flex items-center text-muted-foreground hover:text-foreground transition-colors w-fit text-sm"
          >
            <ArrowLeft className="mr-1.5 h-4 w-4" />
            Back to Projects
          </Link>

          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="min-w-0">
              <h1 className="text-2xl font-bold text-foreground truncate">{project.name}</h1>
              {project.description && (
                <p className="text-muted-foreground mt-1 text-sm max-w-2xl">{project.description}</p>
              )}
              {/* Progress bar */}
              <div className="mt-3 flex items-center gap-3 max-w-xs">
                <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 rounded-full transition-all duration-500"
                    style={{ width: `${progressPct}%` }}
                  />
                </div>
                <span className="text-xs text-muted-foreground shrink-0">
                  {doneTasks}/{totalTasks} done
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Button variant="outline" size="sm" onClick={() => setStatusPanelOpen(true)}>
                <Settings2 className="mr-1.5 h-4 w-4" />
                Statuses
              </Button>
              <Button size="sm" onClick={() => setModalOpen(true)}>
                <Plus className="mr-1.5 h-4 w-4" />
                Add Task
              </Button>
            </div>
          </div>
        </div>

        {/* Kanban Board */}
        {statuses.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center gap-3">
            <p className="text-muted-foreground">No statuses found for this project.</p>
            <Button variant="outline" size="sm" onClick={() => setStatusPanelOpen(true)}>
              <Settings2 className="mr-1.5 h-4 w-4" />
              Manage Statuses
            </Button>
          </div>
        ) : (
          <div className="w-full min-w-0 overflow-hidden">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
          >
            <div className="w-full overflow-x-auto rounded-xl border border-border shadow-xl p-4">
              <div className=" flex gap-4 pb-1" style={{ minWidth: 'max-content' }}>
                {statuses.map((status, idx) => {
                  const columnTasks = tasks.filter((t) => t.status_id === status.status_id);
                  const borderColor = COLUMN_BORDER_COLORS[Math.min(idx, COLUMN_BORDER_COLORS.length - 1)];
                  const countColor = COLUMN_COUNT_COLORS[Math.min(idx, COLUMN_COUNT_COLORS.length - 1)];

                  return (
                    <div
                      key={status.status_id}
                      className="flex flex-col shrink-0 w-72 bg-muted/10 p-2 rounded-lg max-h-[calc(100vh-16rem)] overflow-hidden"
                      id={status.status_id}
                    >
                      {/* Column header */}
                      <div className={cn('flex items-center justify-between mb-3 pb-3 border-b-2', borderColor)}>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-foreground text-sm">{status.name}</h3>
                          <span className={cn('text-xs font-medium px-1.5 py-0.5 rounded-full', countColor)}>
                            {columnTasks.length}
                          </span>
                        </div>
                      </div>

                      {/* Droppable column body */}
                      <SortableContext
                        items={columnTasks.map((t) => t.task_id)}
                        strategy={verticalListSortingStrategy}
                      >
                        <DroppableColumn statusId={status.status_id}>
                          {columnTasks.length === 0 ? (
                            <div className="flex items-center justify-center h-20 rounded-lg border border-dashed border-muted-foreground/25">
                              <p className="text-xs text-muted-foreground">Drop tasks here</p>
                            </div>
                          ) : (
                            columnTasks.map((task) => (
                              <SortableTaskCard
                                key={task.task_id}
                                task={task}
                                statuses={statuses}
                                onEdit={(t) => setEditingTask(t)}
                                onDelete={(t) => setDeletingTask(t)}
                                onStatusChange={handleStatusChange}
                              />
                            ))
                          )}
                        </DroppableColumn>
                      </SortableContext>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Drag overlay */}
            <DragOverlay>
              {activeTask && (
                <div className="rotate-2 scale-105 opacity-90 pointer-events-none">
                  <TaskCard
                    task={activeTask}
                    statuses={statuses}
                    onEdit={() => { }}
                    onDelete={() => { }}
                    onStatusChange={() => { }}
                  />
                </div>
              )}
            </DragOverlay>
          </DndContext>
          </div>
        )}
      </div>

      {/* Create/Edit Task Modal */}
      <TaskModal
        open={modalOpen || !!editingTask}
        onClose={() => {
          setModalOpen(false);
          setEditingTask(null);
        }}
        onSubmit={editingTask ? handleEditTask : handleCreateTask}
        task={editingTask}
        isLoading={isSubmitting}
      />

      {/* Delete Task Confirmation */}
      <AlertDialog open={!!deletingTask} onOpenChange={() => setDeletingTask(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Task</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deletingTask?.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteTask}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Status Confirmation */}
      <AlertDialog open={!!deletingStatus} onOpenChange={() => setDeletingStatus(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Status</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deletingStatus?.name}"? This will fail if any tasks
              are currently using this status.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteStatus}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Status Management Side Panel */}
      <Sheet open={statusPanelOpen} onOpenChange={setStatusPanelOpen}>
        <SheetContent className="w-full sm:max-w-md flex flex-col gap-0 p-0">
          <SheetHeader className="px-6 py-5 border-b">
            <SheetTitle>Manage Statuses</SheetTitle>
          </SheetHeader>

          <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
            {/* Status list */}
            <div className="space-y-2">
              {statuses.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No statuses yet. Add one below.
                </p>
              )}
              {statuses.map((status, idx) => {
                const borderColor = COLUMN_BORDER_COLORS[Math.min(idx, COLUMN_BORDER_COLORS.length - 1)];
                const taskCount = tasks.filter((t) => t.status_id === status.status_id).length;
                const isEditing = editingStatus?.status_id === status.status_id;

                return (
                  <div
                    key={status.status_id}
                    className={cn(
                      'flex items-center gap-2 p-3 rounded-lg border bg-card',
                      `border-l-4 ${borderColor}`
                    )}
                  >
                    {isEditing ? (
                      <>
                        <Input
                          value={editingStatusName}
                          onChange={(e) => setEditingStatusName(e.target.value)}
                          className="h-7 text-sm flex-1"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleUpdateStatus();
                            if (e.key === 'Escape') setEditingStatus(null);
                          }}
                          autoFocus
                        />
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 text-green-600"
                          onClick={handleUpdateStatus}
                          disabled={statusSubmitting}
                        >
                          <Check className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          onClick={() => setEditingStatus(null)}
                        >
                          <X className="h-3.5 w-3.5" />
                        </Button>
                      </>
                    ) : (
                      <>
                        <span className="flex-1 text-sm font-medium">{status.name}</span>
                        <span className="text-xs text-muted-foreground">{taskCount} task{taskCount !== 1 ? 's' : ''}</span>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7"
                          onClick={() => {
                            setEditingStatus(status);
                            setEditingStatusName(status.name);
                          }}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 text-destructive hover:text-destructive"
                          onClick={() => setDeletingStatus(status)}
                          disabled={taskCount > 0}
                          title={taskCount > 0 ? 'Cannot delete: tasks are using this status' : 'Delete status'}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Add new status */}
            <div className="space-y-3">
              {statuses.length >= MAX_STATUSES && (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400">
                  <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                  <p className="text-xs">
                    Maximum of {MAX_STATUSES} statuses reached. Delete an existing status to add a new one.
                  </p>
                </div>
              )}
              <div className="space-y-1.5">
                <Label className="text-sm">Add New Status</Label>
                <div className="flex gap-2">
                  <Input
                    value={newStatusName}
                    onChange={(e) => setNewStatusName(e.target.value)}
                    placeholder="Status name..."
                    className="text-sm"
                    disabled={statuses.length >= MAX_STATUSES || statusSubmitting}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCreateStatus();
                    }}
                  />
                  <Button
                    size="sm"
                    onClick={handleCreateStatus}
                    disabled={
                      !newStatusName.trim() ||
                      statuses.length >= MAX_STATUSES ||
                      statusSubmitting
                    }
                  >
                    {statusSubmitting ? <LoadingSpinner size="sm" /> : <Plus className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </DashboardLayout>
  );
};

export default ProjectDetailsPage;
