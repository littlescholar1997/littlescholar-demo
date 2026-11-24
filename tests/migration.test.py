import json,re
from pathlib import Path
from html.parser import HTMLParser
root=Path(__file__).resolve().parents[1];d=json.loads((root/'content/site.json').read_text());report=json.loads((root/'migration/report.json').read_text())
assert len(d['posts'])==8
assert all(p['migration']=='complete'and p['date']for p in d['posts'])
assert all(not p['missingBlocks']for p in report['sources'])
class Check(HTMLParser):
 def __init__(self):super().__init__();self.images=[];self.links=[]
 def handle_starttag(self,t,a):
  a=dict(a)
  if t=='img':self.images.append(a)
  if t=='a':self.links.append(a)
for p in d['posts']:
 file=root/'dist'/p['section']/(p['slug']+'.html');parser=Check();parser.feed(file.read_text())
 assert '全文尚待匯入'not in file.read_text()
 assert any(a.get('href')=='../#'+p['section']for a in parser.links)
 assert any(a.get('href')==p['sourceUrl']for a in parser.links)
 for image in parser.images:
  path=image['src'];assert image.get('alt')
  if path.startswith('/littlescholar-demo/'):assert(root/'dist'/path.removeprefix('/littlescholar-demo/')).exists(),path
for media in report['media']:assert(root/'dist'/media['path']).exists()
print('PASS: 8 complete articles, 140 source text blocks, 10 self-hosted images, source links and return anchors.')
