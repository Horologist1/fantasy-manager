import fs from 'node:fs/promises';
import path from 'node:path';
import { GUIDE_SECTIONS } from '../src/user_guide.js';

const root = path.resolve(import.meta.dirname, '../..');
const content = '# Fantasy Manager Devkit — User guide\n\n'
  + GUIDE_SECTIONS.map(s => '## '+s.title+'\n\n'
    + (s.steps ? s.steps.map((text,i)=>(i+1)+'. '+text).join('\n')+'\n\n' : '')
    + (s.paragraphs || []).join('\n\n')).join('\n\n')+'\n';
await fs.writeFile(path.join(root,'devkit_web/USER_GUIDE.md'), content);
await fs.mkdir(path.join(root,'user_docs/guides'), {recursive:true});
await fs.writeFile(path.join(root,'user_docs/guides/devkit_user_guide.md'), content);
console.log('User guide generated from the in-app guide.');
