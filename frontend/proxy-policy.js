export function isAllowedMutation(req) {
  return req.method === 'POST' && req.headers.origin === 'http://127.0.0.1:5173' && req.headers.host === '127.0.0.1:5173';
}
