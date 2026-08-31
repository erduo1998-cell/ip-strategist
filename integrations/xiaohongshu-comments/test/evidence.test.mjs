import assert from 'node:assert/strict';
import { mkdtemp, readFile, stat } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { atomicPrivateJson, buildEvidence } from '../src/evidence.mjs';

const target = {
  note_id: '68aabbcc0000000011223344',
  title: '测试笔记',
  published_at: '2026-08-30T10:00:00.000Z',
  impressions: 100,
  views: 50,
  likes: 8,
  collects: 3,
  comment_count: 2,
  shares: 1,
};

test('evidence strips author identity and xsec token while retaining comment text', () => {
  const evidence = buildEvidence([target], {
    [target.note_id]: [
      {
        comment_id: 'root-1', text: '一级正文', author: '敏感昵称', is_reply: false,
        top_fetch_status: 'complete', reply_fetch_status: 'complete', reply_count: 1,
      },
      {
        comment_id: 'reply-1', parent_comment_id: 'root-1', root_comment_id: 'root-1',
        text: '二级正文', author: '另一个昵称', is_reply: true, reply_to: '敏感昵称',
      },
    ],
  }, { fetchedAt: '2026-08-31T00:00:00.000Z' });
  assert.equal(evidence.meta.status, 'complete');
  assert.equal(evidence.works[0].comments[1].text, '二级正文');
  assert.equal(evidence.works[0].fetched_replies, 1);
  assert.equal('author' in evidence.works[0].comments[0], false);
  assert.equal(JSON.stringify(evidence).includes('敏感昵称'), false);
  assert.equal(JSON.stringify(evidence).includes('secret-token-value'), false);
  assert.equal(evidence.meta.privacy, 'author identifiers, profile URLs and xsec_token removed');
});

test('incomplete reply expansion stays explicitly partial', () => {
  const evidence = buildEvidence([target], {
    [target.note_id]: [{
      comment_id: 'root-1', text: '正文', is_reply: false,
      top_fetch_status: 'complete', reply_fetch_status: 'partial', reply_count: 2,
    }],
  });
  assert.equal(evidence.meta.status, 'partial');
  assert.equal(evidence.works[0].completeness, 'partial');
});

test('private JSON writer creates mode-600 evidence', async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'ip-xhs-'));
  const targetPath = path.join(directory, 'private', 'evidence.json');
  await atomicPrivateJson(targetPath, { ok: true });
  assert.deepEqual(JSON.parse(await readFile(targetPath, 'utf8')), { ok: true });
  assert.equal((await stat(targetPath)).mode & 0o777, 0o600);
});
