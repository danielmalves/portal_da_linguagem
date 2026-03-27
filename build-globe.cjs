const fs = require('fs');
const path = require('path');

const source = path.join('static', 'src', 'globe.js');
const output = path.join('static', 'js', 'globe.js');
const vendorDir = path.join('static', 'vendor');
const threeSource = path.join('node_modules', 'three', 'build', 'three.module.js');
const threeCoreSource = path.join('node_modules', 'three', 'build', 'three.core.js');
const orbitSource = path.join('node_modules', 'three', 'examples', 'jsm', 'controls', 'OrbitControls.js');

function copyFile(src, dest) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
}

function copyOrbitControls() {
  const content = fs.readFileSync(orbitSource, 'utf8')
    .replace(/from 'three'/g, "from './three.module.js'")
    .replace(/from \"three\"/g, 'from "./three.module.js"');
  fs.mkdirSync(vendorDir, { recursive: true });
  fs.writeFileSync(path.join(vendorDir, 'OrbitControls.js'), content);
}

function buildAssets() {
  copyFile(source, output);
  copyFile(threeSource, path.join(vendorDir, 'three.module.js'));
  copyFile(threeCoreSource, path.join(vendorDir, 'three.core.js'));
  copyOrbitControls();
}

async function main() {
  if (process.argv.includes('--watch')) {
    buildAssets();
    fs.watchFile(source, { interval: 250 }, () => buildAssets());
    fs.watchFile(threeSource, { interval: 1000 }, () => buildAssets());
    fs.watchFile(threeCoreSource, { interval: 1000 }, () => buildAssets());
    fs.watchFile(orbitSource, { interval: 1000 }, () => buildAssets());
    return;
  }

  buildAssets();
}

main().catch(() => process.exit(1));
