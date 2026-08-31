import assert from 'node:assert/strict';
import test from 'node:test';
import { parseArgs } from '../src/sync.mjs';

test('sync accepts repeated --note owner targets', () => {
  const options = parseArgs([
    '--workdir', '/tmp/ip',
    '--note', '68aabbcc0000000011223344',
    '--note', '68aabbcc0000000011223355',
  ]);
  assert.deepEqual(options.noteIds, [
    '68aabbcc0000000011223344',
    '68aabbcc0000000011223355',
  ]);
});

test('sync rejects malformed note IDs before browser access', () => {
  assert.throws(() => parseArgs(['--workdir', '/tmp/ip', '--note', 'public-url']), /24 位笔记 ID/);
});
