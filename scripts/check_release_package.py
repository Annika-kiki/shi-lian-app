from pathlib import Path
import re,json,subprocess
r=Path(__file__).resolve().parents[1] / 'releases/miniprogram-2';cfg=json.loads((r/'project.config.json').read_text());ign=[v['value'].strip('/') for v in cfg['packOptions']['ignore']]+['project.private.config.json']
files=[p for p in r.rglob('*') if p.is_file() and not any(str(p.relative_to(r))==x or str(p.relative_to(r)).startswith(x+'/') for x in ign)]
errors=[]
for p in files:
 if p.suffix=='.js':
  x=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
  if x.returncode:errors.append(x.stderr)
 if p.suffix not in ['.js','.json','.wxml','.wxss']:continue
 s=p.read_text()
 if p.suffix=='.json':json.loads(s)
 for rel in re.findall(r'require\(["\']([^"\']+)["\']\)',s):
  if rel.startswith('.'):
   q=(p.parent/rel).with_suffix('.js').resolve()
   if not q.exists() or q not in files:errors.append(f'{p}: module {rel}')
 for rel in re.findall(r'["\'](/(?:images|assets)/[^"\'{}]+\.(?:png|jpg|jpeg|mp4))["\']',s):
  if r/rel.lstrip('/') not in files:errors.append(f'{p}: asset {rel}')
 if p.suffix=='.json':
  for rel in json.loads(s).get('usingComponents',{}).values():
   q=(r/rel.lstrip('/') if rel.startswith('/') else p.parent/rel).with_suffix('.json').resolve()
   if q not in files:errors.append(f'{p}: component {rel}')
 if p.suffix=='.js' and ('mock-login' in s or re.search(r'wx\.request\(|headers\[.X-User-Id.\]\s*=',s)):errors.append(f'{p}: legacy transport')
for page in json.loads((r/'app.json').read_text())['pages']:
 for ext in ['.js','.json','.wxml','.wxss']:
  if r/(page+ext) not in files:errors.append(page+ext)
for p in files:
 if p.suffix=='.wxss':
  for rel in re.findall(r'@import\s+["\']([^"\']+)["\']',p.read_text()):
   if (p.parent/rel).resolve() not in files:errors.append(f'{p}: stylesheet {rel}')
 if p.suffix=='.wxml':
  js=p.with_suffix('.js')
  handlers=re.findall(r'(?:bind|catch)(?::[\w]+|[\w]+)=["\']([A-Za-z_$][\w$]*)["\']',p.read_text())
  for handler in handlers:
   if not re.search(r'\b'+re.escape(handler)+r'\s*\(',js.read_text()):errors.append(f'{p}: handler {handler}')
assert not errors,errors
assert sum(p.stat().st_size for p in files) < 1.5*1024*1024, 'main package budget exceeded'
assert all(p.stat().st_size < 200*1024 for p in files if p.suffix=='.png'), 'oversized image'
print('PASS: JS/JSON syntax, all module/component/image/page references, no legacy transport')
print('Included files',len(files),'raw bytes',sum(p.stat().st_size for p in files),'max image bytes',max(p.stat().st_size for p in files if p.suffix=='.png'))
