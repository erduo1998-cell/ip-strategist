// Endpoint and field mapping adapted from yangmaoxin/social-harvest (Apache-2.0).
// See ../THIRD_PARTY_NOTICES.md. This implementation is local and read-only.

export const CREATOR_COMMENT_URL =
  'https://creator.douyin.com/creator-micro/interactive/comment';
export const DATA_SOURCE = 'douyin_creator_center';

export function clampInt(value, fallback, min = 1, max = 50) {
  const parsed = Number.parseInt(String(value ?? ''), 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(min, Math.min(max, parsed));
}

export function firstNonEmpty(...values) {
  for (const value of values) {
    if (value === null || value === undefined) continue;
    const text = String(value).trim();
    if (text) return text;
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

export function asBoolean(value) {
  if (value === true || value === 1) return true;
  if (value === false || value === 0 || value === null || value === undefined) return false;
  const text = String(value).trim().toLowerCase();
  if (['1', 'true', 'yes'].includes(text)) return true;
  if (['', '0', 'false', 'no', 'null', 'undefined'].includes(text)) return false;
  return false;
}

export function preserveLargeIds(text) {
  return String(text).replace(
    /("(?:comment_id|cid|item_id|item_id_plain|aweme_id|uid|user_id|sec_uid|root_comment_id|parent_comment_id|reply_to_comment_id)"\s*:\s*)(-?\d{16,})(?=\s*[,}\]])/g,
    '$1"$2"',
  );
}

function firstArrayValue(...values) {
  for (const value of values) {
    if (Array.isArray(value) && value.length > 0) return value[0];
  }
  return '';
}

function formatTimestamp(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) return '';
  const milliseconds = number > 10_000_000_000 ? number : number * 1000;
  return new Date(milliseconds).toISOString();
}

function assertApiSuccess(data) {
  const code = data?.status_code ?? data?.statusCode;
  if (code !== null && code !== undefined && code !== '' && Number(code) !== 0) {
    const message = firstNonEmpty(data?.status_msg, data?.status_message, data?.message, 'unknown');
    throw new Error(`douyin creator api error ${code}: ${message}`);
  }
}

async function fetchPage(page, path, params = {}) {
  const request = { path, params };
  const result = await page.evaluate(`
    (async () => {
      const request = ${JSON.stringify(request)};
      const preserveLargeIds = ${preserveLargeIds.toString()};
      const parsed = new URL(request.path, window.location.origin);
      for (const [key, value] of Object.entries(request.params || {})) {
        if (value === null || value === undefined || value === '') continue;
        parsed.searchParams.set(key, String(value));
      }
      const response = await fetch(parsed.toString(), { credentials: 'include' });
      const text = await response.text();
      let data = null;
      try { data = JSON.parse(preserveLargeIds(text)); }
      catch { try { data = JSON.parse(text); } catch {} }
      return {
        ok: response.ok,
        status: response.status,
        source_url_path: parsed.origin + parsed.pathname,
        data,
      };
    })()
  `);
  if (!result?.ok || !result?.data) {
    throw new Error(`douyin creator request failed: ${result?.status || 'unknown'}`);
  }
  assertApiSuccess(result.data);
  return result;
}

