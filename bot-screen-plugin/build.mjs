import { build } from 'esbuild';
import { fileURLToPath } from 'node:url';
process.chdir(fileURLToPath(new URL('.', import.meta.url)));
await build({entryPoints:['src/plugin.mjs'],bundle:true,format:'iife',outfile:'dashboard/dist/index.js',legalComments:'eof',loader:{'.css':'text'}});
