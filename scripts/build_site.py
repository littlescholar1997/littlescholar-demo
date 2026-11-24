#!/usr/bin/env python3
"""Build public article pages and lists from CMS JSON. Python standard library only."""
import argparse,json,re,html,shutil
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
def esc(s):return html.escape(str(s or ''),quote=True)
def safe_url(s,image=False):
 s=str(s or '').strip()
 if s.startswith('https://'):return s
 if image and re.fullmatch(r'/littlescholar-demo/uploads/[a-zA-Z0-9_/-]+\.webp',s):return s
 if image and re.fullmatch(r'data:image/(png|jpeg|webp);base64,[a-zA-Z0-9+/=]+',s):return s
 if not image and re.fullmatch(r'#[a-zA-Z0-9_-]+',s):return s
 return ''
def inline(s):
 out=[]
 for part in re.split(r'(\[[^\]]+\]\([^)]+\))',str(s)):
  m=re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)',part)
  if m:
   url=safe_url(m[2]);out.append('<a href="'+esc(url)+'" target="_blank" rel="noopener">'+esc(m[1])+'</a>' if url else esc(m[1]))
  else:out.append(re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',esc(part)))
 return ''.join(out)
def markdown(s):
 lines=[];is_list=False
 for line in str(s).splitlines():
  if not line.strip():
   if is_list:lines.append('</ul>');is_list=False
   continue
  m=re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)',line)
  if m:
   if is_list:lines.append('</ul>');is_list=False
   url=safe_url(m[2],True)
   if url:lines.append(f'<figure><img src="{esc(url)}" alt="{esc(m[1])}" loading="lazy"><figcaption>{esc(m[1])}</figcaption></figure>')
  elif line.startswith('- '):
   if not is_list:lines.append('<ul>');is_list=True
   lines.append('<li>'+inline(line[2:])+'</li>')
  else:
   if is_list:lines.append('</ul>');is_list=False
   if line.startswith('### '):lines.append('<h3>'+inline(line[4:])+'</h3>')
   elif line.startswith('## '):lines.append('<h2>'+inline(line[3:])+'</h2>')
   else:lines.append('<p>'+inline(line)+'</p>')
 if is_list:lines.append('</ul>')
 return ''.join(lines)
def validate(d):
 assert d.get('schemaVersion')==1,'Unsupported schema'
 keys=set()
 for p in d['posts']:
  assert p['section'] in ('news','teacher')
  assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',p['slug']) and len(p['slug'])<=100,'Invalid slug'
  key=p['section']+'/'+p['slug'];assert key not in keys,'Duplicate URL';keys.add(key)
  assert p['status'] in ('draft','published','archived')
  assert p['title'].strip()
 return d
