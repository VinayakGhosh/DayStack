import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import AttachmentSection from './AttachmentSection';

const attachmentApi = {
  list: vi.fn(),
  initiate: vi.fn(),
  finalize: vi.fn(),
  download: vi.fn(),
  delete: vi.fn(),
};

describe('AttachmentSection', () => {
  it('shows pending and available attachment states without showing storage keys', async () => {
    attachmentApi.list.mockResolvedValue({
      data: [
        { attachment_id: 'pending-1', filename: 'draft.pdf', media_type: 'application/pdf', byte_size: 512, state: 'pending', created_at: '2026-09-17T00:00:00Z' },
        { attachment_id: 'ready-1', filename: 'brief.pdf', media_type: 'application/pdf', byte_size: 1024, state: 'available', created_at: '2026-09-17T00:00:00Z' },
      ],
    });

    render(<AttachmentSection taskId="task-1" api={attachmentApi} />);

    expect(await screen.findByText('draft.pdf')).toBeInTheDocument();
    expect(screen.getByText('Pending upload')).toBeInTheDocument();
    expect(screen.getByText('brief.pdf')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Download brief.pdf' })).toBeInTheDocument();
    expect(screen.queryByText(/private\//)).not.toBeInTheDocument();
  });

  it('reports an API upload failure to the member', async () => {
    attachmentApi.list.mockResolvedValue({ data: [] });
    attachmentApi.initiate.mockResolvedValue({ error: 'Upload failed' });

    render(<AttachmentSection taskId="task-1" api={attachmentApi} />);
    await screen.findByText('No attachments yet.');

    fireEvent.change(screen.getByLabelText('Attach a file'), {
      target: { files: [new File(['brief'], 'brief.pdf', { type: 'application/pdf' })] },
    });

    await waitFor(() => expect(screen.getByText('Upload failed. Please try again.')).toBeInTheDocument());
  });

  it('finalizes the pending database upload after the API accepts the file', async () => {
    attachmentApi.list.mockResolvedValue({ data: [] });
    attachmentApi.initiate.mockResolvedValue({
      data: { attachment_id: 'attachment-2', filename: 'brief.pdf', media_type: 'application/pdf', byte_size: 5, state: 'pending', created_at: '2026-09-17T00:00:00Z' },
    });
    attachmentApi.finalize.mockResolvedValue({
      data: { attachment_id: 'attachment-2', filename: 'brief.pdf', media_type: 'application/pdf', byte_size: 5, state: 'available', created_at: '2026-09-17T00:00:00Z' },
    });
    render(<AttachmentSection taskId="task-1" api={attachmentApi} />);
    await screen.findByText('No attachments yet.');
    fireEvent.change(screen.getByLabelText('Attach a file'), {
      target: { files: [new File(['brief'], 'brief.pdf', { type: 'application/pdf' })] },
    });

    await waitFor(() => expect(attachmentApi.finalize).toHaveBeenCalledWith('task-1', 'attachment-2'));
  });
});
