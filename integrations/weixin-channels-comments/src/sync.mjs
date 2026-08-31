#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { access, mkdir, realpath } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { atomicPrivateJson, buildEvidence } from './evidence.mjs';

const integrationDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const openCli = path.join(integrationDir, 'node_modules', '.bin', 'opencli');

function parseArgs(argv) {
  const options = { workdir: '', profile: '', works: 10, workPages: 2, commentLimit: 50, commentPages: 20, replyLimit: 50, replyPages: 20, sampleComments: 20, objectIds: '' };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]; const value = () => argv[++index];
    if (arg === '--workdir') options.workdir = value();
    else if (arg === '--profile') options.profile = value();
    else if (arg === '--works') options.works = Number(value());
    else if (arg === '--work-pages') options.workPages = Number(value());
    else if (arg === '--comment-limit') options.commentLimit = Number(value());
    else if (arg === '--comment-pages') options.commentPages = Number(value());
    else if (arg === '--reply-limit') options.replyLimit = Number(value());
    else if (arg === '--reply-pages') options.replyPages = Number(value());
    else if (arg === '--sample-comments') options.sampleComments = Number(value());
    else if (arg === '--object-ids') options.objectIds = value();
    else throw new Error(`未知参数: ${arg}`);
  }
  if (!options.workdir) throw new Error('--workdir 必填');
  return options;
}

function runOpenCli(args, profile) {
  const stdout = execFileSync(openCli, [...(profile ? ['--profile', profile] : []), ...args, '-f', 'json'], {
    encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, timeout: 12 * 60 * 1000,
    env: { ...process.env, OPENCLI_NO_UPDATE_CHECK: '1' },
  });
  const parsed = JSON.parse(stdout);
  return Array.isArray(parsed) ? parsed : [parsed];
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const workdir = await realpath(options.workdir);
  await access(path.join(workdir, 'ip-dossier.md'));
  await access(openCli);
  const requested = new Set(options.objectIds.split(',').map((id) => id.trim()).filter(Boolean));
  let targets = runOpenCli(['weixin-channels', 'ip-creator-comment-targets', '--limit', '200', '--pages', String(options.workPages)], options.profile);
  if (requested.size) targets = targets.filter((target) => requested.has(String(target.object_id)));
  else targets = targets.filter((target) => Number(target.comment_count || 0) > 0).slice(0, Math.max(1, Math.min(100, options.works)));
  if (requested.size && targets.length !== requested.size) throw new Error('有签约作品未在视频号助手作品列表中找到');
  const commentsByObject = {};
  for (const [index, target] of targets.entries()) {
    const objectId = String(target.object_id || '').trim();
    if (!objectId) continue;
    process.stderr.write(`[${index + 1}/${targets.length}] 拉取视频号评论：${target.title || objectId}\n`);
    commentsByObject[objectId] = runOpenCli(['weixin-channels', 'ip-creator-comments', objectId, '--limit', String(options.commentLimit), '--pages', String(options.commentPages), '--with_replies', 'true', '--reply_limit', String(options.replyLimit), '--reply_pages', String(options.replyPages)], options.profile);
  }
  const evidence = buildEvidence(targets, commentsByObject, { sampleComments: options.sampleComments });
  const evidenceDir = path.join(workdir, 'ip-evidence', 'weixin-channels');
  const rawDir = path.join(evidenceDir, 'raw');
  await mkdir(rawDir, { recursive: true, mode: 0o700 });
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const rawPath = path.join(rawDir, `${stamp}.json`);
  const evidencePath = path.join(evidenceDir, 'comments-evidence.json');
  await atomicPrivateJson(rawPath, { targets, comments_by_object: commentsByObject });
  await atomicPrivateJson(evidencePath, evidence);
  process.stdout.write(`${JSON.stringify({ status: evidence.meta.status, works: evidence.works.length, evidence_file: evidencePath, raw_file: rawPath }, null, 2)}\n`);
}

main().catch((error) => { process.stderr.write(`同步失败：${error instanceof Error ? error.message : String(error)}\n`); process.exitCode = 1; });
export { parseArgs, runOpenCli };
