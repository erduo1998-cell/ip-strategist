// Read-only Xiaohongshu owner-account adapter.
// Creator-list capture patterns are adapted from jackwener/OpenCLI (Apache-2.0).
// Comment endpoint field names were cross-checked against public implementations;
// this module deliberately uses the site's rendered, signed browser flow instead
// of embedding a reverse-engineered signer.

export const DATA_SOURCE = 'xiaohongshu_creator_center';
export const CREATOR_ROOT_URL = 'https://creator.xiaohongshu.com/statistics';
export const CREATOR_ANALYSIS_PATH = '/statistics/data-analysis?source=official';
export const PUBLIC_ROOT_URL = 'https://www.xiaohongshu.com/explore';

const NOTE_ANALYZE_PAGE_SIZE = 10;
const NOTE_ID_RE = /^[0-9a-f]{24}$/i;

export function unwrapBrowserResult(payload) {
  if (payload && typeof payload === 'object' && !Array.isArray(payload)
      && 'session' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload;
}

export function clampInt(value, fallback, min = 1, max = 100) {
  const parsed = Number.parseInt(String(value ?? ''), 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(min, Math.min(max, parsed));
}

export function asBoolean(value) {
  if (value === true || value === 1) return true;
  if (value === false || value === 0 || value == null) return false;
  const text = String(value).trim().toLowerCase();
  return ['1', 'true', 'yes'].includes(text);
}

export function firstNonEmpty(...values) {
  for (const value of values) {
    if (value == null) continue;
    const text = String(value).trim();
    if (text) return text;
  }
  return '';
}

export function firstNumber(...values) {
  for (const value of values) {
    if (value == null || value === '') continue;
    const number = Number(value);
    if (Number.isFinite(number)) return number;
  }
  return 0;
}

export function formatTimestamp(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) return '';
  return new Date(number > 10_000_000_000 ? number : number * 1000).toISOString();
}

export function assertApiSuccess(payload, label = 'xiaohongshu') {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new Error(`${label} api returned malformed data`);
  }
  const code = payload.code ?? payload.status_code ?? payload.statusCode;
  if (payload.success === false
      || (code != null && code !== '' && Number(code) !== 0 && Number(code) !== 200)) {
    const message = firstNonEmpty(payload.msg, payload.message, payload.status_msg, 'unknown');
    throw new Error(`${label} api error ${code ?? 'unknown'}: ${message}`);
  }
}