function normalizeComment(comment = {}, index = 0, context = {}) {
  const user = comment.user && typeof comment.user === 'object' ? comment.user : {};
  const userInfo = comment.user_info && typeof comment.user_info === 'object'
    ? comment.user_info : {};
  const replyTo = comment.reply_to_user_info && typeof comment.reply_to_user_info === 'object'
    ? comment.reply_to_user_info : {};
  const createTime = firstNonEmpty(
    comment.create_time, comment.createTime, comment.timestamp, comment.time,
  );
  const commentId = firstNonEmpty(comment.comment_id, comment.cid, comment.id);
  const rootId = context.is_reply
    ? firstNonEmpty(context.root_comment_id, comment.root_comment_id, context.parent_comment_id, commentId)
    : firstNonEmpty(comment.root_comment_id, commentId);
  return {
    data_source: DATA_SOURCE,
    rank: index + 1,
    comment_id: commentId,
    item_id: firstNonEmpty(context.item_id, comment.item_id, comment.aweme_id),
    author: firstNonEmpty(user.nickname, user.name, userInfo.nickname, userInfo.name, comment.author),
    author_uid: firstNonEmpty(user.uid, user.user_id, userInfo.uid, userInfo.user_id, comment.uid),
    author_sec_uid: firstNonEmpty(user.sec_uid, user.secUid, userInfo.sec_uid, userInfo.secUid),
    avatar_url: firstNonEmpty(
      firstArrayValue(
        user.avatar_thumb?.url_list, user.avatar_medium?.url_list,
        userInfo.avatar_thumb?.url_list, userInfo.avatar_medium?.url_list,
      ),
      user.avatar_url,
      userInfo.avatar_url,
    ),
    text: firstNonEmpty(comment.text, comment.comment_text, comment.content),
    time: formatTimestamp(createTime),
    create_time: String(createTime || ''),
    ip_location: firstNonEmpty(comment.ip_label, comment.ip_location, comment.ipLocation),
    digg_count: firstNumber(comment.digg_count, comment.diggCount, comment.like_count),
    reply_count: firstNumber(comment.reply_count, comment.reply_comment_total, comment.replyCount),
    reply_to: firstNonEmpty(
      context.reply_to, comment.reply_to_user_name, replyTo.nickname, replyTo.name,
    ),
    reply_to_comment_id: firstNonEmpty(
      context.reply_to_comment_id, comment.reply_to_comment_id, comment.reply_id,
    ),
    parent_comment_id: firstNonEmpty(context.parent_comment_id),
    root_comment_id: rootId,
    is_reply: Boolean(context.is_reply),
    fetched_reply_count: 0,
    reply_fetch_status: context.is_reply ? '' : 'not_requested',
    reply_fetch_error: '',
    has_more: asBoolean(context.has_more),
    next_cursor: String(context.next_cursor ?? ''),
    source_url_path: String(context.source_url_path || ''),
  };
}

function normalizeList(data = {}, options = {}) {
  const comments = Array.isArray(data.comment_info_list)
    ? data.comment_info_list
    : Array.isArray(data.comments) ? data.comments : [];
  const limit = clampInt(options.limit ?? comments.length, 20);
  const context = {
    item_id: options.item_id,
    has_more: asBoolean(data.has_more ?? data.hasMore),
    next_cursor: data.cursor ?? data.next_cursor ?? data.offset ?? '',
    source_url_path: options.source_url_path || '',
    is_reply: Boolean(options.is_reply),
    parent_comment_id: options.parent_comment_id || '',
    root_comment_id: options.root_comment_id || '',
    reply_to_comment_id: options.reply_to_comment_id || '',
    reply_to: options.reply_to || '',
  };
  return comments
    .map((comment, index) => normalizeComment(comment, index, context))
    .filter((row) => row.comment_id)
    .slice(0, limit);
}

export async function fetchTargets(page, kwargs = {}) {
  const targetUrl = String(kwargs.url || CREATOR_COMMENT_URL);
  const limit = clampInt(kwargs.limit, 20);
  const pages = clampInt(kwargs.pages, 1, 1, 20);
  const waitSeconds = clampInt(kwargs.wait_seconds, 2, 1, 30);
  if (typeof page?.goto === 'function') {
    await page.goto(targetUrl);
    if (typeof page.wait === 'function') await page.wait(waitSeconds);
  }
  if (typeof page?.evaluate !== 'function') throw new Error('browser page is required');

  const rows = [];
  const seen = new Set();
  let cursor = String(kwargs.cursor ?? '0');
  for (let pageIndex = 0; pageIndex < pages; pageIndex += 1) {
    const result = await fetchPage(page, '/aweme/v1/creator/item/list', { cursor, count: limit });
    const items = Array.isArray(result.data?.item_info_list) ? result.data.item_info_list : [];
    const hasMore = asBoolean(result.data?.has_more ?? result.data?.hasMore);
    const nextCursor = String(
      result.data?.cursor ?? result.data?.next_cursor ?? result.data?.max_cursor ?? '',
    );
    for (const item of items) {
      const itemId = firstNonEmpty(item.item_id, item.id);
      const awemeId = firstNonEmpty(item.item_id_plain, item.aweme_id, itemId);
      const key = itemId || awemeId;
      if (!key || seen.has(key)) continue;
      seen.add(key);
      rows.push({
        data_source: DATA_SOURCE,
        rank: rows.length + 1,
        item_id: itemId,
        aweme_id: awemeId,
        title: firstNonEmpty(item.title, item.item_title, item.desc),
        create_time: firstNonEmpty(item.create_time),
        publish_time: formatTimestamp(item.create_time),
        comment_count: firstNumber(item.comment_count),
        has_more: hasMore,
        next_cursor: hasMore ? nextCursor : '',
      });
    }
    if (!hasMore || !nextCursor) break;
    cursor = nextCursor;
  }
  return rows;
}

