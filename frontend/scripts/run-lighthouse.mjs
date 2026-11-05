import { spawn } from 'child_process';
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '../..');
const EVIDENCE_DIR = path.join(ROOT, 'benchmarks', 'evidence');
const REPORT_PATH = path.join(EVIDENCE_DIR, 'lighthouse_report.json');

if (!fs.existsSync(EVIDENCE_DIR)) {
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
}

async function waitForServer(url, timeoutMs = 20000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      await new Promise((resolve, reject) => {
        const req = http.get(url, (res) => {
          if (res.statusCode === 200) resolve();
          else reject(new Error(`Status ${res.statusCode}`));
        });
        req.on('error', reject);
        req.setTimeout(1000, () => {
          req.destroy();
          reject(new Error('Timeout'));
        });
      });
      return true;
    } catch {
      await new Promise((r) => setTimeout(r, 500));
    }
  }
  return false;
}

async function main() {
  console.log('Starting Vite preview server on http://127.0.0.1:4173...');
  const server = spawn('npx', ['vite', 'preview', '--port', '4173', '--host', '127.0.0.1'], {
    cwd: path.resolve(__dirname, '..'),
    shell: true,
  });

  try {
    const ready = await waitForServer('http://127.0.0.1:4173/');
    if (!ready) {
      throw new Error('Vite preview server failed to respond on http://127.0.0.1:4173/');
    }
    console.log('Preview server ready. Running Lighthouse audit...');

    // Find Chrome path if Playwright installed it
    const localAppData = process.env.LOCALAPPDATA || '';
    const playwrightDir = path.join(localAppData, 'ms-playwright');
    let chromePath = '';
    if (fs.existsSync(playwrightDir)) {
      const items = fs.readdirSync(playwrightDir);
      for (const item of items) {
        if (item.startsWith('chromium-')) {
          const candidate = path.join(playwrightDir, item, 'chrome-win64', 'chrome.exe');
          if (fs.existsSync(candidate)) {
            chromePath = candidate;
            break;
          }
        }
      }
    }

    const env = { ...process.env };
    if (chromePath) {
      env.CHROME_PATH = chromePath;
      console.log(`Using Chrome binary: ${chromePath}`);
    }

    const lighthouseArgs = [
      'lighthouse',
      'http://127.0.0.1:4173',
      '--output=json',
      `--output-path=${REPORT_PATH}`,
      '--chrome-flags="--headless=new --no-sandbox --disable-gpu"',
      '--only-categories=performance,accessibility,best-practices',
      '--preset=desktop',
      '--quiet',
    ];

    await new Promise((resolve, reject) => {
      const lh = spawn('npx', lighthouseArgs, {
        cwd: path.resolve(__dirname, '..'),
        shell: true,
        env,
        stdio: 'inherit',
      });
      lh.on('close', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`Lighthouse exited with code ${code}`));
      });
    });

    console.log(`Lighthouse audit report successfully written to ${REPORT_PATH}`);

    if (fs.existsSync(REPORT_PATH)) {
      const data = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf-8'));
      const perf = (data.categories?.performance?.score || 0) * 100;
      const a11y = (data.categories?.accessibility?.score || 0) * 100;
      const bp = (data.categories?.['best-practices']?.score || 0) * 100;
      console.log(`=== Lighthouse Scores ===`);
      console.log(`Performance:    ${perf.toFixed(1)} / 100 (Target: >= 90)`);
      console.log(`Accessibility:  ${a11y.toFixed(1)} / 100`);
      console.log(`Best Practices: ${bp.toFixed(1)} / 100`);
    }
  } finally {
    console.log('Shutting down preview server...');
    if (process.platform === 'win32') {
      spawn('taskkill', ['/F', '/T', '/PID', server.pid.toString()], { shell: true });
    } else {
      server.kill('SIGTERM');
    }
  }
}

main().catch((err) => {
  console.error('Lighthouse audit failed:', err);
  process.exit(1);
});

