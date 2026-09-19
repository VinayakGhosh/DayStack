import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import TaskModal from './TaskModal';
import type { Task } from '@/lib/api';

const savedTask: Task = {
  task_id: 't1', project_id: 'p1', name: 'Prepare brief', description: null, due_date: null,
  priority: 'none', label_ids: [], labels: [], subtasks: [], attachment_count: 0,
  status_id: 'active', status_name: 'To Do', created_by: 'm1', created_at: '', updated_at: '',
} as Task;

describe('TaskModal', () => {
  it('stages a new Label and commits the Subtask draft during save', async () => {
    const onSubmit = vi.fn().mockResolvedValue({ task: savedTask });
    const onClose = vi.fn();
    render(<TaskModal open onClose={onClose} onSubmit={onSubmit} labels={[]} />);

    fireEvent.change(screen.getByLabelText('Name *'), { target: { value: 'Prepare brief' } });
    fireEvent.change(screen.getByPlaceholderText('Search or create a Label'), { target: { value: 'Client Work' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create “Client Work”' }));
    fireEvent.change(screen.getByPlaceholderText('Add a Subtask'), { target: { value: 'Send draft' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create Task' }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
      label_names: ['Client Work'],
      subtasks: [{ text: 'Send draft', is_completed: false }],
    })));
    expect(onClose).toHaveBeenCalled();
  });

  it('asks before discarding dirty changes', async () => {
    const onClose = vi.fn();
    render(<TaskModal open onClose={onClose} onSubmit={vi.fn()} labels={[]} />);
    fireEvent.change(screen.getByLabelText('Name *'), { target: { value: 'Unsaved' } });
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(await screen.findByText('Discard changes?')).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Discard' }));
    expect(onClose).toHaveBeenCalled();
  });

  it('keeps field values and shows an actionable save error', async () => {
    const onSubmit = vi.fn().mockResolvedValue({ error: 'The service is unavailable.' });
    render(<TaskModal open onClose={vi.fn()} onSubmit={onSubmit} labels={[]} />);
    const name = screen.getByLabelText('Name *');
    fireEvent.change(name, { target: { value: 'Prepare brief' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create Task' }));

    expect(await screen.findByText('The service is unavailable.')).toBeInTheDocument();
    expect(name).toHaveValue('Prepare brief');
  });
});
