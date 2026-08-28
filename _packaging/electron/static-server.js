// Malutki statyczny serwer HTTP na 127.0.0.1 (efemeryczny port) dla bundla atlasu.
// Atlas uzywa fetch() + ES modules -> potrzebuje originu http(s), nie file://.
// Zero zaleznosci.
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.glb': 'model/gltf-binary',
  '.wasm': 'application/wasm',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.bin': 'application/octet-stream',
};

function startStaticServer(root) {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      try {
        const urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
        let rel = urlPath === '/' ? '/index.html' : urlPath;
        // zabezpieczenie przed wyjsciem poza root
        const full = path.join(root, path.normalize(rel).replace(/^(\.\.[/\\])+/, ''));
        if (!full.startsWith(root)) { res.writeHead(403); return res.end('forbidden'); }

        fs.stat(full, (err, st) => {
          let target = full;
          if (err || st.isDirectory()) {
            target = path.join(full, 'index.html');
          }
          fs.stat(target, (err2, st2) => {
            if (err2 || !st2.isFile()) { res.writeHead(404); return res.end('not found'); }
            const ext = path.extname(target).toLowerCase();
            const type = MIME[ext] || 'application/octet-stream';
            const range = req.headers.range;
            if (range) {
              const m = /bytes=(\d*)-(\d*)/.exec(range);
              let start = m && m[1] ? parseInt(m[1], 10) : 0;
              let end = m && m[2] ? parseInt(m[2], 10) : st2.size - 1;
              if (isNaN(start) || start < 0) start = 0;
              if (isNaN(end) || end >= st2.size) end = st2.size - 1;
              res.writeHead(206, {
                'Content-Type': type,
                'Content-Range': `bytes ${start}-${end}/${st2.size}`,
                'Accept-Ranges': 'bytes',
                'Content-Length': end - start + 1,
              });
              fs.createReadStream(target, { start, end }).pipe(res);
            } else {
              res.writeHead(200, { 'Content-Type': type, 'Content-Length': st2.size, 'Accept-Ranges': 'bytes' });
              fs.createReadStream(target).pipe(res);
            }
          });
        });
      } catch (e) {
        res.writeHead(500); res.end('error');
      }
    });
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve({ server, port, origin: `http://127.0.0.1:${port}` });
    });
  });
}

module.exports = { startStaticServer };
