import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react';
import { Download, Eye, ImageIcon, Paperclip, RotateCcw, Trash2, Upload, X } from 'lucide-react';

import { attachmentApi, type Attachment } from '@/lib/api';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

type AttachmentApi = {
  list: (taskId: string) => Promise<{ data?: Attachment[]; error?: string }>;
  initiate: (taskId: string, file: File, signal?: AbortSignal) => Promise<{ data?: Attachment; error?: string }>;
  finalize: (taskId: string, attachmentId: string, signal?: AbortSignal) => Promise<{ data?: Attachment; error?: string }>;
  download: (taskId: string, attachmentId: string) => Promise<{ data?: Blob; error?: string }>;
  delete: (taskId: string, attachmentId: string) => Promise<{ error?: string }>;
};

type QueueItem = {
  id: string;
  file: File;
  state: 'queued' | 'uploading' | 'available' | 'failed';
  error?: string;
  previewUrl?: string;
  attachment?: Attachment;
};

export interface AttachmentSectionHandle {
  uploadQueued: (taskId: string) => Promise<boolean>;
  abortUploads: () => void;
  hasQueuedFiles: () => boolean;
}

interface AttachmentSectionProps {
  taskId?: string;
  api?: AttachmentApi;
  onQueueChange?: (count: number) => void;
  onUploadingChange?: (uploading: boolean) => void;
  onAvailableChange?: () => void;
}

