export async function api<T = any>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try { response = await fetch(`/api/v1${path}`, { ...init, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', ...init?.headers } }); }
  catch { throw new Error('Cannot reach the server. Keep START_WINDOWS.cmd running and open http://localhost:5173.'); }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = Array.isArray(body.detail) ? body.detail.map((e:any)=>`${e.loc?.slice(1).join(' ')}: ${e.msg}`).join('; ') : body.detail;
    throw new Error(response.status >= 500 ? 'Server unavailable. Restart with START_WINDOWS.cmd to migrate and seed the database. See the server terminal for details.' : detail || `Request failed (${response.status})`);
  }
  return response.status === 204 ? undefined as T : response.json();
}
export const post = (path: string, body: unknown = {}) => api(path, { method: 'POST', body: JSON.stringify(body) });
export const patch = (path: string, body: unknown) => api(path, { method: 'PATCH', body: JSON.stringify(body) });
