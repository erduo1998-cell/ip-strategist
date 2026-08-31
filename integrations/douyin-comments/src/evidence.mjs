import { chmod, mkdir, rename, writeFile } from 'node:fs/promises';
import path from 'node:path';

function safeText(value) {
  return String(value ?? '').trim();
}

function safeNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function buildEvidence(targets, commentsByItem, options = {}) {
  const fetchedAt = options.fetchedAt || new Date().toISOString();
  const sampleComments = Math.max(1, Math.min(100, safeNumber(options.sampleComments) || 20));
  const works = [];
  for (const target of targets) {
    const itemId = safeText(target.item_id || target.aweme_id);
    const rows = Array.isArray(commentsByItem[itemId]) ? commentsByItem[itemId] : [];
    const metrics = options.metricsByItem?.[itemId];
    const metricsStatus = options.metricsRequested
      ? (metrics && Object.keys(metrics).length > 0 ? 'complete' : 'failed')
      : 'not_requested';
    const top = rows.filter((row) => !row.is_reply);
    const replies = rows.filter((row) => row.is_reply);
    const lastTop = top.at(-1) || {};
    const topHasMore = lastTop.has_more === true;
    const replyIncomplete = top.some((row) =>
      !['complete', 'no_replies', 'not_requested'].includes(safeText(row.reply_fetch_status)),
    );
    const completeness = topHasMore || replyIncomplete || metricsStatus === 'failed'
      || (safeNumber(target.comment_count) > 0 && top.length === 0)
      ? 'partial' : 'complete';
    works.push({
      item_id: itemId,
      aweme_id: safeText(target.aweme_id),
      title: safeText(target.title) || '未命名作品',
      publish_time: safeText(target.publish_time),
      expected_comment_count: safeNumber(target.comment_count),
      fetched_top_level: top.length,
      fetched_replies: replies.length,
      completeness,
      metrics_status: metricsStatus,
      metrics: metricsStatus === 'complete' ? metrics : {},
      comments: rows.slice(0, sampleComments).map((row) => ({
        comment_id: safeText(row.comment_id),
        parent_comment_id: safeText(row.parent_comment_id),
        root_comment_id: safeText(row.root_comment_id),
        is_reply: Boolean(row.is_reply),
        text: safeText(row.text),
        time: safeText(row.time),
        digg_count: safeNumber(row.digg_count),
        reply_count: safeNumber(row.reply_count),
      })),
    });
  }
  const status = works.every((work) => work.completeness === 'complete')
    ? 'complete' : 'partial';
  return {
    schema_version: 1,
    meta: {
      platform: 'douyin',
      source: 'douyin_creator_center',
      fetched_at: fetchedAt,
      status,
      privacy: 'author identifiers, avatars and IP locations removed',
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
