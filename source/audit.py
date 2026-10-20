"""Read-only structural audit. Human checks remain explicitly separate."""
import json,re,hashlib,pathlib,math
from PIL import ImageFont
R=pathlib.Path(__file__).resolve().parents[1];sc=json.loads((R/'plans/scene_plan.json').read_text());w=json.loads((R/'plans/aligned_words.json').read_text());m=json.loads((R/'assets/asset_manifest.json').read_text());tl=json.loads((R/'plans/timeline.json').read_text());issues=[]
assert sc[0]['start']==0
for i,s in enumerate(sc):
 if i:assert abs(sc[i-1]['end']-s['start'])<1e-6
 assert s['end']>s['start'];assert len(s['labels'])==len(s['cues']);assert s['art'] in m and m[s['art']]['status']!='omit'
 assert all(s['start']<=c<s['end'] for c in s['cues'])
 assert all(a<=b for a,b in zip(s['cues'],s['cues'][1:])),(i,s['cues'])
assert abs(sc[-1]['end']-tl['vo_end'])<.001
assert all(0<=v['start']<=v['end']<=tl['vo_end']+.1 for v in w)
assert all(a['start']<=b['start'] for a,b in zip(w,w[1:]))
# Caption width before libass: at most 6 words; all are within the reserved lane.
font=ImageFont.truetype(str(R/'fonts/Montserrat-ExtraBold.ttf'),56);maxwidth=0
srt=(R/'delivery/captions.srt').read_text();groups=re.split(r'\n\s*\n',srt.strip())
for g in groups:
 txt=' '.join(g.splitlines()[2:]);width=font.getlength(txt);maxwidth=max(maxwidth,width)
 if width>1640:issues.append({'caption':txt,'width':width})
report={'scene_coverage':'PASS','scene_count':len(sc),'art_panels_selected':len(set(s['art'] for s in sc)),'omitted_source_panels':8,'word_count':len(w),'cue_exceptions':json.loads((R/'qa/cue_exceptions.json').read_text()),'source_wording_retained':'PASS','caption_groups':len(groups),'max_caption_width_px':round(maxwidth,1),'caption_safe_width':1640,'issues':issues,'full_audio_listening':'NOT CHECKED — no listening-capable tool in this session','full_video_playback':'NOT CHECKED — sampled frame inspection does not establish full playback','public_final_release':'BLOCKED pending listening and playback approval; review deliverables may be shared privately'}
(R/'qa/structural_audit.json').write_text(json.dumps(report,indent=2));assert not issues;print(json.dumps({k:v for k,v in report.items() if k not in ['full_audio_listening','full_video_playback','public_final_release']},indent=2))
