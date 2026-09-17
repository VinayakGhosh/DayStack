import { useState, useEffect } from 'react';
import { Label as TaskLabel, labelsApi, Priority, Task, TaskInput } from '@/lib/api';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import AttachmentSection from '@/components/tasks/AttachmentSection';

interface TaskModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: TaskInput) => Promise<void>;
  task?: Task | null;
  labels: TaskLabel[];
  isLoading?: boolean;
}

const TaskModal = ({ open, onClose, onSubmit, task, labels, isLoading }: TaskModalProps) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [priority, setPriority] = useState<Priority>('none');
  const [labelIds, setLabelIds] = useState<string[]>([]);
  const [subtasks, setSubtasks] = useState<{ text: string; is_completed: boolean }[]>([]);
  const [newSubtask, setNewSubtask] = useState('');
  const [availableLabels, setAvailableLabels] = useState(labels);
  const [newLabelName, setNewLabelName] = useState('');
  const [errors, setErrors] = useState<{ name?: string }>({});

  useEffect(() => {
    if (task) {
      setName(task.name);
      setDescription(task.description || '');
      setDueDate(task.due_date || '');
      setPriority(task.priority || 'none');
      setLabelIds(task.labels.map((label) => label.label_id));
      setSubtasks(task.subtasks.map(({ text, is_completed }) => ({ text, is_completed })));
    } else {
      setName('');
      setDescription('');
      setDueDate('');
      setPriority('none');
      setLabelIds([]);
      setSubtasks([]);
    }
    setErrors({});
    setAvailableLabels(labels);
  }, [task, open, labels]);

  const validate = () => {
    const newErrors: { name?: string } = {};
    if (!name.trim()) {
      newErrors.name = 'Task name is required';
    } else if (name.length > 200) {
      newErrors.name = 'Task name must be less than 200 characters';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    await onSubmit({
      name: name.trim(),
      description: description.trim() || null,
      due_date: dueDate || null,
      priority,
      label_ids: labelIds,
      subtasks,
    });
  };

  const createLabel = async () => {
    if (!newLabelName.trim()) return;
    const { data } = await labelsApi.create({ name: newLabelName.trim() });
    if (data) {
      setAvailableLabels((previous) => [...previous, data]);
      setLabelIds((previous) => [...previous, data.label_id]);
      setNewLabelName('');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>{task ? 'Edit Task' : 'Create New Task'}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Task Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter task name"
                className={errors.name ? 'border-destructive' : ''}
                autoFocus
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name}</p>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="due-date">Due date</Label>
                <Input id="due-date" type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="priority">Priority</Label>
                <select id="priority" className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm" value={priority} onChange={(event) => setPriority(event.target.value as Priority)}>
                  <option value="none">None</option><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option>
                </select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Labels</Label>
              <div className="flex flex-wrap gap-2">
                {availableLabels.map((label) => <label key={label.label_id} className="flex items-center gap-1 rounded border px-2 py-1 text-sm"><input type="checkbox" checked={labelIds.includes(label.label_id)} onChange={() => setLabelIds((previous) => previous.includes(label.label_id) ? previous.filter((id) => id !== label.label_id) : [...previous, label.label_id])} />{label.name}</label>)}
              </div>
              <div className="flex gap-2"><Input value={newLabelName} onChange={(event) => setNewLabelName(event.target.value)} placeholder="New Label" /><Button type="button" variant="outline" onClick={createLabel}>Add Label</Button></div>
            </div>
            <div className="space-y-2">
              <Label>Subtasks</Label>
              {subtasks.map((subtask, index) => <div key={`${subtask.text}-${index}`} className="flex items-center gap-2"><input type="checkbox" checked={subtask.is_completed} onChange={() => setSubtasks((previous) => previous.map((item, position) => position === index ? { ...item, is_completed: !item.is_completed } : item))} /><span className="flex-1 text-sm">{subtask.text}</span><Button type="button" variant="ghost" size="sm" onClick={() => setSubtasks((previous) => previous.filter((_, position) => position !== index))}>Remove</Button></div>)}
              <div className="flex gap-2"><Input value={newSubtask} onChange={(event) => setNewSubtask(event.target.value)} placeholder="Add a Subtask" onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); if (newSubtask.trim()) { setSubtasks((previous) => [...previous, { text: newSubtask.trim(), is_completed: false }]); setNewSubtask(''); } } }} /><Button type="button" variant="outline" onClick={() => { if (newSubtask.trim()) { setSubtasks((previous) => [...previous, { text: newSubtask.trim(), is_completed: false }]); setNewSubtask(''); } }}>Add</Button></div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter task description (optional)"
                rows={3}
              />
            </div>
            {task && <AttachmentSection taskId={task.task_id} />}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose} disabled={isLoading}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading && <LoadingSpinner size="sm" className="mr-2" />}
              {task ? 'Save Changes' : 'Create Task'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default TaskModal;
