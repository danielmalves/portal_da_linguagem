const { build } = require('esbuild');

build({
  entryPoints: ['static/src/globe.js'],
  bundle: true,
  format: 'esm',
  platform: 'browser',
  target: ['es2020'],
  outfile: 'static/js/globe.js',
  sourcemap: true,
  minify: false,
}).catch(() => process.exit(1));
