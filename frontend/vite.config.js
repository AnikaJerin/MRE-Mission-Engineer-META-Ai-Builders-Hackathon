import { defineConfig } from 'vite';
import {isAllowedMutation} from './proxy-policy.js';

// Local development only. The browser never receives MODEL_API_KEY.
const target = 'http://127.0.0.1:8769';
const proxy = {
  target, changeOrigin: true,
  configure(server) {
    server.on('proxyReq', (proxyReq, req) => {
      // Only the preceding same-origin middleware may forward a mutation.
      if (req.method === 'POST') proxyReq.setHeader('Origin', target);
    });
  },
};
export default defineConfig({
  plugins: [{
    name: 'mre-local-mutation-origin',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (req.url?.startsWith('/api/') && req.method !== 'GET' && req.method !== 'HEAD') {
          if (!isAllowedMutation(req)) {
            res.writeHead(403, {'Content-Type': 'application/json'});
            res.end(JSON.stringify({error: 'Use the local MRE UI at http://127.0.0.1:5173'}));
            return;
          }
        }
        next();
      });
    },
  }],
  server: {
    host: '127.0.0.1', port: 5173, strictPort: true,
    proxy: {'/api/': proxy, '/validation': {target, changeOrigin: true}},
  },
  build: {outDir: 'dist'},
});
