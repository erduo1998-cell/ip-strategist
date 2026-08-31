import test from 'node:test';
import assert from 'node:assert/strict';
import { asBoolean, fetchComments, firstNumber, preserveLargeIds } from '../src/core.mjs';

function fakePage(mode = 'normal') {
  return {
    async goto() {},
    async wait() {},
    async evaluate(code) {
      const oldWindow = globalThis.window;
      const oldFetch = globalThis.fetch;
      globalThis.window = { location: { origin: 'https://creator.douyin.com' } };
      globalThis.fetch = async (url) => {
        const pathname = new URL(url).pathname;
        let body = '{"comment_info_list":[]}';
        if (pathname === '/aweme/v1/creator/comment/list') {
          body = mode === 'api-error'
            ? '{"status_code":10008,"status_msg":"login expired"}'
            : '{"has_more":"0","cursor":"","comment_info_list":[{"comment_id":1234567890123456789,"text":"正文A","reply_count":null,"reply_comment_total":1,"digg_count":null,"like_count":9,"user":{"nickname":"用户A","uid":998877665544332211}}]}';
        } else if (pathname === '/aweme/v1/creator/comment/reply/list') {
          body = '{"has_more":false,"cursor":"","comment_info_list":[{"comment_id":2234567890123456789,"text":"二级回复A"}]}';
        }
        return { ok: true, status: 200, async text() { return body; } };
      };
      try { return await eval(code); }
      finally { globalThis.window = oldWindow; globalThis.fetch = oldFetch; }
    },
  };
}

test('numeric fallback and boolean parsing do not swallow valid values', () => {
  assert.equal(firstNumber(null, '', 9), 9);
  assert.equal(asBoolean('0'), false);
  assert.equal(asBoolean('1'), true);
});

test('large ids are preserved as strings', () => {
  const parsed = JSON.parse(preserveLargeIds('{"comment_id":1234567890123456789}'));
  assert.equal(parsed.comment_id, '1234567890123456789');
});

test('fetches comment body and second-level reply with stable hierarchy', async () => {
  const rows = await fetchComments(fakePage(), {
    item_id: '7777777777777777777',
    aweme_id: '7777777777777777777',
    with_replies: true,
    pages: 1,
    reply_pages: 1,
    wait_seconds: 1,
  });
  assert.deepEqual(rows.map((row) => row.text), ['正文A', '二级回复A']);
  assert.equal(rows[0].digg_count, 9);
  assert.equal(rows[0].reply_count, 1);
  assert.equal(rows[0].has_more, false);
  assert.equal(rows[0].reply_fetch_status, 'complete');
  assert.equal(rows[1].root_comment_id, rows[0].comment_id);
});

test('application-level login error is not normalized as empty comments', async () => {
  await assert.rejects(
    fetchComments(fakePage('api-error'), {
      item_id: '7', pages: 1, wait_seconds: 1,
    }),
    /api error 10008: login expired/,
  );
});
