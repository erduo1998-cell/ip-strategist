// Endpoint and field mapping adapted from yangmaoxin/social-harvest (Apache-2.0).
// This local implementation intentionally exposes only read-only creator work and comment data.

export const CREATOR_POST_URL = 'https://channels.weixin.qq.com/platform/post/list?';
export const CREATOR_COMMENT_URL = 'https://channels.weixin.qq.com/platform/interaction/comment';
export const DATA_SOURCE = 'weixin_channels_creator_helper';
const ORIGIN = 'https://channels.weixin.qq.com';
const API_BASE = '/cgi-bin/mmfinderassistant-bin';

export function cleanText(value) {
  return String(value ?? '').replace(/\s+/g, ' ').trim();
}

export function clampInt(value, fallback, min = 1, max = 100) {
  const parsed = Number.parseInt(String(value ?? ''), 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(min, Math.min(max, parsed));
}

export function asBoolean(value) {
  if (value === true || value === 1) return true;
  if (value === false || value === 0 || value === null || value === undefined) return false;
  return ['true', '1', 'yes'].includes(cleanText(value).toLowerCase());
}

export function firstNonEmpty(...values) {
  for (const value of values) {
    if (value === null || value === undefined) continue;
    const text = typeof value === 'string' ? cleanText(value) : value;
    if (text !== '') return text;
  }
  return '';
}

export function firstNumber(...values) {
  for (const value of values) {
    if (value === null || value === undefined || value === '') continue;
    const number = Number(value);
    if (Number.isFinite(number)) return number;
  }
  return 0;
}

// Browser JSON.parse loses precision for 16+ digit IDs. Quote known ID fields before parsing.
export function preserveLargeIds(text) {
  return String(text).replace(
    /("(?:objectId|finderObjectId|exportId|commentId|rootCommentId|replyCommentId|id|nonceId)"\s*:\s*)(-?\d{16,})(?=\s*[,}\]])/g,
    '$1"$2"',
  );
}

function formatTimestamp(value) {
  const raw = Number(value);
  if (!Number.isFinite(raw) || raw <= 0) return '';
  return new Date(raw > 10_000_000_000 ? raw : raw * 1000).toISOString();
}

function nextCursor(data = {}) {
  return firstNonEmpty(
    data.lastBuff, data.last_buff, data.nextLastBuff, data.next_last_buff,
    data.nextCursor, data.next_cursor, data.cursor, data.continuation,
  );
}

function hasMore(data = {}, rows = []) {
  const explicit = firstNonEmpty(data.hasMore, data.has_more, data.more, data.isContinue, data.continueFlag);
  if (explicit !== '') return asBoolean(explicit);
  return Boolean(nextCursor(data) && rows.length);
}

function assertApiSuccess(payload, apiPath) {
  const errorCode = firstNumber(payload?.errCode, payload?.errcode);
  const baseErrorCode = firstNumber(
    payload?.data?.baseResp?.errcode, payload?.data?.baseResp?.errCode,
    payload?.baseResp?.errcode, payload?.baseResp?.errCode,
  );
  if (errorCode === 0 && baseErrorCode === 0) return;
  const message = cleanText(firstNonEmpty(
    payload?.message, payload?.errmsg, payload?.errMsg,
    payload?.data?.baseResp?.errmsg, payload?.data?.baseResp?.errMsg,
    payload?.baseResp?.errmsg, payload?.baseResp?.errMsg,
  )) || 'unknown error';
  throw new Error(`weixin channels api error ${errorCode || baseErrorCode} at ${apiPath}: ${message}`);
}

async function fetchApi(page, apiPath, payload) {
  if (typeof page?.evaluate !== 'function') throw new Error('browser page is required');
  const url = `${ORIGIN}${API_BASE}${apiPath}`;
  const request = { url, payload };
  const result = await page.evaluate(`
    (async () => {
      const request = ${JSON.stringify(request)};
      const preserveLargeIds = ${preserveLargeIds.toString()};
      const bodyText = document.body?.innerText || '';
      const pageUrl = location.href || '';
      const loginBlocked = /登录|扫码登录|请先登录/.test(bodyText) && /channels\\.weixin\\.qq\\.com/.test(pageUrl);
      const response = await fetch(request.url, {
        method: 'POST', credentials: 'include',
        headers: {
          'Content-Type': 'application/json;charset=UTF-8',
          'Accept': 'application/json, text/plain, */*',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify(request.payload),
      });
      const text = await response.text();
      let data = null;
      try { data = JSON.parse(preserveLargeIds(text)); } catch {}
      return { ok: response.ok, status: response.status, loginBlocked, data };
    })()
  `);
  if (result?.loginBlocked) throw new Error('weixin channels login required');
  if (!result?.ok || !result?.data) {
    throw new Error(`weixin channels request failed at ${apiPath}: ${result?.status || 'unknown'}`);
  }
  assertApiSuccess(result.data, apiPath);
  return result.data?.data ?? result.data;
}

