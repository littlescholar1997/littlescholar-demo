#!/usr/bin/env python3
import argparse,json,re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
class Check(HTMLParser):
 def __init__(self):super().__init__();self.images=[];self.links=[];self.ids=[]
 def handle_starttag(self,t,a):
  a=dict(a)
  if t=='img':self.images.append(a)
  if t=='a':self.links.append(a.get('href',''))
  if a.get('id'):self.ids.append(a['id'])
def audit(root):
 root=Path(root).resolve();issues=[];pages=[]
 for path in sorted(root.rglob('*.html')):
  p=Check();p.feed(path.read_text());page=str(path.relative_to(root));pages.append(page)
  if len(p.ids)!=len(set(p.ids)):issues.append({'page':page,'issue':'duplicate IDs'})
  for image in p.images:
   if 'alt'not in image:issues.append({'page':page,'issue':'missing alt'})
   src=image.get('src','')
   if src.startswith('/littlescholar-demo/')and not(root/src.removeprefix('/littlescholar-demo/')).exists():issues.append({'page':page,'image':src})
  for link in p.links:
   u=urlsplit(link)
   if u.scheme or u.netloc or not u.path:continue
   target=(root/u.path.removeprefix('/littlescholar-demo/'))if u.path.startswith('/littlescholar-demo/')else(path.parent/unquote(u.path))
   if target.is_dir():target=target/'index.html'
   if not target.exists():issues.append({'page':page,'link':link})
 return {'pages':pages,'issues':issues}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('--report');a=parser.parse_args();r=audit(a.directory)
 if a.report:Path(a.report).write_text(json.dumps(r,ensure_ascii=False,indent=2))
 print(json.dumps(r,ensure_ascii=False));raise SystemExit(bool(r['issues']))