export async function fetchComments(page, kwargs = {}) {
  const itemId = String(kwargs.item_id ?? '').trim();
  if (!itemId) throw new Error('item_id is required');
  const awemeId = String(kwargs.aweme_id ?? itemId).trim();
  const targetUrl = String(kwargs.url || CREATOR_COMMENT_URL);
  const limit = clampInt(kwargs.limit, 50);
  const pages = clampInt(kwargs.pages, 20, 1, 20);
  const replyLimit = clampInt(kwargs.reply_limit ?? kwargs.limit, 50);
  const replyPages = clampInt(kwargs.reply_pages, 20, 1, 20);
  const waitSeconds = clampInt(kwargs.wait_seconds, 2, 1, 30);
  const sort = String(kwargs.sort ?? '');
  const withReplies = kwargs.with_replies === true
    || String(kwargs.with_replies ?? '').toLowerCase() === 'true';
  if (typeof page?.goto === 'function') {
    await page.goto(targetUrl);
    if (typeof page.wait === 'function') await page.wait(waitSeconds);
  }
  if (typeof page?.evaluate !== 'function') throw new Error('browser page is required');

  const rows = [];
  let cursor = String(kwargs.cursor ?? '0');
  for (let pageIndex = 0; pageIndex < pages; pageIndex += 1) {
    let result = await fetchPage(page, '/aweme/v1/creator/comment/list', {
      item_id: itemId, cursor, count: limit, sort,
    });
    let pageRows = normalizeList(result.data, {
      item_id: itemId, limit, source_url_path: result.source_url_path,
    });
    if (pageRows.length === 0) {
      result = await fetchPage(
        page,
        '/web/api/third_party/aweme/api/comment/read/aweme/v1/web/comment/list/select/',
        {
          aweme_id: awemeId,
          cursor,
          count: limit,
          sort_options: firstNonEmpty(sort, 0),
          comment_select_options: '0',
          channel_id: 618,
        },
      );
      pageRows = normalizeList(result.data, {
        item_id: itemId, limit, source_url_path: result.source_url_path,
      });
    }
    rows.push(...pageRows);

    if (withReplies) {
      for (const comment of pageRows) {
        comment.reply_fetch_status = comment.reply_count > 0 ? 'failed' : 'no_replies';
        comment.reply_fetch_error = comment.reply_count > 0
          ? 'expanded_reply_request_failed' : '';
        if (comment.reply_count <= 0) continue;
        let replyCursor = '0';
        for (let replyPage = 0; replyPage < replyPages; replyPage += 1) {
          try {
            const fallback = comment.source_url_path.includes('/web/api/third_party/');
            const replyResult = await fetchPage(
              page,
              fallback
                ? '/web/api/third_party/aweme/api/comment/read/aweme/v1/web/comment/list/reply/'
                : '/aweme/v1/creator/comment/reply/list',
              fallback
                ? { comment_id: comment.comment_id, item_id: awemeId, cursor: replyCursor, count: replyLimit }
                : { comment_id: comment.comment_id, cursor: replyCursor, count: replyLimit, sort },
            );
            const replyRows = normalizeList(replyResult.data, {
              item_id: itemId,
              limit: replyLimit,
              source_url_path: replyResult.source_url_path,
              is_reply: true,
              parent_comment_id: comment.comment_id,
              root_comment_id: comment.root_comment_id || comment.comment_id,
              reply_to_comment_id: comment.comment_id,
              reply_to: comment.author,
            });
            rows.push(...replyRows);
            comment.fetched_reply_count += replyRows.length;
            comment.reply_fetch_error = '';
            const replyHasMore = asBoolean(
              replyResult.data?.has_more ?? replyResult.data?.hasMore,
            );
            replyCursor = String(
              replyResult.data?.cursor ?? replyResult.data?.next_cursor ?? '',
            );
            comment.reply_fetch_status = comment.fetched_reply_count >= comment.reply_count
              ? 'complete' : 'partial';
            if (!replyHasMore || !replyCursor) break;
          } catch (error) {
            comment.reply_fetch_status = comment.fetched_reply_count ? 'partial' : 'failed';
            comment.reply_fetch_error = error instanceof Error
              ? error.message.slice(0, 180) : 'expanded_reply_request_failed';
            break;
          }
        }
      }
    }

    const hasMore = asBoolean(result.data?.has_more ?? result.data?.hasMore);
    cursor = String(result.data?.cursor ?? result.data?.next_cursor ?? '');
    if (!hasMore || !cursor) break;
  }
  return rows;
}
