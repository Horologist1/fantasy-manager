import { test } from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { safeJoin } from '../serve.mjs';

test('local server keeps requests within its source directory and handles malformed URLs', () => {
  const root=path.resolve('fixture/src');
  assert.equal(safeJoin(root,'/catalogs/base_files.json?version=1'),path.join(root,'catalogs/base_files.json'));
  for(const request of ['/../src-private/key.json','/%2e%2e/package.json','/%ZZ','/../src2/secret','/a%5c..%5c..%5csecret','/%00']) assert.equal(safeJoin(root,request),null,request);
});
