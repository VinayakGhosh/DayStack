import { beforeEach, describe, expect, it, vi } from 'vitest';

import { attachmentApi } from './api';

const member = {
  member_id: 'member-1',
  email: 'member@example.com',
  display_name: 'Member',
  time_zone: 'UTC',
};

const jsonResponse = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

describe('authenticated API requests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    document.cookie = 'daystack_csrf=csrf-before; path=/';
  });

  it('refreshes an expired access token and retries the original request', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(jsonResponse(401, {
        detail: { code: 'invalid_session', message: 'Your session is invalid or has expired.' },
      }))
      .mockResolvedValueOnce(jsonResponse(200, member))
      .mockResolvedValueOnce(jsonResponse(200, []));

    const result = await attachmentApi.list('task-1');

    expect(result).toEqual({ data: [] });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[1][0]).toContain('/v1/sessions/refresh');
    expect(fetchMock.mock.calls[2][0]).toContain('/v1/tasks/task-1/attachments');
  });

  it('announces session expiry when both access and refresh tokens are invalid', async () => {
    const expiredListener = vi.fn();
    window.addEventListener('daystack:session-expired', expiredListener);
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(jsonResponse(401, {
        detail: { code: 'invalid_session', message: 'Your session is invalid or has expired.' },
      }))
      .mockResolvedValueOnce(jsonResponse(401, {
        detail: { code: 'invalid_refresh_token', message: 'A valid refresh token is required.' },
      }));

    await attachmentApi.list('task-1');

    expect(expiredListener).toHaveBeenCalledOnce();
    window.removeEventListener('daystack:session-expired', expiredListener);
  });

  it('uses one refresh for concurrent 401 responses and retries with the rotated CSRF token', async () => {
    let attachmentAttempts = 0;
    let refreshAttempts = 0;
    let finishRefresh: (() => void) | undefined;
    const refreshGate = new Promise<void>((resolve) => {
      finishRefresh = resolve;
    });
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes('/v1/sessions/refresh')) {
        refreshAttempts += 1;
        await refreshGate;
        document.cookie = 'daystack_csrf=csrf-after; path=/';
        return jsonResponse(200, member);
      }

      attachmentAttempts += 1;
      if (attachmentAttempts <= 2) {
        return jsonResponse(401, {
          detail: { code: 'invalid_session', message: 'Your session is invalid or has expired.' },
        });
      }

      expect(new Headers(init?.headers).get('X-CSRF-Token')).toBe('csrf-after');
      return jsonResponse(200, []);
    });

    const requests = Promise.all([
      attachmentApi.list('task-1'),
      attachmentApi.list('task-2'),
    ]);
    await vi.waitFor(() => expect(refreshAttempts).toBe(1));
    finishRefresh?.();

    await expect(requests).resolves.toEqual([{ data: [] }, { data: [] }]);
    expect(refreshAttempts).toBe(1);
    expect(fetchMock).toHaveBeenCalledTimes(5);
  });
});
