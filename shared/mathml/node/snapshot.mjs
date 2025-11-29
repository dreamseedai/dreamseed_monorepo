/**
 * 골든셋 스냅샷 생성/검증
 */
import fs from 'node:fs';
import fse from 'fs-extra';
import {renderToSvgHashAndSpeech} from './render_math.mjs';

const args = process.argv.slice(2);
const mode = args.includes('--write') ? 'write' : 'check';
const writeIdx = args.indexOf('--write');
const checkIdx = args.indexOf('--check');
const file = writeIdx >= 0 ? args[writeIdx + 1] : (checkIdx >= 0 ? args[checkIdx + 1] : null);

if (!file) {
  console.error('Usage: snapshot.mjs --write|--check <jsonl>');
  process.exit(2);
}

let failures = 0;
const lines = fs.readFileSync(file, 'utf-8').split(/\r?\n/).filter(Boolean);
const out = [];

for (const line of lines) {
  const item = JSON.parse(line);
  const exp = item.expected || {};
  const inputTex = exp.tex || item.payload?.tex || null;
  const inputMml = item.payload?.mathml || null;

  const {svg_hash, speech} = renderToSvgHashAndSpeech({texString: inputTex, mathml: inputMml});

  if (mode === 'write') {
    item.expected = {...exp, svg_hash, speech};
  } else {
    if (!exp.svg_hash || exp.svg_hash !== svg_hash) {
      failures++;
      console.error(`[HASH MISMATCH] ${item.id}: expected=${exp.svg_hash||"(none)"} actual=${svg_hash}`);
    }
    if (!exp.speech || exp.speech !== speech) {
      failures++;
      console.error(`[SPEECH MISMATCH] ${item.id}`);
    }
  }
  out.push(JSON.stringify(item));
}

if (mode === 'write') {
  const backup = file.replace(/\.jsonl$/, `.bak.jsonl`);
  await fse.copy(file, backup);
  fs.writeFileSync(file, out.join('\n')+'\n', 'utf-8');
  console.log(`✅ Wrote snapshots + backup: ${backup}`);
} else {
  if (failures) {
    console.error(`\n❌ Failures: ${failures}`);
    process.exit(1);
  } else {
    console.log('✅ All snapshots OK');
  }
}
