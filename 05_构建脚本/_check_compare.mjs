// Extract <script> and check syntax
import fs from 'fs';
import { execSync } from 'child_process';
const html = fs.readFileSync('docs/compare.html', 'utf8');
const start = html.indexOf('<script type="module">');
const end = html.indexOf('</script>', start);
const code = html.substring(start + '<script type="module">'.length, end);
console.log('script length:', code.length);
const tmp = 'docs/_check_compare.mjs';
fs.writeFileSync(tmp, code);
try {
  execSync(`node --check "${tmp}"`, { stdio: 'inherit' });
  console.log('CHECK OK');
} catch (e) {
  console.log('CHECK FAILED:', e.message.split('\n').slice(0,5).join(' | '));
} finally {
  try { fs.unlinkSync(tmp); } catch {}
}
