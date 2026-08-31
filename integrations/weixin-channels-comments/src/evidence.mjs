import { chmod, mkdir, rename, writeFile } from 'node:fs/promises';
import path from 'node:path';

const text = (value) => String(value ?? '').trim();
const number = (value) => Number.isFinite(Number(value)) ? Number(value) : 0;

export function buildEvidence(targets, commentsByObject, options = {}) {
  const sampleComments = Math.max(1, Math.min(100, number(options.sampleComments) || 20));
  const works = targets.map((target) => {
    const objectId = text(target.object_id);
    const rows = Array.isArray(commentsByObject[objectId]) ? commentsByObject[objectId] : [];
    const top = rows.filter((row) => !row.is_reply);
    const replies = rows.filter((row) => row.is_reply);
    const partial = top.some((row) => row.traversal_complete === false || !['complete', 'no_replies', 'not_requested'].includes(text(row.reply_fetch_status)))
      || (number(target.comment_count) > 0 && top.length === 0);
    return {
      platform: 'weixin-channels', item_id: objectId,
      title: text(target.title) || '未命名作品', published_at: text(target.publish_time),
      completeness: partial ? 'partial' : 'complete',
      fetched_top_level: top.length,
      fetched_replies: replies.length,
      metrics: {
        view_count: number(target.view_count), like_count: number(target.like_count),
        fav_count: number(target.fav_count), share_count: number(target.share_count),
        comment_count: number(target.comment_count), fetched_top_level: top.length, fetched_replies: replies.length,
      },
      comments: rows.slice(0, sampleComments).map((row) => ({
        comment_id: text(row.comment_id), parent_comment_id: text(row.parent_comment_id), root_comment_id: text(row.root_comment_id),
        is_reply: Boolean(row.is_reply), text: text(row.text), time: text(row.time),
        like_count: number(row.like_count), reply_count: number(row.reply_count),
      })),
    };
  });
  return {
    schema_version: 1,
    meta: {
      platform: 'weixin-channels', source: 'weixin_channels_creator_helper',
      fetched_at: options.fetchedAt || new Date().toISOString(),
      status: works.every((work) => work.completeness === 'complete') ? 'complete' : 'partial',
      privacy: 'author identifiers and avatars removed',
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
