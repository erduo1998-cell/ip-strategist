#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { chmod, mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const sourceDir = path.dirname(fileURLToPath(import.meta.url));
const integrationDir = path.dirname(sourceDir);
const openCliDir = path.join(os.homedir(), '.opencli');
const targetDir = path.join(openCliDir, 'clis', 'douyin');
const files = [
  ['adapter.js', 'ip-strategist-comments.js'],
  ['core.mjs', 'ip-strategist-core.mjs'],
];

async function installFile(sourceName, targetName) {
  const source = path.join(sourceDir, sourceName);
  const target = path.join(targetDir, targetName);
  let payload = await readFile(source);
  if (sourceName === 'adapter.js') {
    payload = Buffer.from(
      payload.toString('utf8').replace("'./core.mjs'", "'./ip-strategist-core.mjs'"),
      'utf8',
    );
  }
  try {
    const current = await readFile(target);
    if (current.equals(payload)) return { target, changed: false, backup: '' };
    const backup = `${target}.bak-${new Date().toISOString().replace(/[:.]/g, '-')}`;
    await rename(target, backup);
    await writeFile(target, payload, { mode: 0o600 });
    return { target, changed: true, backup };
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
    await writeFile(target, payload, { mode: 0o600 });
    await chmod(target, 0o600);
    return { target, changed: true, backup: '' };
  }
}

await mkdir(targetDir, { recursive: true, mode: 0o700 });
const installed = [];
for (const [sourceName, targetName] of files) {
  installed.push(await installFile(sourceName, targetName));
}

const openCli = path.join(integrationDir, 'node_modules', '.bin', 'opencli');
try {
  execFileSync(openCli, ['--help'], { stdio: 'ignore', timeout: 30_000 });
} catch (error) {
  process.stderr.write('OpenCLI 初始化失败。请先运行 npm install，再重试 npm run setup。\n');
  process.exitCode = error?.status || 1;
}

for (const item of installed) {
  const action = item.changed ? '已安装' : '无需更新';
  process.stdout.write(`${action}: ${item.target}\n`);
  if (item.backup) process.stdout.write(`旧文件备份: ${item.backup}\n`);
}
process.stdout.write('下一步：安装并启用 OpenCLI Browser Bridge 扩展，然后运行 opencli profile list。\n');
