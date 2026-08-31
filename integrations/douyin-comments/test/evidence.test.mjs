import test from 'node:test';
import assert from 'node:assert/strict';
import { buildEvidence } from '../src/evidence.mjs';

test('evidence strips identities and reports partial traversal', () => {
  const targets = [{
    item_id: '7', title: '测试作品', comment_count: 10,
  }];
  const evidence = buildEvidence(targets, {
    7: [{
      comment_id: '1', text: '正文', author: '真实昵称', author_uid: 'secret',
      avatar_url: 'https://example.test/avatar', ip_location: '北京',
      is_reply: false, digg_count: 3, reply_count: 2,
      reply_fetch_status: 'partial', has_more: true,
    }],
  }, { fetchedAt: '2026-08-31T00:00:00Z' });
  const serialized = JSON.stringify(evidence);
  assert.equal(evidence.meta.status, 'partial');
  assert.equal(evidence.works[0].completeness, 'partial');
  assert.equal(serialized.includes('真实昵称'), false);
  assert.equal(serialized.includes('secret'), false);
  assert.equal(serialized.includes('北京'), false);
  assert.equal(evidence.works[0].comments[0].text, '正文');
});

test('evidence keeps deep work metrics and does not invent missing values', () => {
  const evidence = buildEvidence([
    { item_id: '7', aweme_id: '8', title: '测试作品', comment_count: 0 },
  ], { 7: [] }, {
    fetchedAt: '2026-08-31T00:00:00Z',
    metricsRequested: true,
    metricsByItem: {
      7: { view_count: '123', completion_rate: '45.6%' },
    },
  });
  assert.equal(evidence.meta.status, 'complete');
  assert.equal(evidence.works[0].metrics_status, 'complete');
  assert.deepEqual(evidence.works[0].metrics, {
    view_count: '123', completion_rate: '45.6%',
  });
  assert.equal('share_count' in evidence.works[0].metrics, false);
});

test('requested but unavailable work metrics mark evidence partial', () => {
  const evidence = buildEvidence([
    { item_id: '7', title: '测试作品', comment_count: 0 },
  ], { 7: [] }, { metricsRequested: true, metricsByItem: {} });
  assert.equal(evidence.meta.status, 'partial');
  assert.equal(evidence.works[0].metrics_status, 'failed');
  assert.deepEqual(evidence.works[0].metrics, {});
});
