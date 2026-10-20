from pathlib import Path
import requests,json,subprocess,time,os,sys
R=Path('/data/boundaries');base='https://api.github.com/repos/xoloteach/why-we-become-dark-psychology-boundaries';s=requests.Session();s.headers.update({'Authorization':'Bearer '+Path('/data/.private/github-token').read_text().strip(),'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
def api(method,path,**kw):
 r=s.request(method,base+path,timeout=60,**kw);r.raise_for_status();return r.json() if r.content else None
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=R,text=True).split()[0]
assert sha==remote,'Local inputs are not backed up'
runs=api('GET','/actions/workflows/render-mp4.yml/runs?per_page=10')['workflow_runs'];active=[r for r in runs if r['status'] in ['queued','in_progress','waiting','requested','pending']]
if active:
 run=active[0];assert run['head_sha']==sha,'A different MP4 build is already active; do not duplicate'
else:
 api('POST','/actions/workflows/render-mp4.yml/dispatches',json={'ref':'main'})
 run=None
 for _ in range(30):
  time.sleep(3);runs=api('GET','/actions/workflows/render-mp4.yml/runs?per_page=10')['workflow_runs'];matches=[r for r in runs if r['head_sha']==sha and r['event']=='workflow_dispatch']
  if matches:run=matches[0];break
 assert run,'Dispatched but no run found; inspect before retrying'
record={'run_id':run['id'],'url':run['html_url'],'reviewed_commit':sha,'status':run['status'],'output':'episode-v3-review.mp4','workflow':'render-mp4.yml','artifact_retention_days':14}
(R/'plans/render_run.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
# Save the real job identifier in Git as well. This does not alter the reviewed render commit.
subprocess.run([sys.executable,'source/checkpoint.py','Record active persistent MP4 render and reviewed commit'],cwd=R,check=True)
last=None
for _ in range(480):
 run=api('GET',f"/actions/runs/{record['run_id']}");jobs=api('GET',f"/actions/runs/{record['run_id']}/jobs")['jobs'];steps=[st['name'] for j in jobs for st in j.get('steps',[]) if st['status']=='in_progress'];state=(run['status'],run.get('conclusion'),tuple(steps))
 if state!=last:print(json.dumps({'run_id':run['id'],'status':state[0],'conclusion':state[1],'active_steps':steps}),flush=True);last=state
 if run['status']=='completed':
  record.update({'status':'completed','conclusion':run['conclusion']});(R/'plans/render_run.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
  if run['conclusion']!='success':raise SystemExit(1)
  arts=api('GET',f"/actions/runs/{run['id']}/artifacts")['artifacts'];assert arts,'Successful run has no artifact'
  a=arts[0];resp=s.get(a['archive_download_url'],timeout=300);resp.raise_for_status();dest=Path('/data/boundaries-render-artifact.zip');dest.write_bytes(resp.content);print(json.dumps({'artifact_id':a['id'],'artifact_bytes':len(resp.content),'artifact_path':str(dest)}),flush=True);raise SystemExit(0)
 time.sleep(20)
raise SystemExit('Controller timeout; persistent render may still be running. Check the recorded run before retrying.')
