import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import {
  assertApiSuccess,
  attachSignedUrls,
  buildCommentExtractionScript,
  extractOwnProfileNotes,
  fetchCreatorMetricNotes,
  harvestCreatorCaptures,
  normalizeCreatorNote,
  normalizeDomCommentRows,
} from '../src/core.mjs';

const fixtures = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures');
async function fixture(name) {
  return JSON.parse(await readFile(path.join(fixtures, name), 'utf8'));
}

test('creator capture keeps stable IDs and all review metrics', async () => {
  const payload = await fixture('creator-notes.json');
  const result = harvestCreatorCaptures({
    '/api/galaxy/creator/datacenter/note/analyze/list?page_num=1': {
      ok: true, status: 200, body: JSON.stringify(payload),
    },
  });
  assert.equal(result.total, 1);
  assert.equal(result.notes.length, 1);
  const row = normalizeCreatorNote(result.notes[0]);
  assert.equal(row.note_id, '68aabbcc0000000011223344');
  assert.equal(row.impressions, 3600);
  assert.equal(row.views, 1200);
  assert.equal(row.comment_count, 3);
  assert.equal(row.shares, 11);
  assert.equal(row.average_view_time, 18.5);
});

test('application-level failures are rejected instead of reported as empty success', () => {
  assert.throws(
    () => assertApiSuccess({ success: false, code: -100, msg: '登录失效' }, 'xhs'),
    /登录失效/,
  );
});

test('all creator-page evaluate snippets are syntactically valid JavaScript', async () => {
  const payload = await fixture('creator-notes.json');
  const capture = JSON.stringify({
    '/api/galaxy/creator/datacenter/note/analyze/list?page_num=1': {
      ok: true, status: 200, body: JSON.stringify(payload),
    },
  });
  const page = {
    goto: async () => {},
    wait: async () => {},
    evaluate: async (script) => {
      assert.doesNotThrow(() => new Function(`return (${script});`));
      if (script.includes('document.body?.innerText')) return { login: false };
      if (script.includes('JSON.stringify(window.__ipXhsCreatorCapture')) return capture;
      return true;
    },
  };
  const rows = await fetchCreatorMetricNotes(page, 1);
  assert.equal(rows.length, 1);
});

test('creator capture polling does not treat an empty pre-response map as success', async () => {
  const payload = await fixture('creator-notes.json');
  const capture = JSON.stringify({
    '/api/galaxy/creator/datacenter/note/analyze/list?page_num=1': {
      ok: true, status: 200, body: JSON.stringify(payload),
    },
  });
  let captureReads = 0;
  const page = {
    goto: async () => {},
    wait: async () => {},
    evaluate: async (script) => {
      if (script.includes('document.body?.innerText')) return { login: false };
      if (script.includes('JSON.stringify(window.__ipXhsCreatorCapture')) {
        captureReads += 1;
        return captureReads === 1 ? '{}' : capture;
      }
      return true;
    },
  };
  const rows = await fetchCreatorMetricNotes(page, 1);
  assert.equal(rows.length, 1);
  assert.equal(captureReads, 2);
});

test('comment DOM extraction snippet compiles before browser use', () => {
  const script = buildCommentExtractionScript({
    limit: 20, pages: 10, reply_pages: 10, with_replies: true,
  });
  assert.doesNotThrow(() => new Function(`return (${script});`));
});

test('only signed notes from the current owner profile are resolved', () => {
  const rows = extractOwnProfileNotes({
    note_groups: [[{
      noteCard: {
        noteId: '68aabbcc0000000011223344',
        user: { userId: 'owner-user-id' },
      },
      xsecToken: 'owner-token',
    }]],
  }, 'owner-user-id');
  assert.equal(rows.length, 1);
  assert.match(rows[0].signed_url, /xsec_token=owner-token/);

  const hidden = attachSignedUrls([
    { note_id: '68aabbcc0000000011223344' },
  ], rows, false);
  assert.equal(hidden[0].signed_url_available, true);
  assert.equal(hidden[0].signed_url, '');
});

test('comment bodies and second-level hierarchy survive normalization', async () => {
  const fixtureData = await fixture('comments-dom-result.json');
  const rows = normalizeDomCommentRows(fixtureData.results, {
    note_id: '68aabbcc0000000011223344',
    top_fetch_status: fixtureData.top_fetch_status,
    expected_comment_count: 3,
  });
  assert.equal(rows.length, 3);
  assert.equal(rows[0].text, '希望把第二步讲得更具体');
  assert.equal(rows[1].is_reply, true);
  assert.equal(rows[1].parent_comment_id, rows[0].comment_id);
  assert.equal(rows[2].reply_to, '读者乙');
  assert.equal(rows[0].reply_fetch_status, 'complete');
});

test('missing DOM IDs get explicit synthetic identity instead of number coercion', () => {
  const rows = normalizeDomCommentRows([
    { text: '正文', author: '读者', is_reply: false, likes: 0 },
    {
      text: '二级正文', author: '另一位读者', is_reply: true, likes: 0,
      parent_comment_id: 'dom-top-1', root_comment_id: 'dom-top-1',
    },
  ], { note_id: '68aabbcc0000000011223344' });
  assert.equal(rows[0].comment_id_source, 'synthetic');
  assert.match(rows[0].comment_id, /^dom:/);
  assert.equal(rows[1].parent_comment_id, rows[0].comment_id);
  assert.equal(rows[1].root_comment_id, rows[0].comment_id);
});
