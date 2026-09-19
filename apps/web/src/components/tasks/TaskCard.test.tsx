import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import TaskCard from './TaskCard';
import type { ProjectStatus, Task } from '@/lib/api';

const statuses: ProjectStatus[] = [
  { status_id: 'active', project_id: 'p1', name: 'Doing', is_completion: false, display_order: 1, created_at: '', updated_at: '' },
  { status_id: 'done', project_id: 'p1', name: 'Shipped', is_completion: true, display_order: 0, created_at: '', updated_at: '' },
];

const task: Task = {
  task_id: 't1', project_id: 'p1', name: 'Prepare brief', description: 'Two useful lines',
  due_date: '2026-09-20', priority: 'high', status_id: 'active', status_name: 'Doing', created_by: 'm1',
  labels: [
    { label_id: 'l1', name: 'Client' }, { label_id: 'l2', name: 'Research' }, { label_id: 'l3', name: 'Launch' },
  ],
  subtasks: [
    { subtask_id: 's1', text: 'One', display_order: 0, is_completed: true },
    { subtask_id: 's2', text: 'Two', display_order: 1, is_completed: false },
  ],
  attachment_count: 2, created_at: '', updated_at: '',
};

describe('TaskCard', () => {
  it('opens details by click and keyboard while controls stay isolated', () => {
    const onOpen = vi.fn();
    const onToggleCompletion = vi.fn();
    render(<TaskCard task={task} statuses={statuses} onOpen={onOpen} onDelete={vi.fn()} onToggleCompletion={onToggleCompletion} dragHandleProps={{ onPointerDown: vi.fn() }} />);

    fireEvent.click(screen.getByRole('button', { name: 'Open details for Prepare brief' }));
    fireEvent.keyDown(screen.getByRole('button', { name: 'Open details for Prepare brief' }), { key: 'Enter' });
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.pointerDown(screen.getByRole('button', { name: 'Drag Prepare brief' }));

    expect(onOpen).toHaveBeenCalledTimes(2);
    expect(onToggleCompletion).toHaveBeenCalledWith(task, true);
  });

  it('uses is_completion and renders compact metadata', () => {
    render(<TaskCard task={task} statuses={statuses} onOpen={vi.fn()} onDelete={vi.fn()} onToggleCompletion={vi.fn()} now={new Date(2026, 8, 20)} />);

    expect(screen.getByText('Today')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Client')).toBeInTheDocument();
    expect(screen.getByText('Research')).toBeInTheDocument();
    expect(screen.getByText('+1')).toBeInTheDocument();
    expect(screen.getByText('1/2')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByRole('checkbox')).not.toBeChecked();
  });

  it('marks active past dates as Overdue but not completed dates', () => {
    const { rerender } = render(<TaskCard task={{ ...task, due_date: '2026-09-19' }} statuses={statuses} onOpen={vi.fn()} onDelete={vi.fn()} onToggleCompletion={vi.fn()} now={new Date(2026, 8, 20)} />);
    expect(screen.getByText(/Overdue/)).toBeInTheDocument();

    rerender(<TaskCard task={{ ...task, due_date: '2026-09-19', status_id: 'done' }} statuses={statuses} onOpen={vi.fn()} onDelete={vi.fn()} onToggleCompletion={vi.fn()} now={new Date(2026, 8, 20)} />);
    expect(screen.queryByText(/Overdue/)).not.toBeInTheDocument();
    expect(screen.getByText(/19 Sep/)).toBeInTheDocument();
    expect(screen.getByRole('checkbox')).toBeChecked();
  });
});
