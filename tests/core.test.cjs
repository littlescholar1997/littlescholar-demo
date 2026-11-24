const assert=require('node:assert/strict'),fs=require('node:fs');const C=require('../admin/core.js');const seed=JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'../content/site.json')));
assert.equal(C.validate(structuredClone(seed)).posts.length,8);
assert.equal(C.safeUrl('javascript:alert(1)'), '');assert.equal(C.safeUrl('data:text/html,evil',true),'');
assert(!C.markdown('<img src=x onerror=alert(1)>').includes('<img'));assert(C.markdown('## 標題\n\n**重點**').includes('<strong>重點</strong>'));
const duplicate=structuredClone(seed);duplicate.posts[2].slug=duplicate.posts[0].slug;assert.throws(()=>C.validate(duplicate),/重複/);
const traversal=structuredClone(seed);traversal.posts[0].slug='../admin';assert.throws(()=>C.validate(traversal),/網址/);
const popup=structuredClone(seed);popup.popup.start='2026-12-03T10:00';popup.popup.end='2026-12-01T10:00';assert.throws(()=>C.validate(popup),/結束時間/);
const image=structuredClone(seed);image.posts[0].coverAlt='';assert.throws(()=>C.validate(image),/圖片說明/);
console.log('PASS: schema, unsafe URLs, escaped Markdown, duplicate slugs, traversal, popup dates, image descriptions.');
