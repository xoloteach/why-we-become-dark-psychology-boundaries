from pathlib import Path
import requests,json,hashlib,zipfile,subprocess
ROOT=Path('/data/boundaries');OUT=Path('/data/rendered-review-v3');D=Path('/data/delivery');D.mkdir(exist_ok=True)
run=json.loads((ROOT/'plans/render_run.json').read_text());manifest=json.loads((OUT/'delivery/build-manifest.json').read_text());tech=json.loads((OUT/'qa/master_technical.json').read_text());review=json.loads((ROOT/'qa/encoded_review.json').read_text())
assert manifest['commit']==run['reviewed_commit'] and str(manifest['run_id'])==str(run['run_id'])
assert tech['technical']=='PASS' and review['corrected_encoded_verification']=='PASS'
video=OUT/'delivery/episode-v3-review.mp4';sha=hashlib.sha256(video.read_bytes()).hexdigest()
s=requests.Session();s.headers.update({'Authorization':'Bearer '+Path('/data/.private/github-token').read_text().strip(),'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
api='https://api.github.com/repos/xoloteach/why-we-become-dark-psychology-boundaries'
r=s.get(api,timeout=60);r.raise_for_status();assert r.json()['private'] is True
qa=D/'WWB-Boundaries-v3-review-notes.zip'
with zipfile.ZipFile(qa,'w',zipfile.ZIP_DEFLATED) as z:
 for name in ['delivery/build-manifest.json','delivery/captions.srt','delivery/seo.md','delivery/credits-licenses.md','delivery/panel_sync_review.md','qa/master_technical.json','qa/structural_audit.json']:
  z.write(OUT/name,name)
 z.write(ROOT/'qa/encoded_review.json','qa/encoded_review.json')
# Explicit credential-value scan of all text members; assets contain no provider configuration.
secrets=[p.read_bytes().strip() for p in Path('/data/.private').glob('*key') if p.is_file()]+[Path('/data/.private/github-token').read_bytes().strip()]
with zipfile.ZipFile(qa) as z:
 for name in z.namelist():
  body=z.read(name);assert not any(len(secret)>12 and secret in body for secret in secrets),'Sensitive value in release notes'
tag=f"review-v3-run-{run['run_id']}"
r=s.get(api+'/releases/tags/'+tag,timeout=60)
if r.status_code==404:
 body=f"1080p 30fps review master, 859.1 seconds. Rendered from {manifest['commit']} by Actions run {run['run_id']}. Technical checks and sampled encoded-frame inspection passed. Full audio listening and continuous playback: NOT CHECKED. SHA-256: {sha}. Private versioned backup; not a public video publication."
 r=s.post(api+'/releases',json={'tag_name':tag,'target_commitish':manifest['commit'],'name':'Why We Become — Boundaries v3 review master','body':body,'draft':False,'prerelease':True},timeout=60)
r.raise_for_status();release=r.json();assert release['prerelease'] and release['target_commitish']==manifest['commit']
assets={x['name']:x for x in release['assets']}
for path,name,ctype in [(video,'WWB-Dark-Psychology-Boundaries-v3-1080p.mp4','video/mp4'),(qa,qa.name,'application/zip')]:
 if name not in assets:
  with path.open('rb') as f:
   r=s.post(release['upload_url'].split('{')[0],params={'name':name},headers={'Content-Type':ctype},data=f,timeout=600)
  r.raise_for_status();assets[name]=r.json()
asset=assets['WWB-Dark-Psychology-Boundaries-v3-1080p.mp4'];assert asset['size']==video.stat().st_size
restored=D/asset['name']
r=s.get(asset['url'],headers={'Accept':'application/octet-stream'},stream=True,timeout=600);r.raise_for_status()
with restored.open('wb') as f:
 for chunk in r.iter_content(1024*1024):f.write(chunk)
assert hashlib.sha256(restored.read_bytes()).hexdigest()==sha,'Release restore hash mismatch'
record={'review_master':True,'release_url':release['html_url'],'release_tag':tag,'release_id':release['id'],'asset_id':asset['id'],'render_run':run['url'],'reviewed_commit':manifest['commit'],'sha256':sha,'bytes':restored.stat().st_size,'duration_seconds':tech['duration_seconds'],'resolution':[1920,1080],'fps':30,'technical':'PASS','sampled_visual_review':'PASS','full_listening':'NOT CHECKED','full_playback':'NOT CHECKED','release_restore_sha256_verified':True,'repository_private':True}
(ROOT/'plans/delivery.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
