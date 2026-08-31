import assert from 'node:assert/strict';
import test from 'node:test';
import { buildEvidence } from '../src/evidence.mjs';

test('evidence preserves analysis fields while removing commenter identity', () => {
  const evidence = buildEvidence([{ object_id: 'work-1', title: '测试作品', comment_count: 2, view_count: 10 }], {
    'work-1': [{ comment_id: 'comment-1', text: '请讲这个话题', author: '私密昵称', avatar_url: 'https://private.example/avatar', is_reply: false, reply_fetch_status: 'complete', traversal_complete: true }],
  }, { fetchedAt: '2026-08-31T00:00:00Z' });
  assert.equal(evidence.works[0].metrics.view_count, 10);
  assert.equal(evidence.works[0].comments[0].text, '请讲这个话题');
  assert.equal(evidence.works[0].completeness, 'complete');
  assert.equal(JSON.stringify(evidence).includes('私密昵称'), false);
  assert.equal(JSON.stringify(evidence).includes('private.example'), false);
});
