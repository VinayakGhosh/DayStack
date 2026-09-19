import { useEffect, useMemo, useRef, useState } from 'react';
import { Check, Info, Plus, Search, X } from 'lucide-react';

import type { Label as TaskLabel, Priority, Task, TaskInput } from '@/lib/api';
import AttachmentSection, { type AttachmentSectionHandle } from '@/components/tasks/AttachmentSection';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Textarea } from '@/components/ui/textarea';

interface SubmitResult { task?: Task; error?: string }
interface TaskModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: TaskInput) => Promise<SubmitResult>;
  onLabelsChange?: (labels: TaskLabel[]) => void;
  onAttachmentsChange?: () => void;
  task?: Task | null;
  labels: TaskLabel[];
  isLoading?: boolean;
}

const help = {
  labels: 'Use labels to group related tasks across projects—for example, Client Work or Research. You can reuse labels on other tasks.',
  subtasks: 'Break this task into smaller checklist steps. Subtasks stay inside this task and can be completed individually.',
};

const TaskModal = ({ open, onClose, onSubmit, onLabelsChange, onAttachmentsChange, task, labels, isLoading }: TaskModalProps) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [priority, setPriority] = useState<Priority>('none');
  const [labelIds, setLabelIds] = useState<string[]>([]);
  const [stagedLabelNames, setStagedLabelNames] = useState<string[]>([]);
  const [labelQuery, setLabelQuery] = useState('');
  const [subtasks, setSubtasks] = useState<{ text: string; is_completed: boolean }[]>([]);
  const [subtaskDraft, setSubtaskDraft] = useState('');
  const [queueCount, setQueueCount] = useState(0);
  const [uploadsActive, setUploadsActive] = useState(false);
  const [discardOpen, setDiscardOpen] = useState(false);
  const [cancelUploadsOpen, setCancelUploadsOpen] = useState(false);
  const [errors, setErrors] = useState<{ name?: string; save?: string; label?: string }>({});
  const initialSnapshot = useRef('');
  const attachmentRef = useRef<AttachmentSectionHandle>(null);

  const snapshot = useMemo(() => JSON.stringify({
    name: name.trim(), description: description.trim(), dueDate, priority,
    labelIds: [...labelIds].sort(), stagedLabelNames: stagedLabelNames.map((item) => item.trim()).sort(),
    subtasks: [...subtasks, ...(subtaskDraft.trim() ? [{ text: subtaskDraft.trim(), is_completed: false }] : [])], queueCount,
  }), [description, dueDate, labelIds, name, priority, queueCount, stagedLabelNames, subtaskDraft, subtasks]);
  const dirty = open && initialSnapshot.current !== snapshot;

  useEffect(() => {
    if (!open) return;
    const values = task ? {
      name: task.name, description: task.description || '', dueDate: task.due_date || '', priority: task.priority || 'none' as Priority,
      labelIds: task.labels.map((label) => label.label_id), subtasks: task.subtasks.map(({ text, is_completed }) => ({ text, is_completed })),
    } : { name: '', description: '', dueDate: '', priority: 'none' as Priority, labelIds: [], subtasks: [] };
    setName(values.name); setDescription(values.description); setDueDate(values.dueDate); setPriority(values.priority);
    setLabelIds(values.labelIds); setSubtasks(values.subtasks); setStagedLabelNames([]); setLabelQuery(''); setSubtaskDraft('');
    setQueueCount(0); setErrors({}); setUploadsActive(false);
    initialSnapshot.current = JSON.stringify({
      name: values.name.trim(), description: values.description.trim(), dueDate: values.dueDate,
      priority: values.priority, labelIds: [...values.labelIds].sort(), stagedLabelNames: [],
      subtasks: values.subtasks, queueCount: 0,
    });
  }, [open, task]);

  const requestClose = () => {
    if (uploadsActive) { setCancelUploadsOpen(true); return; }
    if (dirty) { setDiscardOpen(true); return; }
    onClose();
  };

  const commitDraft = () => {
    const text = subtaskDraft.trim();
    if (!text) return subtasks;
    const committed = [...subtasks, { text, is_completed: false }];
    setSubtasks(committed); setSubtaskDraft('');
    return committed;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim()) { setErrors({ name: 'Task name is required' }); return; }
    if (name.trim().length > 200) { setErrors({ name: 'Task name must be at most 200 characters' }); return; }
    const committedSubtasks = commitDraft();
    setErrors({});
    const result = await onSubmit({
      name: name.trim(), description: description.trim() || null, due_date: dueDate || null, priority,
      label_ids: labelIds, label_names: stagedLabelNames, subtasks: committedSubtasks,
    });
    if (!result.task) { setErrors((current) => ({ ...current, save: result.error || 'Task could not be saved. Please try again.' })); return; }
    onLabelsChange?.(result.task.labels);
    if (attachmentRef.current?.hasQueuedFiles()) {
      const allUploaded = await attachmentRef.current.uploadQueued(result.task.task_id);
      if (!allUploaded) { setErrors((current) => ({ ...current, save: 'The Task was saved, but one or more Attachments failed. Retry or remove them.' })); return; }
    }
    onClose();
  };

  const normalizedQuery = labelQuery.trim().toLocaleLowerCase();
  const matchingLabels = labels.filter((label) => label.name.toLocaleLowerCase().includes(normalizedQuery));
  const exactMatch = labels.some((label) => label.name.toLocaleLowerCase() === normalizedQuery)
    || stagedLabelNames.some((name) => name.toLocaleLowerCase() === normalizedQuery);
  const stageLabel = () => {
    const value = ' '.concat(labelQuery).trim().replace(/\s+/g, ' ');
    if (!value) return;
    if (value.length > 64) { setErrors((current) => ({ ...current, label: 'Label names can be at most 64 characters.' })); return; }
    setStagedLabelNames((current) => [...current, value]); setLabelQuery(''); setErrors((current) => ({ ...current, label: undefined }));
  };

  return (
    <>
      <Dialog open={open} onOpenChange={(next) => !next && requestClose()}>
        <DialogContent className="flex max-h-[95vh] w-[calc(100vw-1rem)] max-w-2xl flex-col gap-0 overflow-hidden p-0 sm:max-h-[90vh]" onEscapeKeyDown={(event) => { if (dirty || uploadsActive) event.preventDefault(); }} onPointerDownOutside={(event) => { if (dirty || uploadsActive) event.preventDefault(); }}>
          <DialogHeader className="shrink-0 border-b px-6 py-4"><DialogTitle>{task ? 'Task Details' : 'Create Task'}</DialogTitle><DialogDescription className="sr-only">{task ? 'Review and edit this Task.' : 'Create a Task and optionally stage Labels, Subtasks, and Attachments.'}</DialogDescription></DialogHeader>
          <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
            <div className="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-5">
              <div className="space-y-2"><Label htmlFor="task-name">Name *</Label><Input id="task-name" value={name} onChange={(event) => setName(event.target.value)} autoFocus aria-invalid={Boolean(errors.name)} />{errors.name && <p role="alert" className="text-sm text-destructive">{errors.name}</p>}</div>
              <div className="space-y-2"><Label htmlFor="task-description">Description</Label><Textarea id="task-description" value={description} onChange={(event) => setDescription(event.target.value)} rows={3} /></div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2"><Label htmlFor="task-due-date">Due date</Label><Input id="task-due-date" type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} /></div>
                <div className="space-y-2"><Label htmlFor="task-priority">Priority</Label><select id="task-priority" className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm" value={priority} onChange={(event) => setPriority(event.target.value as Priority)}><option value="none">None</option><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-1"><Label htmlFor="label-search">Labels</Label><Popover><PopoverTrigger asChild><Button type="button" variant="ghost" size="icon" className="h-6 w-6" aria-label="About Labels"><Info className="h-3.5 w-3.5" /></Button></PopoverTrigger><PopoverContent className="text-sm">{help.labels}</PopoverContent></Popover></div>
                <div className="flex flex-wrap gap-1.5">{labels.filter((label) => labelIds.includes(label.label_id)).map((label) => <Badge key={label.label_id} variant="secondary">{label.name}<button type="button" className="ml-1" aria-label={`Remove ${label.name}`} onClick={() => setLabelIds((current) => current.filter((id) => id !== label.label_id))}><X className="h-3 w-3" /></button></Badge>)}{stagedLabelNames.map((label) => <Badge key={label} variant="outline">{label}<button type="button" className="ml-1" aria-label={`Remove ${label}`} onClick={() => setStagedLabelNames((current) => current.filter((name) => name !== label))}><X className="h-3 w-3" /></button></Badge>)}</div>
                <div className="relative"><Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" /><Input id="label-search" value={labelQuery} onChange={(event) => setLabelQuery(event.target.value)} className="pl-9" placeholder="Search or create a Label" /></div>
                {labelQuery && <div className="max-h-40 overflow-y-auto rounded-md border p-1">{matchingLabels.map((label) => <button key={label.label_id} type="button" className="flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-sm hover:bg-muted" onClick={() => setLabelIds((current) => current.includes(label.label_id) ? current.filter((id) => id !== label.label_id) : [...current, label.label_id])}>{label.name}{labelIds.includes(label.label_id) && <Check className="h-4 w-4" />}</button>)}{!exactMatch && <button type="button" className="flex w-full items-center rounded px-2 py-1.5 text-left text-sm text-primary hover:bg-muted" onClick={stageLabel}><Plus className="mr-2 h-4 w-4" />Create “{labelQuery.trim()}”</button>}</div>}
                {errors.label && <p role="alert" className="text-sm text-destructive">{errors.label}</p>}
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-1"><Label htmlFor="subtask-draft">Subtasks</Label><Popover><PopoverTrigger asChild><Button type="button" variant="ghost" size="icon" className="h-6 w-6" aria-label="About Subtasks"><Info className="h-3.5 w-3.5" /></Button></PopoverTrigger><PopoverContent className="text-sm">{help.subtasks}</PopoverContent></Popover></div>
                {subtasks.map((subtask, index) => <div key={`${subtask.text}-${index}`} className="flex items-center gap-2"><input aria-label={`Complete ${subtask.text}`} type="checkbox" checked={subtask.is_completed} onChange={() => setSubtasks((current) => current.map((item, position) => position === index ? { ...item, is_completed: !item.is_completed } : item))} /><span className="flex-1 text-sm">{subtask.text}</span><Button type="button" variant="ghost" size="sm" onClick={() => setSubtasks((current) => current.filter((_, position) => position !== index))}>Remove</Button></div>)}
                <div className="flex gap-2"><Input id="subtask-draft" value={subtaskDraft} onChange={(event) => setSubtaskDraft(event.target.value)} placeholder="Add a Subtask" onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); commitDraft(); } }} /><Button type="button" variant="outline" onClick={commitDraft}>Add</Button></div>
              </div>
              <AttachmentSection ref={attachmentRef} taskId={task?.task_id} onQueueChange={setQueueCount} onUploadingChange={setUploadsActive} onAvailableChange={onAttachmentsChange} />
            </div>
            <DialogFooter className="shrink-0 border-t bg-background px-6 py-4 sm:items-center">
              {errors.save && <p role="alert" className="mr-auto text-sm text-destructive">{errors.save}</p>}
              <Button type="button" variant="outline" onClick={requestClose} disabled={Boolean(isLoading)}>Cancel</Button>
              <Button type="submit" disabled={Boolean(isLoading) || uploadsActive}>{isLoading && <LoadingSpinner size="sm" className="mr-2" />}{task ? 'Save changes' : 'Create Task'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={discardOpen} onOpenChange={setDiscardOpen}><AlertDialogContent><AlertDialogHeader><AlertDialogTitle>Discard changes?</AlertDialogTitle><AlertDialogDescription>Your unsaved Task changes will be lost.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel>Keep editing</AlertDialogCancel><AlertDialogAction onClick={() => { setDiscardOpen(false); onClose(); }}>Discard</AlertDialogAction></AlertDialogFooter></AlertDialogContent></AlertDialog>
      <AlertDialog open={cancelUploadsOpen} onOpenChange={setCancelUploadsOpen}><AlertDialogContent><AlertDialogHeader><AlertDialogTitle>Uploads are still active</AlertDialogTitle><AlertDialogDescription>Closing now cancels unfinished Attachment uploads.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel>Keep editing</AlertDialogCancel><AlertDialogAction onClick={() => { attachmentRef.current?.abortUploads(); setCancelUploadsOpen(false); onClose(); }}>Cancel uploads and close</AlertDialogAction></AlertDialogFooter></AlertDialogContent></AlertDialog>
    </>
  );
};

export default TaskModal;
