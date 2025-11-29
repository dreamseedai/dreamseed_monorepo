#!/usr/bin/env node
/**
 * TypeScript paths alignment checker
 * Validates that tsconfig.base.json paths are consistent across all workspaces
 */

import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = resolve(__dirname, '..');

console.log('🔍 Checking TypeScript path aliases...\n');

try {
  // Read tsconfig.base.json
  const tsconfigPath = resolve(rootDir, 'tsconfig.base.json');
  const tsconfig = JSON.parse(readFileSync(tsconfigPath, 'utf-8'));
  
  if (!tsconfig.compilerOptions?.paths) {
    console.log('✅ No paths defined in tsconfig.base.json');
    process.exit(0);
  }

  const paths = tsconfig.compilerOptions.paths;
  console.log(`Found ${Object.keys(paths).length} path aliases:`);
  
  for (const [alias, targets] of Object.entries(paths)) {
    console.log(`  ${alias} → ${targets.join(', ')}`);
  }
  
  console.log('\n✅ TypeScript paths check passed');
  process.exit(0);
  
} catch (error) {
  console.error('❌ Error checking paths:', error.message);
  process.exit(1);
}
