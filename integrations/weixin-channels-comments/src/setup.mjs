#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { chmod, mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const sourceDir = path.dirname(fileURLToPath(import.meta.url));
const integrationDir = path.dirname(sourceDir);
const targetDir = path.join(os.homedir(), '.opencli', 'clis', 'weixin-channels');
const files = [['adapter.js', 'ip-strategist-comments.js'], ['core.mjs', 'ip-strategist-core.mjs']];

async function installFile(sourceName, targetName) {
  const source = path.join(sourceDir, sourceName);
  const target = path.join(targetDir, targetName);
  let payload = await readFile(source);
  if (sourceName === 'adapter.js') {
    payload = Buffer.from(payload.toString('utf8').replace("'./core.mjs'", "'./ip-strategist-core.mjs'"));
  }
  try {
    const current = await readFile(target);
    if (current.equals(payload)) return { target, changed: false };
    const backup = `${target}.bak-${new Date().toISOString().replace(/[:.]/g, '-')}`;
    await rename(target, backup);
    await writeFile(target, payload, { mode: 0o600 });
    return { target, changed: true, backup };
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
    await writeFile(target, payload, { mode: 0o600 });
    await chmod(target, 0o600);
    return { target, changed: true };
  }
}

await mkdir(targetDir, { recursive: true, mode: 0o700 });
const installed = await Promise.all(files.map(([source, target]) => installFile(source, target)));
try {
  execFileSync(path.join(integrationDir, 'node_modules', '.bin', 'opencli'), ['--help'], { stdio: 'ignore', timeout: 30_000 });
} catch {
  process.stderr.write('OpenCLI 初始化失败。请先运行 npm install，再重试 npm run setup。\n');
  process.exitCode = 1;
}
for (const item of installed) {
  process.stdout.write(`${item.changed ? '已安装' : '无需更新'}: ${item.target}\n`);
  if (item.backup) process.stdout.write(`旧文件备份: ${item.backup}\n`);
}