ARTICLE_CSS='''body{margin:0;font:16px/1.95 "Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;color:#29342e;background:white}*{box-sizing:border-box}a{color:#a9000a;text-underline-offset:4px}header{border-bottom:1px solid #dde3dc;padding:22px max(20px,calc((100vw - 1120px)/2));display:flex;justify-content:space-between;gap:20px;align-items:center}header a{color:#29342e;text-decoration:none;font-weight:650}header small{color:#bc000b;margin-left:10px;font-size:12px}main{width:min(760px,calc(100% - 40px));margin:55px auto 80px}h1{font-size:clamp(27px,4vw,40px);line-height:1.55;letter-spacing:-.035em;margin:17px 0 23px;text-wrap:balance}h2{font-size:25px;line-height:1.6;margin-top:36px}h3{font-size:21px}p{margin:18px 0}img{max-width:100%;height:auto;display:block;max-height:520px;object-fit:contain;margin:25px auto}figure{margin:28px 0}figcaption,.meta{font-size:13px;color:#687368}.lead{font-size:18px;color:#5b685e}.note{background:#fff7e5;color:#6e582d;padding:15px 19px;font-size:14px;border-radius:6px}.article-list{display:grid;gap:0;margin-top:25px}.article-card{padding:25px 0;border-bottom:1px solid #dde3dc;color:inherit;text-decoration:none}.article-card h2{margin:8px 0;font-size:23px}.article-card:hover h2{color:#bc000b}.article-card p{font-size:15px;margin:10px 0;color:#5b685e}input{width:100%;min-height:48px;padding:10px 14px;border:1px solid #bcc9b7;border-radius:6px;font:inherit}.return-links{display:flex;gap:12px 25px;flex-wrap:wrap;border-top:1px solid #dde3dc;margin-top:35px}.back{display:inline-flex;min-height:44px;align-items:center;margin-top:25px}footer{border-top:1px solid #dde3dc;padding:30px 20px;text-align:center;font-size:13px;color:#687368}blockquote{margin:20px 0;font-size:18px}.voice{padding:28px 0;border-bottom:1px solid #dde3dc}.voice h2{margin:0}.voice p{font-size:14px;margin:5px 0}a:focus-visible,input:focus-visible{outline:3px solid #bc000b;outline-offset:4px}@media(max-width:600px){header{align-items:start;font-size:14px}header small{display:block;margin:0}main{margin-top:35px}.lead{font-size:16px}}'''
def shell(title,body,section=''):
 prefix='../' if section else './'
 return '<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="'+esc(title)+'｜小學者美語"><title>'+esc(title)+'｜小學者美語</title><style>'+ARTICLE_CSS+'</style></head><body><header><a href="'+prefix+'">小學者美語 <small>Little Scholar · Since 1997</small></a><a href="'+prefix+'#contact">聯繫我們</a></header><main>'+body+'</main><footer>小學者美語・Since 1997<br>本頁為網站設計與內容管理示範稿。</footer></body></html>'
