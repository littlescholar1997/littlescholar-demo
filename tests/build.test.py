import importlib.util,json,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('build_site',root/'scripts/build_site.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
d=json.loads((root/'content/site.json').read_text())
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);source=p/'content.json';out=p/'out'
 d['posts'][0]['status']='draft';d['posts'][1]['title']='<script>alert(1)</script>';source.write_text(json.dumps(d))
 result=m.build(source,out)
 assert result['articles']==3
 assert not(out/'news/attention-and-habits.html').exists()
 article=(out/'news/generation-z-english.html').read_text();assert '<script>alert(1)</script>'not in article and '&lt;script&gt;'in article
 assert '摘要版'in article
 index=(out/'news/index.html').read_text();assert 'attention-and-habits.html'not in index
 assert '查看所有老師文章'in(out/'index.html').read_text()
 for name in ['張耀文','張培衡','黃胤凱']:assert name in(out/'voices/index.html').read_text()
 d['posts'][1]['status']='archived';source.write_text(json.dumps(d));m.build(source,out);assert not(out/'news/generation-z-english.html').exists()
 assert all(p['status']=='published' for p in json.loads((out/'content/site.json').read_text())['posts'])
print('PASS: drafts excluded, article URLs, safe text, summary labels, archives and testimonials.')
