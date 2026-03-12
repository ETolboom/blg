export class ApiError extends Error {
  constructor(public status: number, public statusText: string, public detail?: string) {
    super(`API Error: ${status} ${statusText}`);
    this.name = 'ApiError';
  }
}

export async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = await response.text().catch(() => undefined);
    if (detail) {
      try {
        const parsed = JSON.parse(detail);
        if (parsed && typeof parsed === 'object' && 'detail' in parsed) {
          detail = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
        }
      } catch (e) {
        // Not JSON, leave detail as text
      }
    }
    throw new ApiError(response.status, response.statusText, detail);
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }

  return response.text() as Promise<T>;
}

function getUrl(url: string): string {
  return url.startsWith('/') ? `/api${url}` : `/api/${url}`;
}

export async function apiGet<T>(url: string): Promise<T> {
  const response = await fetch(getUrl(url), { method: 'GET' });
  return handleResponse<T>(response);
}

export async function apiPost<T>(
  url: string,
  body?: BodyInit,
  contentType?: string
): Promise<T> {
  const headers: HeadersInit = {};
  if (contentType) {
    headers['Content-Type'] = contentType;
  }

  const response = await fetch(getUrl(url), {
    method: 'POST',
    body,
    headers,
  });

  return handleResponse<T>(response);
}

export async function apiPatch<T>(
  url: string,
  body?: BodyInit,
  contentType?: string
): Promise<T> {
  const headers: HeadersInit = {};
  if (contentType) {
    headers['Content-Type'] = contentType;
  }

  const response = await fetch(getUrl(url), {
    method: 'PATCH',
    body,
    headers,
  });

  return handleResponse<T>(response);
}

export async function apiPut<T>(
  url: string,
  body?: BodyInit,
  contentType?: string
): Promise<T> {
  const headers: HeadersInit = {};
  if (contentType) {
    headers['Content-Type'] = contentType;
  }

  const response = await fetch(getUrl(url), {
    method: 'PUT',
    body,
    headers,
  });

  return handleResponse<T>(response);
}

export async function apiDelete<T>(url: string): Promise<T> {
  const response = await fetch(getUrl(url), { method: 'DELETE' });
  return handleResponse<T>(response);
}
