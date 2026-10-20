"""Fail-closed Git checkpoint. Authentication is provided externally, never in source."""
from pathlib import Path
import subprocess,re,hashlib,json,sys
R=Path(__file__).resolve().parents[1]
def run(*args):
 return subprocess.check_output(['git','-C',str(R),*args],text=True).strip()
def checkpoint(message):
 run('add','--all')
 paths=run('diff','--cached','--name-only','--diff-filter=ACM').splitlines()
 for name in paths:
  data=(R/name).read_bytes()
  for pattern in [rb'gh[pousr]_[A-Za-z0-9]{20,}',rb'(?i)(?:API_KEY|GITHUB_TOKEN)\s*=\s*[a-zA-Z0-9]{20,}']:
   if re.search(pattern,data):raise RuntimeError('Secret scan blocked '+name)
  if len(data)>95*1024*1024:raise RuntimeError('File exceeds conservative Git limit: '+name)
 if paths:run('commit','-m',message)
 run('push','origin','HEAD:main')
 local=run('rev-parse','HEAD');remote=run('ls-remote','origin','refs/heads/main').split()[0]
 if local!=remote:raise RuntimeError('Remote verification failed')
 print(json.dumps({'checkpoint':message,'verified_commit':local}),flush=True)
 return local
if __name__=='__main__':checkpoint(sys.argv[1] if len(sys.argv)>1 else 'Production checkpoint')