def build(content,out):
 d=validate(json.loads(Path(content).read_text()));out=Path(out).resolve();assert out!=ROOT and out not in ROOT.parents,'Output must be separate from source';out.mkdir(parents=True,exist_ok=True)
 for folder in ('admin','content','assets','uploads'):
  shutil.copytree(ROOT/folder,out/folder,dirs_exist_ok=True)
 for filename in ('preview.html','.nojekyll'):
  if (ROOT/filename).exists():shutil.copy2(ROOT/filename,out/filename)
 published=[p for p in d['posts'] if p['status']=='published']
 public_data=dict(d);public_data['posts']=published;public_data['testimonials']=[v for v in d['testimonials'] if v['status']=='published'];(out/'content/site.json').write_text(json.dumps(public_data,ensure_ascii=False,indent=2))
 for section,label in [('news','最新消息'),('teacher','Ling 老師的叮嚀')]:
  dest=out/section
  if dest.exists():shutil.rmtree(dest)
  dest.mkdir(exist_ok=True)
  items=[p for p in published if p['section']==section];items.sort(key=lambda p:p.get('date',''),reverse=True)
  for p in items:
   cover=safe_url(p.get('cover'),True);source=safe_url(p.get('sourceUrl'))
   body='<p class="meta">'+esc(p.get('category'))+('　'+esc(p['date']) if p.get('date') else '')+'</p><h1>'+esc(p['title'])+'</h1><p class="lead">'+esc(p.get('summary'))+'</p>'
   if p.get('migration')=='excerpt':body+='<p class="note">這篇內容目前為摘要版，全文尚待匯入。完整內容請參閱原官網。</p>'
   if cover and ('('+cover+')') not in p.get('body',''):body+='<img src="'+esc(cover)+'" alt="'+esc(p.get('coverAlt'))+'">'
   body+=markdown(p.get('body',''))
   if source:body+='<p><a href="'+esc(source)+'" target="_blank" rel="noopener">查看 Wix 原文</a></p>'
   body+='<nav class="return-links" aria-label="文章返回連結"><a class="back" href="../#'+section+'">返回首頁'+label+'區塊</a><a class="back" href="./">返回'+label+'列表</a></nav>'
   (dest/(p['slug']+'.html')).write_text(shell(p['title'],body,section))
  cards=''.join('<a class="article-card" data-article href="'+esc(p['slug'])+'.html"><span class="meta">'+esc(p.get('category'))+('　'+esc(p['date']) if p.get('date') else '')+'</span><h2>'+esc(p['title'])+'</h2><p>'+esc(p.get('summary'))+'</p>'+('<span class="meta">全文待匯入</span>' if p.get('migration')=='excerpt' else '')+'</a>' for p in items)
  body='<a class="back" href="../#'+section+'">返回首頁'+label+'區塊</a><h1>'+label+'</h1><p class="lead">'+('講座、課程與小學者的消息。' if section=='news' else '陪孩子學習，也一起想一想。')+'</p><label for="archive-search">搜尋文章</label><input id="archive-search" type="search" placeholder="輸入標題或分類"><p id="archive-count" class="meta" aria-live="polite">共 '+str(len(items))+' 篇</p><div class="article-list">'+cards+'</div><script>const field=document.querySelector("input");const cards=[...document.querySelectorAll("[data-article]")];field.addEventListener("input",()=>{let n=0;for(const c of cards){c.hidden=!c.textContent.toLowerCase().includes(field.value.trim().toLowerCase());if(!c.hidden)n++}document.querySelector("#archive-count").textContent="找到 "+n+" 篇"});</script>'
  (dest/'index.html').write_text(shell(label,body,section))
 # Preserve the demo's previous summer-course URL after merging the duplicate summary.
 if any(p['slug']=='generation-z-english' and p['section']=='news' for p in published):
  (out/'news/summer-course-2026.html').write_text(shell('暑期與新班招生','<h1>暑期與新班招生</h1><p>此消息已整併至完整招生文章。</p><a href="generation-z-english.html">閱讀完整招生消息</a><p><a href="./">返回最新消息</a></p>','news'))
 dest=out/'voices';dest.mkdir(exist_ok=True)
 voices=sorted([v for v in d['testimonials']if v['status']=='published'],key=lambda v:v.get('order',0))
 body='<a class="back" href="../#voices">返回首頁學生見證區塊</a><h1>他們從小學者出發</h1>'+''.join('<article class="voice"><h2>'+esc(v['name'])+'</h2><p>'+esc(v.get('school'))+'</p><p>'+esc(v.get('role'))+'</p><blockquote>'+esc(v['quote'])+'</blockquote></article>' for v in voices)
 (dest/'index.html').write_text(shell('學生見證',body,'voices'))
 homepage=(ROOT/'index.html').read_text()
 # Render the homepage from the same source as archives and individual pages.
 news=sorted([p for p in published if p['section']=='news'],key=lambda p:p.get('date',''),reverse=True)[:3]
 if news:
  cards=[]
  for i,p in enumerate(news):
   cover=safe_url(p.get('cover'),True);url='news/'+p['slug']+'.html'
   image='<img class="'+('poster' if i==0 else 'news-thumb')+'" src="'+esc(cover)+'" alt="'+esc(p.get('coverAlt'))+'" loading="lazy">' if cover else '<span class="news-thumb" aria-hidden="true" style="display:grid;place-items:center;background:#edf2e9">閱讀</span>'
   text='<div><span class="news-type">'+esc(p.get('category'))+'</span><h3>'+esc(p['title'])+'</h3><span class="news-read">閱讀文章</span></div>'
   cards.append('<a class="'+('feature-news' if i==0 else 'news-item')+'" href="'+url+'">'+(image+text if i==0 else text+image)+'</a>')
  block='<div class="news-layout">'+cards[0]+'<div class="news-list">'+''.join(cards[1:])+'</div></div>'
  homepage=re.sub(r'<div class="news-layout">.*?(?=<p class="news-context">)',lambda m:block,homepage,count=1,flags=re.S)
 teachers=[p for p in published if p['section']=='teacher'];teachers.sort(key=lambda p:(p.get('featured',False),p.get('date','')),reverse=True)
 if teachers:
  p=teachers[0];image=safe_url(p.get('cover'),True)
  inner=('<img class="teacher-image" src="'+esc(image)+'" alt="'+esc(p.get('coverAlt'))+'" loading="lazy">' if image else '')+'<div><div class="section-label">Ling 老師的叮嚀</div><h2>陪孩子學習，<br>也一起想一想。</h2><h3>'+esc(p['title'])+'</h3><p>'+esc(p.get('summary'))+'</p><a class="text-link" href="teacher/'+p['slug']+'.html">閱讀完整文章</a></div>'
  homepage=re.sub(r'(<div class="wrap teacher">).*?(</div></div></section>)',lambda m:m[1]+inner+'</div></section>',homepage,count=1,flags=re.S)
 quotes=''.join('<article class="quote-card"><span class="quote-mark" aria-hidden="true">“</span><blockquote>'+esc(v['quote'])+'</blockquote><div class="quote-author"><h3>'+esc(v['name'])+'</h3><p>'+esc(v.get('school'))+'</p><small>'+esc(v.get('role'))+'</small></div></article>' for v in voices)
 homepage=re.sub(r'(<div class="quote-grid">).*?(</div></div></section>)',lambda m:m[1]+quotes+'</div></div></section>',homepage,count=1,flags=re.S)
 for section,label in [('news','所有最新消息'),('teacher','所有老師文章'),('voices','所有學生見證'),('about','關於小學者'),('courses','課程說明'),('contact','聯絡資料')]:
  # Replace a previously generated archive link before adding one; builds are repeatable.
  homepage=re.sub(r'<!-- archive-'+section+r' -->.*?<!-- /archive-'+section+r' -->','',homepage,flags=re.S)
  pattern=r'(<section[^>]*id="'+section+r'"[^>]*>)(.*?)(</section>)'
  m=re.search(pattern,homepage,re.S)
  if m:homepage=homepage[:m.start()]+m[1]+m[2]+'<!-- archive-'+section+' --><div class="wrap" style="margin-top:24px"><a class="text-link" href="'+section+'/">查看'+label+'</a></div><!-- /archive-'+section+' -->'+m[3]+homepage[m.end():]
 homepage=re.sub(r'<script src="assets/content-runtime.js"></script>','',homepage)
 homepage=homepage.replace('</body>','<script src="assets/content-runtime.js"></script></body>')
 for section,label in [('about','關於小學者'),('courses','課程說明'),('contact','聯繫我們')]:
  m=re.search(r'<section[^>]*id="'+section+r'"[^>]*>.*?</section>',homepage,re.S)
  if not m:continue
  styles=re.search(r'<style>(.*?)</style>',homepage,re.S)[1]
  nav='<header class="site-header"><nav class="wrap" style="padding:18px 0;display:flex;justify-content:space-between;gap:20px"><a href="../#'+section+'">返回首頁'+label+'區塊</a><a href="../">小學者美語・Since 1997</a></nav></header>'
  content=m[0].replace('src="assets/','src="../assets/').replace('href="#contact"','href="../#contact"')
  content=re.sub(r'<!-- archive-'+section+r' -->.*?<!-- /archive-'+section+r' -->','',content,flags=re.S)
  page='<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+label+'｜小學者美語</title><style>'+styles+'</style></head><body>'+nav+'<main>'+content+'</main><div class="wrap" style="padding:0 0 40px"><a class="text-link" href="https://www.littlescholar-edu.com/" target="_blank" rel="noopener">查看 Wix 官網原頁</a></div><script src="../assets/info-page.js"></script></body></html>'
  (out/section).mkdir(exist_ok=True);(out/section/'index.html').write_text(page)
 # Original Wix informational text is presented in full on the independent pages.
 pages_path=ROOT/'content/pages.json'
 if pages_path.exists():
  for item in json.loads(pages_path.read_text()):
   section=item['slug'];body='<a class="back" href="../#'+section+'">返回首頁'+item['title']+'區塊</a><h1>'+esc(item['title'])+'</h1>'+markdown(item['body'])+'<p><a href="'+esc(item['sourceUrl'])+'" target="_blank" rel="noopener">查看 Wix 官網原頁</a></p>'
   (out/section).mkdir(exist_ok=True);(out/section/'index.html').write_text(shell(item['title'],body,section))
 (out/'index.html').write_text(homepage)
 return {'articles':len(published),'testimonials':len(voices),'output':str(out)}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--content',default=str(ROOT/'content/site.json'));parser.add_argument('--output',default=str(ROOT/'_site'));a=parser.parse_args();print(json.dumps(build(a.content,a.output),ensure_ascii=False))
