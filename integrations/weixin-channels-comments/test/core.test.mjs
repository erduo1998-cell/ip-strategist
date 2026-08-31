import assert from 'node:assert/strict';
import test from 'node:test';
import { asBoolean, fetchComments, fetchTargets, firstNumber, preserveLargeIds } from '../src/core.mjs';

function fakePage(mode = 'normal') {
  return {
    async goto() {}, async wait() {},
    async evaluate(code) {
      const original = { document: globalThis.document, location: globalThis.location, fetch: globalThis.fetch };
      globalThis.document = { body: { innerText: '' } };
      globalThis.location = { href: 'https://channels.weixin.qq.com/platform/interaction/comment' };
      globalThis.fetch = async (url, init) => {
        const apiPath = new URL(url).pathname.replace('/cgi-bin/mmfinderassistant-bin', '');
        const request = JSON.parse(init.body);
        let body = '{"errCode":0,"data":{}}';
        if (mode === 'api-error') body = '{"errCode":1001,"errmsg":"login expired"}';
        else if (apiPath === '/post/post_list') body = '{"errCode":0,"data":{"list":[{"objectId":1234567890123456789,"desc":{"description":"作品 A"},"createTime":1700000000,"readCount":9,"likeCount":2,"commentCount":1}]}}';
        else if (apiPath === '/comment/get_feed_detail') body = '{"errCode":0,"data":{"object":{"objectId":1234567890123456789}}}';
        else if (apiPath === '/comment/comment_list' && request.rootCommentId) body = '{"errCode":0,"data":{"hasMore":false,"comment":[{"commentId":2234567890123456789,"content":"二级回复","commentCreatetime":1700000001}]}}';
        else if (apiPath === '/comment/comment_list') body = '{"errCode":0,"data":{"hasMore":false,"comment":[{"commentId":1234567890123456788,"content":"一级正文","replyCount":1,"commentCreatetime":1700000000}]}}';
        return { ok: true, status: 200, async text() { return body; } };
      };
      try { return await eval(code); }
      finally { globalThis.document = original.document; globalThis.location = original.location; globalThis.fetch = original.fetch; }
    },
  };
}

test('numeric and boolean coercion preserve valid fallbacks', () => {
  assert.equal(firstNumber(null, '', 7), 7);
  assert.equal(asBoolean('false'), false);
  assert.equal(asBoolean('1'), true);
});

test('large Weixin IDs remain strings', () => {
  const parsed = JSON.parse(preserveLargeIds('{"objectId":1234567890123456789,"commentId":2234567890123456789}'));
  assert.equal(parsed.objectId, '1234567890123456789');
  assert.equal(parsed.commentId, '2234567890123456789');
});

test('fetches own work metrics plus comment body and nested reply', async () => {
  const targets = await fetchTargets(fakePage(), { limit: 5, pages: 1 });
  assert.equal(targets[0].object_id, '1234567890123456789');
  assert.equal(targets[0].comment_count, 1);
  const rows = await fetchComments(fakePage(), { object_id: targets[0].object_id, with_replies: true, pages: 1, reply_pages: 1 });
  assert.deepEqual(rows.map((row) => row.text), ['一级正文', '二级回复']);
  assert.equal(rows[1].parent_comment_id, rows[0].comment_id);
  assert.equal(rows[1].root_comment_id, rows[0].comment_id);
  assert.equal(rows[0].reply_fetch_status, 'complete');
});

test('application errors are never normalized as empty results', async () => {
  await assert.rejects(fetchTargets(fakePage('api-error'), { limit: 1 }), /api error 1001.*login expired/);
});
