#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { access, mkdir, realpath } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { atomicPrivateJson, buildEvidence } from './evidence.mjs';

const integrationDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const openCli = path.join(integrationDir, 'node_modules', '.bin', 'opencli');

export function parseArgs(argv) {
  const options = {
    workdir: '', profile: '', works: 10, noteIds: [], targetLimit: 50,
    commentLimit: 50, commentPages: 20, replyPages: 10,
    profileScrolls: 12, sampleComments: 20, withReplies: true,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const value = () => argv[++index];
    if (arg === '--workdir') options.workdir = value();
    else if (arg === '--profile') options.profile = value();
    else if (arg === '--works') options.works = Number(value());
    else if (arg === '--note') options.noteIds.push(String(value() || '').trim());
    else if (arg === '--target-limit') options.targetLimit = Number(value());
    else if (arg === '--comment-limit') options.commentLimit = Number(value());
    else if (arg === '--comment-pages') options.commentPages = Number(value());
    else if (arg === '--reply-pages') options.replyPages = Number(value());
    else if (arg === '--profile-scrolls') options.profileScrolls = Number(value());
    else if (arg === '--sample-comments') options.sampleComments = Number(value());
    else if (arg === '--without-replies') options.withReplies = false;
    else throw new Error(`未知参数: ${arg}`);
  }
  if (!options.workdir) throw new Error('--workdir 必填');
  for (const noteId of options.noteIds) {
    if (!/^[0-9a-f]{24}$/i.test(noteId)) throw new Error(`--note 不是有效的 24 位笔记 ID: ${noteId}`);
  }
  return options;
}

export function runOpenCli(args, profile) {
  const command = [...(profile ? ['--profile', profile] : []), ...args, '-f', 'json'];
  const stdout = execFileSync(openCli, command, {
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
    timeout: 20 * 60 * 1000,
    env: { ...process.env, OPENCLI_NO_UPDATE_CHECK: '1' },
  });
  const parsed = JSON.parse(stdout);
  return Array.isArray(parsed) ? parsed : [parsed];
}

export async function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  const workdir = await realpath(options.workdir);
  await access(path.join(workdir, 'ip-dossier.md'));
  await access(openCli);

  const allTargets = runOpenCli([
    'xiaohongshu', 'ip-creator-comment-targets',
    '--limit', String(options.targetLimit),
    '--profile_scrolls', String(options.profileScrolls),
    '--include_signed_urls', 'false',
  ], options.profile);
  const wanted = new Set(options.noteIds);
  let targets = wanted.size > 0
    ? allTargets.filter((target) => wanted.has(String(target.note_id || target.item_id)))
    : allTargets.filter((target) => Number(target.comment_count || 0) > 0)
      .slice(0, Math.max(1, Math.min(100, options.works)));
  if (wanted.size > 0) {
    const found = new Set(targets.map((target) => String(target.note_id || target.item_id)));
    const missing = [...wanted].filter((noteId) => !found.has(noteId));
    if (missing.length) throw new Error(`指定笔记不在本人创作者列表中: ${missing.join(', ')}`);
  }

  const commentsByNote = {};
  for (const [index, target] of targets.entries()) {
    const noteId = String(target.note_id || target.item_id || '').trim();
    if (!noteId) continue;
    process.stderr.write(`[${index + 1}/${targets.length}] 拉取本人笔记评论：${target.title || noteId}\n`);
    commentsByNote[noteId] = runOpenCli([
      'xiaohongshu', 'ip-creator-comments', noteId,
      '--expected_comment_count', String(target.comment_count || 0),
      '--limit', String(options.commentLimit),
      '--pages', String(options.commentPages),
      '--with_replies', String(options.withReplies),
      '--reply_pages', String(options.replyPages),
      '--profile_scrolls', String(options.profileScrolls),
    ], options.profile);
  }

  const evidence = buildEvidence(targets, commentsByNote, { sampleComments: options.sampleComments });
  const evidenceDir = path.join(workdir, 'ip-evidence', 'xiaohongshu');
  const rawDir = path.join(evidenceDir, 'raw');
  await mkdir(rawDir, { recursive: true, mode: 0o700 });
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const rawPath = path.join(rawDir, `${stamp}.json`);
  const evidencePath = path.join(evidenceDir, 'comments-evidence.json');
  await atomicPrivateJson(rawPath, { targets, comments_by_note: commentsByNote });
  await atomicPrivateJson(evidencePath, evidence);
  process.stdout.write(`${JSON.stringify({
    status: evidence.meta.status,
    works: evidence.works.length,
    top_level_comments: evidence.works.reduce((sum, work) => sum + work.fetched_top_level, 0),
    replies: evidence.works.reduce((sum, work) => sum + work.fetched_replies, 0),
    evidence_file: evidencePath,
    raw_file: rawPath,
  }, null, 2)}\n`);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    process.stderr.write(`同步失败：${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  });
}
