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

  it('reports a direct-upload failure to the member', async () => {
    attachmentApi.list.mockResolvedValue({ data: [] });
    attachmentApi.initiate.mockResolvedValue({
      data: {
        attachment: { attachment_id: 'attachment-1', filename: 'brief.pdf', media_type: 'application/pdf', byte_size: 512, state: 'pending', created_at: '2026-09-17T00:00:00Z' },
        upload_url: 'https://storage.example.test/upload/attachment-1',
      },
    });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }));

    render(<AttachmentSection taskId="task-1" api={attachmentApi} />);
    await screen.findByText('No attachments yet.');

    fireEvent.change(screen.getByLabelText('Attach a file'), {
      target: { files: [new File(['brief'], 'brief.pdf', { type: 'application/pdf' })] },
    });

    await waitFor(() => expect(screen.getByText('Upload failed. Please try again.')).toBeInTheDocument());
  });

  it('submits a signed POST ticket as multipart form data before finalizing', async () => {
    attachmentApi.list.mockResolvedValue({ data: [] });
    attachmentApi.initiate.mockResolvedValue({
      data: {
        attachment: { attachment_id: 'attachment-2', filename: 'brief.pdf', media_type: 'application/pdf', byte_size: 5, state: 'pending', created_at: '2026-09-17T00:00:00Z' },
        upload_url: 'https://storage.example.test/upload/attachment-2',
        upload_method: 'POST',
        upload_fields: { policy: 'signed-policy' },
      },
    });
    attachmentApi.finalize.mockResolvedValue({
      data: { attachment_id: 'attachment-2', filename: 'brief.pdf', media_type: 'application/pdf', byte_size: 5, state: 'available', created_at: '2026-09-17T00:00:00Z' },
    });
    const directUpload = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal('fetch', directUpload);

    render(<AttachmentSection taskId="task-1" api={attachmentApi} />);
    await screen.findByText('No attachments yet.');
    fireEvent.change(screen.getByLabelText('Attach a file'), {
      target: { files: [new File(['brief'], 'brief.pdf', { type: 'application/pdf' })] },
    });

    await waitFor(() => expect(directUpload).toHaveBeenCalledWith(
      'https://storage.example.test/upload/attachment-2',
      expect.objectContaining({ method: 'POST', body: expect.any(FormData) }),
    ));
    expect(attachmentApi.finalize).toHaveBeenCalledWith('task-1', 'attachment-2');
  });
});