async function goto(page, url) {
  if (typeof page?.goto === 'function') await page.goto(url);
  if (typeof page?.wait === 'function') await page.wait({ time: 2 });
}

function normalizeWork(item = {}, index = 0) {
  const media = Array.isArray(item?.desc?.media) ? item.desc.media[0] || {} : {};
  const stats = item?.stat || item?.stats || item?.data || {};
  const publishedAt = firstNonEmpty(item.createTime, item.create_time, item.publishTime, item.publish_time, item.objectCreateTime);
  return {
    data_source: DATA_SOURCE,
    rank: index + 1,
    object_id: firstNonEmpty(item.objectId, item.finderObjectId, item.exportId, item.id),
    title: firstNonEmpty(item?.desc?.description, item?.objectDesc?.description, item.description, item.title, item.feedTitle),
    media_type: firstNonEmpty(item?.desc?.mediaType, item.mediaType, media.mediaType),
    publish_time: formatTimestamp(publishedAt),
    publish_timestamp: String(publishedAt || ''),
    view_count: firstNumber(item.readCount, item.readNum, item.browseCount, item.playCount, stats.readCount, stats.browseCount),
    like_count: firstNumber(item.likeCount, item.likeNum, stats.likeCount),
    fav_count: firstNumber(item.favCount, item.favoriteCount, item.collectCount, stats.favCount, stats.favoriteCount, stats.collectCount),
    share_count: firstNumber(item.forwardCount, item.shareCount, stats.forwardCount, stats.shareCount),
    comment_count: firstNumber(item.commentCount, item.allCommentCount, stats.commentCount),
    unread_comment_count: firstNumber(item.unreadcommentCount, item.unreadCommentCount),
  };
}

function normalizeComment(item = {}, objectId, parent = null, index = 0, pageState = {}) {
  const timestamp = firstNonEmpty(
    item.commentCreatetime, item.commentCreateTime, item.comment_create_time,
    item.createTime, item.create_time, item.commentTime, item.comment_time, item.timestamp,
  );
  const commentId = firstNonEmpty(item.commentId, item.id);
  const parentId = parent ? firstNonEmpty(parent.commentId, parent.id) : '';
  return {
    data_source: DATA_SOURCE,
    rank: index + 1,
    comment_id: commentId,
    object_id: objectId,
    parent_comment_id: parentId,
    root_comment_id: firstNonEmpty(item.rootCommentId, parentId, commentId),
    is_reply: Boolean(parent),
    author: cleanText(firstNonEmpty(item.commentNickname, item.nickname, item.author, item.username)),
    avatar_url: cleanText(firstNonEmpty(item.commentHeadurl, item.commentHeadUrl, item.headUrl, item.headurl, item.avatar, item.avatarUrl)),
    reply_to: cleanText(firstNonEmpty(item.replyNickname, item.replyToNickname, parent?.commentNickname, parent?.nickname)),
    text: cleanText(firstNonEmpty(item.content, item.commentContent, item.text, item.comment)),
    like_count: firstNumber(item.commentLikeCount, item.likeCount, item.like_count),
    reply_count: firstNumber(item.replyCount, item.reply_count, item.subCommentCount),
    time: formatTimestamp(timestamp),
    comment_timestamp: String(timestamp || ''),
    has_more: Boolean(pageState.has_more),
    next_cursor: String(pageState.next_cursor || ''),
    reply_fetch_status: parent ? '' : 'not_requested',
    fetched_reply_count: 0,
    reply_fetch_error: '',
  };
}

