import { config } from 'dotenv';
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { serve } from '@hono/node-server';
import { serveStatic } from '@hono/node-server/serve-static';
import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';
import { voices } from './routes.js';

// Load .env from project root
config({ path: resolve(import.meta.dirname, '../../.env') });

const app = new Hono();

app.use('*', cors());
app.use('*', logger());

// API routes
app.route('/api', voices);

// Static frontend (after build)
const staticRoot = resolve(import.meta.dirname, '../../frontend/dist');
if (existsSync(staticRoot)) {
  app.use('/assets/*', serveStatic({ root: staticRoot }));
  const indexHtml = readFileSync(resolve(staticRoot, 'index.html'), 'utf-8');
  app.notFound((c) => {
    const accept = c.req.header('accept') || '';
    if (c.req.method === 'GET' && accept.includes('text/html')) {
      return c.html(indexHtml);
    }
    return c.json({ error: 'Not found' }, 404);
  });
}

const port = Number(process.env.PORT) || 8000;
console.log(`Server running on http://localhost:${port}`);
serve({ fetch: app.fetch, port });
