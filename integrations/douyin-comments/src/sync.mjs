#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { access, mkdir, realpath } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { atomicPrivateJson, buildEvidence } from './evidence.mjs';

const integrationDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const openCli = path.join(integrationDir, 'node_modules', '.bin', 'opencli');

function parseArgs(argv) {
  const options = {
    workdir: '', profile: '', works: 10, workPages: 2,
    commentLimit: 50, commentPages: 20, replyLimit: 50, replyPages: 20,
    sampleComments: 20, withReplies: true, itemIds: [],
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const value = () => argv[++index];
    if (arg === '--workdir') options.workdir = value();
    else if (arg === '--profile') options.profile = value();
    else if (arg === '--works') options.works = Number(value());
    else if (arg === '--work-pages') options.workPages = Number(value());
    else if (arg === '--comment-limit') options.commentLimit = Number(value());
    else if (arg === '--comment-pages') options.commentPages = Number(value());
    else if (arg === '--reply-limit') options.replyLimit = Number(value());
    else if (arg === '--reply-pages') options.replyPages = Number(value());
    else if (arg === '--sample-comments') options.sampleComments = Number(value());
    else if (arg === '--item-ids') {
      options.itemIds = String(value() || '').split(',').map((item) => item.trim()).filter(Boolean);
    }
    else if (arg === '--without-replies') options.withReplies = false;
    else throw new Error(`未知参数: ${arg}`);
  }
  if (!options.workdir) throw new Error('--workdir 必填');
  return options;
}

function runOpenCli(args, profile) {
  const command = [
    ...(profile ? ['--profile', profile] : []),
    ...args,
    '-f', 'json',
  ];
  const stdout = execFileSync(openCli, command, {
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
    timeout: 12 * 60 * 1000,
    env: { ...process.env, OPENCLI_NO_UPDATE_CHECK: '1' },
  });
  const parsed = JSON.parse(stdout);
  return Array.isArray(parsed) ? parsed : [parsed];
}

function metricRowsToMap(rows) {
  const metrics = {};
  for (const row of rows) {
    const key = String(row?.metric || '').trim();
    if (!/^[a-z][a-z0-9_]*$/.test(key)) continue;
    const value = row?.value;
    if (value === null || value === undefined || value === '') continue;
    metrics[key] = String(value).trim();
  }
  return metrics;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const workdir = await realpath(options.workdir);
  await access(path.join(workdir, 'ip-dossier.md'));
  await access(openCli);

  let targets = runOpenCli([
    'douyin', 'ip-creator-comment-targets',
    '--limit', '50',
    '--pages', String(options.workPages),
  ], options.profile);
  if (options.itemIds.length > 0) {
    const wanted = new Set(options.itemIds);
    targets = targets.filter((row) => wanted.has(String(row.item_id || ''))
      || wanted.has(String(row.aweme_id || '')));
  } else {
    targets = targets.slice(0, Math.max(1, Math.min(100, options.works)));
  }

  const commentsByItem = {};
  const metricsByItem = {};
  for (const [index, target] of targets.entries()) {
    const itemId = String(target.item_id || target.aweme_id || '').trim();
    if (!itemId) continue;
    process.stderr.write(`[${index + 1}/${targets.length}] 拉取：${target.title || itemId}\n`);
    const awemeId = String(target.aweme_id || itemId);
    commentsByItem[itemId] = Number(target.comment_count || 0) > 0
      ? runOpenCli([
        'douyin', 'ip-creator-comments', itemId,
        '--aweme_id', awemeId,
        '--limit', String(options.commentLimit),
        '--pages', String(options.commentPages),
        '--with_replies', String(options.withReplies),
        '--reply_limit', String(options.replyLimit),
        '--reply_pages', String(options.replyPages),
      ], options.profile)
      : [];
    try {
      metricsByItem[itemId] = metricRowsToMap(runOpenCli([
        'douyin', 'stats', awemeId,
      ], options.profile));
    } catch {
      metricsByItem[itemId] = {};
    }
  }

  const evidence = buildEvidence(targets, commentsByItem, {
    sampleComments: options.sampleComments,
    metricsByItem,
    metricsRequested: true,
  });
  const evidenceDir = path.join(workdir, 'ip-evidence', 'douyin');
  const rawDir = path.join(evidenceDir, 'raw');
  await mkdir(rawDir, { recursive: true, mode: 0o700 });
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const rawPath = path.join(rawDir, `${stamp}.json`);
  const evidencePath = path.join(evidenceDir, 'comments-evidence.json');
  await atomicPrivateJson(rawPath, { targets, comments_by_item: commentsByItem, metrics_by_item: metricsByItem });
  await atomicPrivateJson(evidencePath, evidence);
  process.stdout.write(`${JSON.stringify({
    status: evidence.meta.status,
    works: evidence.works.length,
    top_level_comments: evidence.works.reduce((sum, work) => sum + work.fetched_top_level, 0),
    replies: evidence.works.reduce((sum, work) => sum + work.fetched_replies, 0),
    metrics_complete: evidence.works.filter((work) => work.metrics_status === 'complete').length,
    evidence_file: evidencePath,
    raw_file: rawPath,
  }, null, 2)}\n`);
}

main().catch((error) => {
  process.stderr.write(`同步失败：${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
});

export { metricRowsToMap, parseArgs, runOpenCli };
