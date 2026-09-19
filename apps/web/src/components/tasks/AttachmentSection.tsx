import { ChangeEvent, useCallback, useEffect, useState } from 'react';
import { Download, Paperclip, Trash2, Upload } from 'lucide-react';

import { attachmentApi, Attachment } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

type AttachmentApi = {
  list: (taskId: string) => Promise<{ data?: Attachment[]; error?: string }>;
  initiate: (taskId: string, file: File) => Promise<{ data?: Attachment; error?: string }>;
  finalize: (taskId: string, attachmentId: string) => Promise<{ data?: Attachment; error?: string }>;
  download: (taskId: string, attachmentId: string) => Promise<{ data?: Blob; error?: string }>;
  delete: (taskId: string, attachmentId: string) => Promise<{ error?: string }>;
};

interface AttachmentSectionProps {
  taskId: string;
  api?: AttachmentApi;
}

const formatSize = (bytes: number) => bytes < 1024 * 1024
  ? `${Math.max(1, Math.ceil(bytes / 1024))} KB`
  : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;

const AttachmentSection = ({ taskId, api = attachmentApi }: AttachmentSectionProps) => {
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    const response = await api.list(taskId);
    if (response.error) setError(response.error);
    else setAttachments(response.data || []);
    setIsLoading(false);
  }, [api, taskId]);

  useEffect(() => { load(); }, [load]);

  const upload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setError(null);
    setUploading(true);
    try {
      const initiated = await api.initiate(taskId, file);
      if (!initiated.data) throw new Error(initiated.error || 'Could not start upload.');
      setAttachments((items) => [...items, initiated.data]);
      const finalized = await api.finalize(taskId, initiated.data.attachment_id);
      if (!finalized.data) throw new Error(finalized.error || 'Could not finish upload.');
      setAttachments((items) => items.map((item) => (
        item.attachment_id === finalized.data!.attachment_id ? finalized.data! : item
      )));
    } catch {
      setError('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const download = async (attachment: Attachment) => {
    setError(null);
    const response = await api.download(taskId, attachment.attachment_id);
    if (!response.data) {
      setError(response.error || 'Download failed. Please try again.');
      return;
    }
    const url = URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = attachment.filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  const remove = async (attachment: Attachment) => {
    setError(null);
    const response = await api.delete(taskId, attachment.attachment_id);
    if (response.error) {
      setError(response.error);
      return;
    }
    setAttachments((items) => items.filter((item) => item.attachment_id !== attachment.attachment_id));
  };

  return (
    <section className="space-y-2" aria-label="Attachments">
      <div className="flex items-center justify-between gap-2">
        <Label htmlFor={`attachment-${taskId}`}>Attachments</Label>
        <label className="inline-flex cursor-pointer items-center gap-1 text-sm text-primary hover:underline">
          <Upload className="h-3.5 w-3.5" />
          {uploading ? 'Uploading…' : 'Attach a file'}
          <Input
            id={`attachment-${taskId}`}
            aria-label="Attach a file"
            className="sr-only"
            type="file"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,image/jpeg,image/png,image/gif,image/webp"
            onChange={upload}
            disabled={uploading}
          />
        </label>
      </div>
      <p className="text-xs text-muted-foreground">Documents and images up to 10 MB.</p>
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      {isLoading ? <p className="text-sm text-muted-foreground">Loading attachments…</p> : (
        <div className="space-y-1">
          {attachments.length === 0 && <p className="text-sm text-muted-foreground">No attachments yet.</p>}
          {attachments.map((attachment) => (
            <div key={attachment.attachment_id} className="flex items-center gap-2 rounded border px-2 py-1.5 text-sm">
              <Paperclip className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              <span className="min-w-0 flex-1 truncate">{attachment.filename}</span>
              <span className="text-xs text-muted-foreground">{formatSize(attachment.byte_size)}</span>
              {attachment.state === 'pending' ? (
                <span className="text-xs text-muted-foreground">Pending upload</span>
              ) : (
                <Button type="button" variant="ghost" size="sm" onClick={() => download(attachment)} aria-label={`Download ${attachment.filename}`}>
                  <Download className="h-3.5 w-3.5" />
                </Button>
              )}
              <Button type="button" variant="ghost" size="sm" onClick={() => remove(attachment)} aria-label={`Delete ${attachment.filename}`}>
                <Trash2 className="h-3.5 w-3.5 text-destructive" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
};

export default AttachmentSection;
