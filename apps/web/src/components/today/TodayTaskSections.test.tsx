import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import TodayTaskSections from './TodayTaskSections';

const task = (id: string, name: string) => ({
  task_id: id,
  project_id: 'project-1',
  name,
  description: null,
  due_date: '2026-09-17',
  priority: 'none' as const,
  labels: [],
  subtasks: [],
  status_id: 'status-1',
  status_name: 'To Do',
  created_by: 'member-1',
  created_at: '2026-09-17T00:00:00Z',
  updated_at: '2026-09-17T00:00:00Z',
});

describe('TodayTaskSections', () => {
  it('shows ordered Today tasks, due groups, and disables adding at the three-task limit', () => {
    render(
      <TodayTaskSections
        today={{
          local_date: '2026-09-17',
          selected_tasks: [
            { position: 0, task: task('task-1', 'Prepare brief') },
            { position: 1, task: task('task-2', 'Send brief') },
            { position: 2, task: task('task-3', 'Review brief') },
          ],
          due_today: [task('task-2', 'Send brief')],
          overdue: [task('task-4', 'Approve contract')],
          available_tasks: [task('task-4', 'Approve contract')],
        }}
        onAdd={vi.fn()}
        onRemove={vi.fn()}
        onReorder={vi.fn()}
      />
    );

    expect(screen.getByRole('heading', { name: 'Today' })).toBeInTheDocument();
    expect(screen.getAllByText('Prepare brief')).toHaveLength(1);
    expect(screen.getByText('Due today')).toBeInTheDocument();
    expect(screen.getByText('Overdue')).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: 'Add a Task to Today' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Move Send brief up' })).toBeInTheDocument();
  });
});
