import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import fs from 'fs';

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'serve-outputs-middleware',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url && req.url.startsWith('/outputs/')) {
            const relativePath = req.url.replace(/^\/outputs\//, '').split('?')[0];
            const baseDir = import.meta.dirname || process.cwd();
            const filePath = path.resolve(baseDir, '../outputs', relativePath);
            if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
              if (filePath.endsWith('.json')) {
                res.setHeader('Content-Type', 'application/json');
              } else if (filePath.endsWith('.obj')) {
                res.setHeader('Content-Type', 'text/plain');
              } else if (filePath.endsWith('.png')) {
                res.setHeader('Content-Type', 'image/png');
              }
              fs.createReadStream(filePath).pipe(res);
              return;
            }
          }
          next();
        });
      },
    },
  ],
  server: {
    fs: {
      allow: ['..'],
    },
    port: 5173,
    host: true,
  },
});