export async function fetchTargets(page, kwargs = {}) {
  const limit = clampInt(kwargs.limit, 20, 1, 200);
  const pages = clampInt(kwargs.pages, 1, 1, 20);
  let currentPage = clampInt(kwargs.page, 1, 1, 9999);
  await goto(page, CREATOR_POST_URL);
  const output = [];
  const seen = new Set();
  for (let index = 0; index < pages && output.length < limit; index += 1) {
    const data = await fetchApi(page, '/post/post_list', {
      currentPage, pageSize: Math.min(50, limit - output.length),
      onlyUnread: false, needAllCommentCount: true, forMcn: false,
    });
    const list = Array.isArray(data?.list) ? data.list : [];
    for (const item of list) {
      const row = normalizeWork(item, output.length);
      if (!row.object_id || seen.has(row.object_id)) continue;
      seen.add(row.object_id);
      output.push(row);
      if (output.length >= limit) break;
    }
    if (list.length < 50) break;
    currentPage += 1;
  }
  return output;
}

async function fetchReplies(page, objectId, parent, kwargs) {
  const limit = clampInt(kwargs.reply_limit, 50, 1, 200);
  const pages = clampInt(kwargs.reply_pages, 20, 1, 50);
  const parentId = firstNonEmpty(parent.commentId, parent.id);
  const output = [];
  const seen = new Set();
  let lastBuff = '';
  let complete = false;
  for (let index = 0; index < pages && output.length < limit; index += 1) {
    const data = await fetchApi(page, '/comment/comment_list', {
      exportId: objectId, rootCommentId: parentId, commentSelection: false,
      lastBuff, pageSize: Math.min(50, limit - output.length),
    });
    const list = Array.isArray(data?.comment) ? data.comment : [];
    const cursor = nextCursor(data);
    const more = hasMore(data, list);
    for (const item of list) {
      const row = normalizeComment(item, objectId, parent, output.length, { has_more: more, next_cursor: cursor });
      if (!row.comment_id || row.comment_id === parentId || seen.has(row.comment_id)) continue;
      seen.add(row.comment_id);
      output.push(row);
      if (output.length >= limit) break;
    }
    if (!more || !cursor || cursor === lastBuff) { complete = true; break; }
    lastBuff = cursor;
  }
  return { rows: output, status: complete ? 'complete' : 'partial' };
}

export async function fetchComments(page, kwargs = {}) {
  const objectId = cleanText(kwargs.object_id);
  if (!objectId) throw new Error('object_id is required');
  const limit = clampInt(kwargs.limit, 50, 1, 200);
  const pages = clampInt(kwargs.pages, 20, 1, 50);
  const withReplies = asBoolean(kwargs.with_replies ?? true);
  await goto(page, CREATOR_COMMENT_URL);
  let resolvedId = objectId;
  try {
    const detail = await fetchApi(page, '/comment/get_feed_detail', { exportId: objectId });
    resolvedId = cleanText(firstNonEmpty(detail?.object?.objectId, detail?.objectId, objectId));
  } catch (error) {
    // The list endpoint still gives a decisive authentication/API error; do not make detail mandatory.
  }
  const output = [];
  const seen = new Set();
  let lastBuff = cleanText(kwargs.cursor);
  let complete = false;
  for (let index = 0; index < pages && output.filter((row) => !row.is_reply).length < limit; index += 1) {
    const remaining = limit - output.filter((row) => !row.is_reply).length;
    const data = await fetchApi(page, '/comment/comment_list', {
      exportId: resolvedId, lastBuff, pageSize: Math.min(50, remaining), commentSelection: false, forMcn: false,
    });
    const list = Array.isArray(data?.comment) ? data.comment : [];
    const cursor = nextCursor(data);
    const more = hasMore(data, list);
    for (const item of list) {
      const row = normalizeComment(item, resolvedId, null, output.length, { has_more: more, next_cursor: cursor });
      if (!row.comment_id || seen.has(row.comment_id)) continue;
      seen.add(row.comment_id);
      output.push(row);
      if (withReplies && row.reply_count > 0) {
        try {
          const replies = await fetchReplies(page, resolvedId, item, kwargs);
          row.fetched_reply_count = replies.rows.length;
          row.reply_fetch_status = replies.status;
          output.push(...replies.rows);
        } catch (error) {
          row.reply_fetch_status = 'failed';
          row.reply_fetch_error = String(error?.message || error).slice(0, 180);
        }
      } else {
        row.reply_fetch_status = withReplies ? 'no_replies' : 'not_requested';
      }
      if (output.filter((entry) => !entry.is_reply).length >= limit) break;
    }
    if (!more || !cursor || cursor === lastBuff) { complete = true; break; }
    lastBuff = cursor;
  }
  return output.map((row, index) => ({ ...row, rank: index + 1, traversal_complete: complete }));
}