function parseCaptureMap(raw) {
  const value = unwrapBrowserResult(raw);
  if (value && typeof value === 'object' && !Array.isArray(value)) return value;
  if (typeof value !== 'string') return {};
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

function capturePageNumber(url) {
  try {
    const parsed = new URL(url, 'https://creator.xiaohongshu.com');
    const value = Number.parseInt(parsed.searchParams.get('page_num') || '', 10);
    return Number.isFinite(value) && value > 0 ? value : Number.MAX_SAFE_INTEGER;
  } catch {
    return Number.MAX_SAFE_INTEGER;
  }
}

export function harvestCreatorCaptures(captureMap) {
  const notes = [];
  const seen = new Set();
  const errors = [];
  let total = 0;
  const entries = Object.entries(captureMap || {})
    .filter(([url]) => String(url).includes('/note/analyze/list'))
    .sort(([left], [right]) => capturePageNumber(left) - capturePageNumber(right));
  for (const [url, capture] of entries) {
    if (!capture?.ok) {
      errors.push(`${url}: HTTP ${capture?.status ?? 'unknown'}`);
      continue;
    }
    try {
      const json = typeof capture.body === 'string' ? JSON.parse(capture.body) : capture.body;
      assertApiSuccess(json, 'xiaohongshu creator');
      const data = json?.data;
      if (!data || typeof data !== 'object') {
        errors.push(`${url}: malformed data`);
        continue;
      }
      total = Math.max(total, firstNumber(data.total));
      for (const note of Array.isArray(data.note_infos) ? data.note_infos : []) {
        const noteId = firstNonEmpty(note?.id, note?.note_id);
        if (!NOTE_ID_RE.test(noteId) || seen.has(noteId)) continue;
        seen.add(noteId);
        notes.push(note);
      }
    } catch (error) {
      errors.push(`${url}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  return { notes, total, errors };
}

export function normalizeCreatorNote(note, rank = 1) {
  const noteId = firstNonEmpty(note?.id, note?.note_id);
  const publishedAt = formatTimestamp(note?.post_time ?? note?.publish_time);
  return {
    data_source: DATA_SOURCE,
    rank,
    note_id: noteId,
    item_id: noteId,
    title: firstNonEmpty(note?.title, note?.display_title, '未命名笔记'),
    published_at: publishedAt,
    publish_time: publishedAt,
    views: firstNumber(note?.read_count, note?.view_count),
    impressions: firstNumber(note?.imp_count, note?.impression_count),
    likes: firstNumber(note?.like_count, note?.liked_count),
    collects: firstNumber(note?.fav_count, note?.collect_count),
    comment_count: firstNumber(note?.comment_count),
    shares: firstNumber(note?.share_count),
    rise_fans: firstNumber(note?.increase_fans_count, note?.rise_fans_count),
    average_view_time: firstNumber(note?.view_time_avg),
    signed_url_available: false,
    signed_url: '',
  };
}

async function installCreatorCapture(page) {
  await page.evaluate(`(() => {
    window.__ipXhsCreatorCapture = {};
    if (window.__ipXhsCreatorCaptureInstalled) return true;
    window.__ipXhsCreatorCaptureInstalled = true;
    const save = (url, status, ok, body) => {
      try {
        if (String(url || '').includes('/api/galaxy/')) {
          window.__ipXhsCreatorCapture[String(url)] = { status, ok, body };
        }
      } catch {}
    };
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
      const response = await originalFetch.apply(this, args);
      try {
        const url = typeof args[0] === 'string' ? args[0] : (args[0]?.url || '');
        response.clone().text().then(body => save(url, response.status, response.ok, body)).catch(() => {});
      } catch {}
      return response;
    };
    const OriginalXHR = window.XMLHttpRequest;
    function CapturedXHR() {
      const xhr = new OriginalXHR();
      const originalOpen = xhr.open;
      let url = '';
      xhr.open = function(method, nextUrl, ...rest) {
        url = String(nextUrl || '');
        return originalOpen.call(this, method, nextUrl, ...rest);
      };
      xhr.addEventListener('load', () => save(url, xhr.status, xhr.status >= 200 && xhr.status < 300, xhr.responseText));
      return xhr;
    }
    CapturedXHR.prototype = OriginalXHR.prototype;
    window.XMLHttpRequest = CapturedXHR;
    return true;
  })()`);
}

async function readCreatorCapture(page) {
  const raw = await page.evaluate('JSON.stringify(window.__ipXhsCreatorCapture || {})');
  return parseCaptureMap(raw);
}

async function pollCreatorCapture(page, previousCount = -1) {
  let harvested = { notes: [], total: 0, errors: [] };
  for (let attempt = 0; attempt < 20; attempt += 1) {
    if (typeof page.wait === 'function') await page.wait(0.5);
    const captureMap = await readCreatorCapture(page);
    harvested = harvestCreatorCaptures(captureMap);
    const hasAnalyzeCapture = Object.keys(captureMap)
      .some((url) => String(url).includes('/note/analyze/list'));
    if (previousCount < 0 ? hasAnalyzeCapture : harvested.notes.length > previousCount) return harvested;
  }
  return harvested;
}

async function assertCreatorLoggedIn(page) {
  const state = unwrapBrowserResult(await page.evaluate(`(() => {
    const text = document.body?.innerText || '';
    return {
      href: location.href,
      login: /扫码登录|验证码登录|密码登录|请先登录/.test(text) || location.pathname.startsWith('/login'),
    };
  })()`));
  if (state?.login) throw new Error('xiaohongshu creator login required');
}

export async function fetchCreatorMetricNotes(page, limit = 20) {
  const safeLimit = clampInt(limit, 20, 1, 100);
  await page.goto(CREATOR_ROOT_URL);
  if (typeof page.wait === 'function') await page.wait(1);
  await assertCreatorLoggedIn(page);
  await installCreatorCapture(page);
  await page.evaluate(`(() => {
    history.pushState({}, '', ${JSON.stringify(CREATOR_ANALYSIS_PATH)});
    window.dispatchEvent(new PopStateEvent('popstate'));
    return true;
  })()`);

  let harvested = await pollCreatorCapture(page);
  if (harvested.notes.length === 0) {
    await assertCreatorLoggedIn(page);
    const details = harvested.errors.length ? ` (${harvested.errors.join('; ')})` : '';
    throw new Error(`xiaohongshu creator notes unavailable${details}`);
  }
  const expected = harvested.total > 0 ? Math.min(harvested.total, safeLimit) : safeLimit;
  const neededPages = Math.ceil(expected / NOTE_ANALYZE_PAGE_SIZE);
  for (let pageNumber = 2; pageNumber <= neededPages && harvested.notes.length < expected; pageNumber += 1) {
    const clicked = unwrapBrowserResult(await page.evaluate(`(() => {
      const target = String(${pageNumber});
      const buttons = Array.from(document.querySelectorAll('.d-pagination-page'));
      const button = buttons.find((entry) => {
        const text = (entry.textContent || '').trim();
        return text === target || text === target + target;
      });
      if (!button) return false;
      button.click();
      return true;
    })()`));
    if (!clicked) break;
    const before = harvested.notes.length;
    harvested = await pollCreatorCapture(page, before);
    if (harvested.notes.length <= before) break;
  }
  if (harvested.total > 0 && harvested.notes.length < expected) {
    throw new Error(`xiaohongshu creator notes incomplete: ${harvested.notes.length}/${expected}`);
  }
  return harvested.notes.slice(0, safeLimit).map((note, index) => normalizeCreatorNote(note, index + 1));
}

export function extractOwnProfileNotes(snapshot, fallbackUserId = '') {
  const groups = Array.isArray(snapshot?.note_groups) ? snapshot.note_groups : [];
  const entries = [];
  for (const group of groups) {
    if (Array.isArray(group)) entries.push(...group);
    else if (group) entries.push(group);
  }
  const rows = [];
  const seen = new Set();
  for (const entry of entries) {
    const card = entry?.noteCard ?? entry?.note_card ?? entry;
    const noteId = firstNonEmpty(card?.noteId, card?.note_id, entry?.noteId, entry?.note_id, entry?.id);
    const token = firstNonEmpty(entry?.xsecToken, entry?.xsec_token, card?.xsecToken, card?.xsec_token);
    const userId = firstNonEmpty(card?.user?.userId, card?.user?.user_id, fallbackUserId);
    if (!NOTE_ID_RE.test(noteId) || !token || !userId || seen.has(noteId)) continue;
    seen.add(noteId);
    const url = new URL(`https://www.xiaohongshu.com/user/profile/${encodeURIComponent(userId)}/${noteId}`);
    url.searchParams.set('xsec_token', token);
    url.searchParams.set('xsec_source', 'pc_user');
    rows.push({ note_id: noteId, signed_url: url.toString() });
  }
  return rows;
}

async function readSelfState(page) {
  return unwrapBrowserResult(await page.evaluate(`(() => {
    const store = window.__INITIAL_STATE__?.user;
    const loggedIn = store ? (store.loggedIn?._value ?? store.loggedIn) : undefined;
    const rawInfo = store ? (store.userInfo?._value ?? store.userInfo) : {};
    return {
      login_wall: location.pathname.startsWith('/login') || loggedIn === false,
      user_id: rawInfo?.user_id || rawInfo?.userId || rawInfo?.userID || '',
    };
  })()`));
}

async function readProfileSnapshot(page) {
  return unwrapBrowserResult(await page.evaluate(`(() => {
    const clone = (value) => {
      try { return JSON.parse(JSON.stringify(value ?? null)); } catch { return null; }
    };
    const store = window.__INITIAL_STATE__?.user;
    const loggedIn = store ? (store.loggedIn?._value ?? store.loggedIn) : undefined;
    const notes = store ? (store.notes?._value ?? store.notes) : undefined;
    return {
      login_wall: location.pathname.startsWith('/login') || loggedIn === false,
      note_groups: clone(Array.isArray(notes) ? notes : []),
    };
  })()`));
}

export async function fetchOwnSignedNotes(page, options = {}) {
  const maxScrolls = clampInt(options.max_scrolls, 12, 0, 40);
  const wanted = new Set((options.note_ids || []).map(String).filter((value) => NOTE_ID_RE.test(value)));
  await page.goto(PUBLIC_ROOT_URL);
  if (typeof page.wait === 'function') await page.wait(2);
  let self = await readSelfState(page);
  if (self?.login_wall || !self?.user_id) {
    throw new Error('xiaohongshu public-site login required');
  }
  const userId = String(self.user_id);
  await page.goto(`https://www.xiaohongshu.com/user/profile/${encodeURIComponent(userId)}`);
  if (typeof page.wait === 'function') await page.wait(2);
  const found = new Map();
  let previousSize = -1;
  let stalls = 0;
  for (let round = 0; round <= maxScrolls; round += 1) {
    const snapshot = await readProfileSnapshot(page);
    if (snapshot?.login_wall) throw new Error('xiaohongshu public-site login required');
    for (const row of extractOwnProfileNotes(snapshot, userId)) found.set(row.note_id, row);
    if (wanted.size > 0 && [...wanted].every((noteId) => found.has(noteId))) break;
    if (found.size === previousSize) stalls += 1;
    else stalls = 0;
    if (stalls >= 3 || round === maxScrolls) break;
    previousSize = found.size;
    if (typeof page.autoScroll === 'function') await page.autoScroll({ times: 1, delayMs: 1200 });
    else await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
    if (typeof page.wait === 'function') await page.wait(1);
  }
  return { user_id: userId, notes: [...found.values()] };
}

export function attachSignedUrls(targets, signedNotes, includeSignedUrls = false) {
  const mapping = new Map((signedNotes || []).map((row) => [String(row.note_id), row.signed_url]));
  return (targets || []).map((target) => {
    const signedUrl = mapping.get(String(target.note_id)) || '';
    return {
      ...target,
      signed_url_available: Boolean(signedUrl),
      signed_url: includeSignedUrls ? signedUrl : '',
    };
  });
}

export async function fetchTargets(page, kwargs = {}) {
  const limit = clampInt(kwargs.limit, 20, 1, 100);
  const includeSignedUrls = asBoolean(kwargs.include_signed_urls);
  const targets = await fetchCreatorMetricNotes(page, limit);
  const profile = await fetchOwnSignedNotes(page, {
    note_ids: targets.map((target) => target.note_id),
    max_scrolls: kwargs.profile_scrolls,
  });
  return attachSignedUrls(targets, profile.notes, includeSignedUrls);
}

export function normalizeDomCommentRows(value, context = {}) {
  if (!Array.isArray(value)) throw new Error('xiaohongshu comments payload is malformed');
  const noteId = String(context.note_id || '');
  const topIdByDomKey = new Map();
  let topIndex = 0;
  for (const row of value) {
    if (!row || typeof row !== 'object' || row.is_reply) continue;
    topIndex += 1;
    const domKey = firstNonEmpty(row.comment_id, `dom-top-${topIndex}`);
    const normalized = firstNonEmpty(row.comment_id, `dom:${noteId}:top:${topIndex}`);
    topIdByDomKey.set(domKey, normalized);
  }
  return value.map((row, index) => {
    if (!row || typeof row !== 'object' || !firstNonEmpty(row.text)) {
      throw new Error(`xiaohongshu comment row ${index} is malformed`);
    }
    const isReply = Boolean(row.is_reply);
    const rawParentId = isReply ? firstNonEmpty(row.parent_comment_id) : '';
    const parentId = isReply ? firstNonEmpty(topIdByDomKey.get(rawParentId), rawParentId) : '';
    const commentId = firstNonEmpty(
      row.comment_id,
      `dom:${noteId}:${isReply ? `reply:${parentId || 'unknown'}` : 'top'}:${index + 1}`,
    );
    const rawRootId = isReply ? firstNonEmpty(row.root_comment_id, rawParentId) : '';
    const rootId = isReply
      ? firstNonEmpty(topIdByDomKey.get(rawRootId), parentId)
      : commentId;
    return {
      data_source: DATA_SOURCE,
      rank: index + 1,
      note_id: noteId,
      item_id: noteId,
      comment_id: commentId,
      comment_id_source: row.comment_id ? 'dom' : 'synthetic',
      parent_comment_id: parentId,
      root_comment_id: rootId,
      is_reply: isReply,
      reply_to: firstNonEmpty(row.reply_to),
      author: firstNonEmpty(row.author),
      text: firstNonEmpty(row.text),
      likes: firstNumber(row.likes),
      time: firstNonEmpty(row.time),
      reply_count: firstNumber(row.reply_count),
      fetched_reply_count: firstNumber(row.fetched_reply_count),
      reply_fetch_status: firstNonEmpty(row.reply_fetch_status),
      top_fetch_status: firstNonEmpty(context.top_fetch_status, 'partial'),
      expected_comment_count: firstNumber(context.expected_comment_count),
      source_url_path: `https://www.xiaohongshu.com/user/profile/*/${noteId}`,
    };
  });
}

export function buildCommentExtractionScript(options) {
  const targetCount = clampInt(options.limit, 50, 1, 200);
  const maxRounds = clampInt(options.pages, 20, 1, 60);
  const replyRounds = clampInt(options.reply_pages, 10, 1, 30);
  const withReplies = Boolean(options.with_replies);
  return `(async () => {
    const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
    const clean = el => (el?.textContent || '').replace(/\\s+/g, ' ').trim();
    const readId = el => {
      if (!el) return '';
      for (const key of ['data-comment-id', 'data-id', 'comment-id', 'id']) {
        const value = el.getAttribute?.(key);
        if (value && /^[0-9a-z:_-]{6,}$/i.test(value)) return value;
      }
      return '';
    };
    const bodyText = document.body?.innerText || '';
    const loginWall = /登录后查看|请登录|登录后才能/.test(bodyText) || location.pathname.startsWith('/login');
    const securityBlock = /安全限制|访问链接异常|当前笔记暂时无法浏览/.test(bodyText)
      || /website-login\\/error|error_code=300017|error_code=300031/.test(location.href);
    const scroller = document.querySelector('.note-scroller') || document.querySelector('.container');
    let stalls = 0;
    for (let round = 0; round < ${maxRounds}; round++) {
      const parents = document.querySelectorAll('.parent-comment');
      if (parents.length >= ${targetCount}) break;
      const before = parents.length;
      const last = parents[parents.length - 1];
      if (scroller) scroller.scrollTo(0, scroller.scrollHeight);
      last?.scrollIntoView?.({ block: 'end' });
      window.scrollTo?.(0, document.body.scrollHeight);
      await wait(850 + Math.random() * 650);
      const after = document.querySelectorAll('.parent-comment').length;
      stalls = after <= before ? stalls + 1 : 0;
      if (stalls >= 5) break;
    }
    const parents = Array.from(document.querySelectorAll('.parent-comment')).slice(0, ${targetCount});
    const results = [];
    const parseNumber = text => {
      const raw = String(text || '').replace(/[,，\\s]/g, '');
      const match = raw.match(/(\\d+(?:\\.\\d+)?)(万|w|W|千|k|K)?/);
      if (!match) return 0;
      const multiplier = /万|w/i.test(match[2] || '') ? 10000 : /千|k/i.test(match[2] || '') ? 1000 : 1;
      return Math.round(Number(match[1]) * multiplier);
    };
    const expander = el => {
      const text = clean(el);
      return text && text.length <= 30 && /(展开|更多回复|全部回复|查看.*回复|共\\d+条回复)/.test(text);
    };
    for (const [parentIndex, parent] of parents.entries()) {
      const item = parent.querySelector(':scope > .comment-item, .comment-item');
      if (!item) continue;
      const parentId = readId(item) || readId(parent) || '';
      const author = clean(item.querySelector('.author-wrapper .name, .user-name, .name'));
      const text = clean(item.querySelector('.content, .note-text'));
      if (!text) continue;
      const beforeText = clean(parent);
      const expectedMatch = beforeText.match(/(?:共|展开|查看)?\\s*(\\d+)\\s*条回复/);
      const expectedReplies = expectedMatch ? Number(expectedMatch[1]) : 0;
      if (${withReplies}) {
        const clicked = new Set();
        for (let round = 0; round < ${replyRounds}; round++) {
          const controls = Array.from(parent.querySelectorAll('button, [role="button"], span, div'))
            .filter(node => node instanceof HTMLElement && expander(node) && !clicked.has(clean(node)));
          if (!controls.length) break;
          for (const control of controls) {
            clicked.add(clean(control));
            control.click();
            await wait(250 + Math.random() * 250);
          }
        }
      }
      const subNodes = ${withReplies}
        ? Array.from(parent.querySelectorAll('.reply-container .comment-item-sub, .sub-comment-list .comment-item'))
        : [];
      const remaining = Array.from(parent.querySelectorAll('button, [role="button"], span, div')).some(expander);
      const replyStatus = !${withReplies} ? 'not_requested'
        : expectedReplies === 0 && subNodes.length === 0 ? 'no_replies'
        : !remaining && (expectedReplies === 0 || subNodes.length >= expectedReplies) ? 'complete'
        : 'partial';
      const topId = parentId || 'dom-top-' + (parentIndex + 1);
      results.push({
        comment_id: parentId,
        parent_comment_id: '',
        root_comment_id: parentId,
        author,
        text,
        likes: parseNumber(clean(item.querySelector('.count'))),
        time: clean(item.querySelector('.date, .time')),
        is_reply: false,
        reply_to: '',
        reply_count: expectedReplies,
        fetched_reply_count: subNodes.length,
        reply_fetch_status: replyStatus,
      });
      for (const sub of subNodes) {
        const content = sub.querySelector('.content, .note-text');
        const subText = clean(content);
        if (!subText) continue;
        results.push({
          comment_id: readId(sub),
          parent_comment_id: topId,
          root_comment_id: topId,
          author: clean(sub.querySelector('.author-wrapper .name, .user-name, .name')),
          text: subText,
          likes: parseNumber(clean(sub.querySelector('.count'))),
          time: clean(sub.querySelector('.date, .time')),
          is_reply: true,
          reply_to: clean(content?.querySelector(':scope > .nickname')) || author,
          reply_count: 0,
          fetched_reply_count: 0,
          reply_fetch_status: '',
        });
      }
    }
    const sectionText = clean(document.querySelector('.comments-container, .comment-list, .note-scroller'));
    const terminal = /没有更多评论|暂无更多评论|已经到底|到底了/.test(sectionText);
    return {
      login_wall: loginWall,
      security_block: securityBlock,
      top_fetch_status: terminal || parents.length >= ${targetCount} ? 'complete' : 'partial',
      results,
    };
  })()`;
}

export async function fetchComments(page, kwargs = {}) {
  const noteId = String(kwargs.note_id ?? '').trim();
  if (!NOTE_ID_RE.test(noteId)) throw new Error('valid 24-character note_id is required');
  const profile = await fetchOwnSignedNotes(page, {
    note_ids: [noteId],
    max_scrolls: kwargs.profile_scrolls,
  });
  const owned = profile.notes.find((row) => row.note_id === noteId);
  if (!owned) {
    throw new Error(`note ${noteId} was not found on the logged-in owner's profile; refusing non-owner comment access`);
  }
  await page.goto(owned.signed_url);
  if (typeof page.wait === 'function') await page.wait(2);
  const result = unwrapBrowserResult(await page.evaluate(buildCommentExtractionScript({
    limit: kwargs.limit,
    pages: kwargs.pages,
    reply_pages: kwargs.reply_pages,
    with_replies: asBoolean(kwargs.with_replies),
  })));
  if (!result || typeof result !== 'object') throw new Error('xiaohongshu comments returned malformed data');
  if (result.login_wall) throw new Error('xiaohongshu public-site login required');
  if (result.security_block) throw new Error('xiaohongshu security block; stop and retry later');
  return normalizeDomCommentRows(result.results, {
    note_id: noteId,
    top_fetch_status: result.top_fetch_status,
    expected_comment_count: kwargs.expected_comment_count,
  });
}
