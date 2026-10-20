from pathlib import Path
import json,hashlib,subprocess,os
R=Path(__file__).resolve().parents[1]
paths=['script.md','audio/narration_master.flac','audio/final_mix.flac','plans/scene_plan.json','plans/captions.ass','assets/asset_manifest.json','source/render.py']
v={'commit':os.environ.get('GITHUB_SHA') or subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'run_id':os.environ.get('GITHUB_RUN_ID'),'target':'delivery/episode-v2-review.mp4','fps':30,'resolution':[1920,1080],'files':{p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in paths},'validation_scope':'Technical checks and sampled frames; full listening/playback must not be claimed from stills.'}
(R/'delivery/build-manifest.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
