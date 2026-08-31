import { chmod, mkdir, rename, writeFile } from 'node:fs/promises';
import path from 'node:path';

function safeText(value) {
  return String(value ?? '').trim();
}

function safeNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function workCompleteness(target, rows) {
  const top = rows.filter((row) => !row.is_reply);
  const expected = safeNumber(target.comment_count);
  if (expected === 0 && rows.length === 0) return 'complete';
  const topComplete = top.length > 0 && top.every((row) => safeText(row.top_fetch_status) === 'complete');
  const repliesComplete = top.every((row) =>
    ['complete', 'no_replies', 'not_requested'].includes(safeText(row.reply_fetch_status)),
  );
  if (topComplete && repliesComplete && (expected === 0 || rows.length >= expected)) return 'complete';
  return 'partial';
}

export function buildEvidence(targets, commentsByNote, options = {}) {
  const fetchedAt = options.fetchedAt || new Date().toISOString();
  const sampleComments = Math.max(1, Math.min(100, safeNumber(options.sampleComments) || 20));
  const works = (targets || []).map((target) => {
    const noteId = safeText(target.note_id || target.item_id);
    const rows = Array.isArray(commentsByNote?.[noteId]) ? commentsByNote[noteId] : [];
    const top = rows.filter((row) => !row.is_reply);
    const replies = rows.filter((row) => row.is_reply);
    return {
      platform: 'xiaohongshu',
      note_id: noteId,
      item_id: noteId,
      title: safeText(target.title) || '未命名笔记',
      published_at: safeText(target.published_at || target.publish_time),
      metrics: {
        impressions: safeNumber(target.impressions),
        views: safeNumber(target.views),
        likes: safeNumber(target.likes),
        collects: safeNumber(target.collects),
        comments: safeNumber(target.comment_count),
        shares: safeNumber(target.shares),
        rise_fans: safeNumber(target.rise_fans),
        average_view_time: safeNumber(target.average_view_time),
      },
      fetched_top_level: top.length,
      fetched_replies: replies.length,
      completeness: workCompleteness(target, rows),
      comments: rows.slice(0, sampleComments).map((row) => ({
        comment_id: safeText(row.comment_id),
        parent_comment_id: safeText(row.parent_comment_id),
        root_comment_id: safeText(row.root_comment_id),
        is_reply: Boolean(row.is_reply),
        text: safeText(row.text),
        time: safeText(row.time),
        likes: safeNumber(row.likes),
        reply_count: safeNumber(row.reply_count),
      })),
    };
  });
  return {
    schema_version: 1,
    meta: {
      platform: 'xiaohongshu',
      source: 'xiaohongshu_creator_center_and_owner_profile',
      fetched_at: fetchedAt,
      status: works.every((work) => work.completeness === 'complete') ? 'complete' : 'partial',
      scope: 'logged-in owner account only',
      privacy: 'author identifiers, profile URLs and xsec_token removed',
    },
    works,
  };
}

export async function atomicPrivateJson(target, data) {
  const directory = path.dirname(target);
  await mkdir(directory, { recursive: true, mode: 0o700 });
  const temporary = `${target}.tmp-${process.pid}`;
  await writeFile(temporary, `${JSON.stringify(data, null, 2)}\n`, { mode: 0o600 });
  await chmod(temporary, 0o600);
  await rename(temporary, target);
}