const ACCEPT = '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,image/jpeg,image/png,image/gif,image/webp';
const formatSize = (bytes: number) => bytes < 1024 * 1024 ? `${Math.max(1, Math.ceil(bytes / 1024))} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
const idFor = (file: File) => `${file.name}-${file.size}-${file.lastModified}-${crypto.randomUUID?.() ?? Math.random()}`;

const AttachmentSection = forwardRef<AttachmentSectionHandle, AttachmentSectionProps>(({ taskId, api = attachmentApi, onQueueChange, onUploadingChange, onAvailableChange }, ref) => {
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [isLoading, setIsLoading] = useState(Boolean(taskId));
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Attachment | null>(null);
  const [preview, setPreview] = useState<{ name: string; url: string; attachment?: Attachment; queueId?: string } | null>(null);
  const [existingPreviewUrls, setExistingPreviewUrls] = useState<Record<string, string>>({});
  const controllers = useRef(new Map<string, AbortController>());
  const queueRef = useRef(queue);
  const existingPreviewUrlsRef = useRef(existingPreviewUrls);
  queueRef.current = queue;
  existingPreviewUrlsRef.current = existingPreviewUrls;

  const load = useCallback(async () => {
    if (!taskId) { setIsLoading(false); return; }
    setIsLoading(true);
    const response = await api.list(taskId);
    if (response.error) setError(response.error);
    else {
      const available = response.data || [];
      setAttachments(available);
      const images = available.filter((attachment) => attachment.state === 'available' && attachment.media_type.startsWith('image/'));
      const previews = await Promise.all(images.map(async (attachment) => {
        const downloaded = await api.download(taskId, attachment.attachment_id);
        return downloaded.data ? [attachment.attachment_id, URL.createObjectURL(downloaded.data)] as const : null;
      }));
      setExistingPreviewUrls(Object.fromEntries(previews.filter(Boolean) as Array<readonly [string, string]>));
    }
    setIsLoading(false);
  }, [api, taskId]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { onQueueChange?.(queue.filter((item) => item.state !== 'available').length); }, [onQueueChange, queue]);
  useEffect(() => () => {
    controllers.current.forEach((controller) => controller.abort());
    queueRef.current.forEach((item) => item.previewUrl && URL.revokeObjectURL(item.previewUrl));
    Object.values(existingPreviewUrlsRef.current).forEach((url) => URL.revokeObjectURL(url));
  }, []);

  const addFiles = (files: File[]) => {
    const items = files.map((file) => ({
      id: idFor(file), file, state: 'queued' as const,
      previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
    }));
    queueRef.current = [...queueRef.current, ...items];
    setQueue(queueRef.current);
    setError(null);
    if (taskId) queueMicrotask(() => items.forEach((item) => void uploadOne(item.id, taskId)));
  };

  const uploadOne = async (id: string, targetTaskId: string): Promise<boolean> => {
    const item = queueRef.current.find((candidate) => candidate.id === id);
    if (!item) return true;
    const controller = new AbortController();
    controllers.current.set(id, controller);
    setQueue((current) => current.map((candidate) => candidate.id === id ? { ...candidate, state: 'uploading', error: undefined } : candidate));
    onUploadingChange?.(true);
    try {
      const initiated = await api.initiate(targetTaskId, item.file, controller.signal);
      if (!initiated.data) throw new Error(initiated.error || 'Could not start upload.');
      const finalized = await api.finalize(targetTaskId, initiated.data.attachment_id, controller.signal);
      if (!finalized.data) throw new Error(finalized.error || 'Could not finish upload.');
      setAttachments((current) => [...current.filter((attachment) => attachment.attachment_id !== finalized.data!.attachment_id), finalized.data!]);
      if (item.previewUrl) setExistingPreviewUrls((current) => ({ ...current, [finalized.data!.attachment_id]: item.previewUrl! }));
      setQueue((current) => current.filter((candidate) => candidate.id !== id));
      onAvailableChange?.();
      return true;
    } catch (reason) {
      const message = reason instanceof Error && reason.name !== 'AbortError' ? reason.message : 'Upload cancelled.';
      setQueue((current) => current.map((candidate) => candidate.id === id ? { ...candidate, state: 'failed', error: message } : candidate));
      setError(message === 'Upload failed' ? 'Upload failed. Please try again.' : message);
      return false;
    } finally {
      controllers.current.delete(id);
      if (controllers.current.size === 0) onUploadingChange?.(false);
    }
  };

  const uploadQueued = async (targetTaskId: string) => {
    const ids = queueRef.current.filter((item) => item.state === 'queued' || item.state === 'failed').map((item) => item.id);
    const results = await Promise.all(ids.map((id) => uploadOne(id, targetTaskId)));
    return results.every(Boolean);
  };

  useImperativeHandle(ref, () => ({
    uploadQueued,
    abortUploads: () => controllers.current.forEach((controller) => controller.abort()),
    hasQueuedFiles: () => queueRef.current.some((item) => item.state !== 'available'),
  }));

  const removeQueued = (item: QueueItem) => {
    controllers.current.get(item.id)?.abort();
    if (item.previewUrl) URL.revokeObjectURL(item.previewUrl);
    setQueue((current) => current.filter((candidate) => candidate.id !== item.id));
  };

  const download = async (attachment: Attachment) => {
    if (!taskId) return;
    const response = await api.download(taskId, attachment.attachment_id);
    if (!response.data) { setError(response.error || 'Download failed. Please try again.'); return; }
    const url = URL.createObjectURL(response.data);
    const link = document.createElement('a'); link.href = url; link.download = attachment.filename; link.click();
    URL.revokeObjectURL(url);
  };

  const openExistingImage = async (attachment: Attachment) => {
    if (!taskId) return;
    const response = await api.download(taskId, attachment.attachment_id);
    if (!response.data) { setError(response.error || 'Preview failed. Please try again.'); return; }
    setPreview({ name: attachment.filename, url: URL.createObjectURL(response.data), attachment });
  };

  const removeAvailable = async () => {
    if (!taskId || !deleteTarget) return;
    const response = await api.delete(taskId, deleteTarget.attachment_id);
    if (response.error) setError(response.error);
    else {
      setAttachments((current) => current.filter((item) => item.attachment_id !== deleteTarget.attachment_id));
      const previewUrl = existingPreviewUrls[deleteTarget.attachment_id];
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setExistingPreviewUrls((current) => { const next = { ...current }; delete next[deleteTarget.attachment_id]; return next; });
      onAvailableChange?.();
    }
    setDeleteTarget(null);
  };

  return (
    <section className="space-y-3" aria-label="Attachments">
      <Label htmlFor="task-attachments">Attachments</Label>
      <label htmlFor="task-attachments" className="flex min-h-24 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed p-4 text-center hover:bg-muted/40" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); addFiles(Array.from(event.dataTransfer.files)); }}>
        <Upload className="mb-2 h-5 w-5 text-muted-foreground" />
        <span className="text-sm font-medium">Drop files here or browse</span>
        <span className="mt-1 text-xs text-muted-foreground">PDF, Word, Excel, PowerPoint, text, JPEG, PNG, GIF, or WebP. Documents up to 10 MB; images are converted to WebP.</span>
        <Input id="task-attachments" aria-label="Attach a file" className="sr-only" type="file" accept={ACCEPT} multiple onChange={(event) => { addFiles(Array.from(event.target.files || [])); event.target.value = ''; }} />
      </label>
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      {isLoading && <p className="text-sm text-muted-foreground">Loading attachments…</p>}
      <div className="space-y-2">
        {!isLoading && attachments.length === 0 && queue.length === 0 && <p className="text-sm text-muted-foreground">No attachments yet.</p>}
        {queue.map((item) => (
          <div key={item.id} className="flex items-center gap-2 rounded border p-2 text-sm">
            {item.previewUrl ? <button type="button" aria-label={`Preview ${item.file.name}`} onClick={() => setPreview({ name: item.file.name, url: item.previewUrl!, queueId: item.id })}><img src={item.previewUrl} alt="" className="h-10 w-10 rounded object-cover" /></button> : <Paperclip className="h-4 w-4 text-muted-foreground" />}
            <div className="min-w-0 flex-1"><p className="truncate">{item.file.name}</p><p className={cn('text-xs text-muted-foreground', item.state === 'failed' && 'text-destructive')}>{item.error || item.state}</p></div>
            <span className="text-xs text-muted-foreground">{formatSize(item.file.size)}</span>
            {item.state === 'failed' && taskId && <Button type="button" variant="ghost" size="icon" aria-label={`Retry ${item.file.name}`} onClick={() => uploadOne(item.id, taskId)}><RotateCcw className="h-4 w-4" /></Button>}
            <Button type="button" variant="ghost" size="icon" aria-label={`Remove ${item.file.name}`} onClick={() => removeQueued(item)}><X className="h-4 w-4" /></Button>
          </div>
        ))}
        {attachments.map((attachment) => (
          <div key={attachment.attachment_id} className="flex items-center gap-2 rounded border p-2 text-sm">
            {existingPreviewUrls[attachment.attachment_id] ? <button type="button" aria-label={`Preview ${attachment.filename}`} onClick={() => setPreview({ name: attachment.filename, url: existingPreviewUrls[attachment.attachment_id], attachment })}><img src={existingPreviewUrls[attachment.attachment_id]} alt="" className="h-10 w-10 rounded object-cover" /></button> : attachment.media_type.startsWith('image/') ? <ImageIcon className="h-4 w-4 text-muted-foreground" /> : <Paperclip className="h-4 w-4 text-muted-foreground" />}
            <div className="min-w-0 flex-1"><p className="truncate">{attachment.filename}</p><p className="text-xs text-muted-foreground">{attachment.media_type.split('/').pop()} · {formatSize(attachment.byte_size)}</p></div>
            {attachment.media_type.startsWith('image/') && attachment.state === 'available' && <Button type="button" variant="ghost" size="icon" aria-label={`Preview ${attachment.filename}`} onClick={() => openExistingImage(attachment)}><Eye className="h-4 w-4" /></Button>}
            {attachment.state === 'available' ? <Button type="button" variant="ghost" size="icon" aria-label={`Download ${attachment.filename}`} onClick={() => download(attachment)}><Download className="h-4 w-4" /></Button> : <span className="text-xs text-muted-foreground">Pending upload</span>}
            <Button type="button" variant="ghost" size="icon" aria-label={`Delete ${attachment.filename}`} onClick={() => setDeleteTarget(attachment)}><Trash2 className="h-4 w-4 text-destructive" /></Button>
          </div>
        ))}
      </div>

      <AlertDialog open={Boolean(deleteTarget)} onOpenChange={(open) => !open && setDeleteTarget(null)}><AlertDialogContent><AlertDialogHeader><AlertDialogTitle>Delete Attachment?</AlertDialogTitle><AlertDialogDescription>This permanently deletes {deleteTarget?.filename}. This action cannot be undone.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel><AlertDialogAction onClick={removeAvailable} className="bg-destructive text-destructive-foreground">Delete</AlertDialogAction></AlertDialogFooter></AlertDialogContent></AlertDialog>
      <Dialog open={Boolean(preview)} onOpenChange={(open) => { if (!open && preview) { if (preview.attachment && existingPreviewUrls[preview.attachment.attachment_id] !== preview.url) URL.revokeObjectURL(preview.url); setPreview(null); } }}><DialogContent className="max-w-3xl"><DialogHeader><DialogTitle>{preview?.name}</DialogTitle></DialogHeader>{preview && <img src={preview.url} alt={preview.name} className="max-h-[70vh] w-full object-contain" />}<DialogFooter>{preview?.queueId && <Button type="button" variant="destructive" onClick={() => { const item = queue.find((candidate) => candidate.id === preview.queueId); if (item) removeQueued(item); setPreview(null); }}><Trash2 className="mr-2 h-4 w-4" />Remove</Button>}{preview?.attachment && <><Button type="button" variant="outline" onClick={() => download(preview.attachment!)}><Download className="mr-2 h-4 w-4" />Download</Button><Button type="button" variant="destructive" onClick={() => { setDeleteTarget(preview.attachment!); setPreview(null); }}><Trash2 className="mr-2 h-4 w-4" />Delete</Button></>}</DialogFooter></DialogContent></Dialog>
    </section>
  );
});

AttachmentSection.displayName = 'AttachmentSection';
export default AttachmentSection;
