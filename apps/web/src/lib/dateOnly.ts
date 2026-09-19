export const parseDateOnly = (value: string): Date => {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day);
};

export const formatTaskDueDate = (
  value: string,
  completed: boolean,
  now = new Date(),
): { text: string; overdue: boolean } => {
  const due = parseDateOnly(value);
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const compact = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short' }).format(due);
  if (due.getTime() === today.getTime()) return { text: 'Today', overdue: false };
  if (!completed && due < today) return { text: `Overdue · ${compact}`, overdue: true };
  return { text: compact, overdue: false };
};
