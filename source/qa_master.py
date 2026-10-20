from pathlib import Path
import sys,json,subprocess,math
from fractions import Fraction
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];p=Path(sys.argv[1]);tl=json.loads((R/'plans/timeline.json').read_text());sc=json.loads((R/'plans/scene_plan.json').read_text())
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)],text=True));v=next(x for x in probe['streams'] if x['codec_type']=='video');a=next(x for x in probe['streams'] if x['codec_type']=='audio');dur=float(probe['format']['duration']);fps=float(Fraction(v['avg_frame_rate']))
assert (v['width'],v['height'])==(1920,1080);assert v['pix_fmt']=='yuv420p';assert v['codec_name']=='h264';assert abs(fps-30)<.001;assert abs(dur-tl['total'])<=.5;assert a['codec_name']=='aac'
q=subprocess.run(['ffmpeg','-hide_banner','-i',str(p),'-vn','-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);loud=json.JSONDecoder().raw_decode(q.stderr[q.stderr.rfind('{'):])[0];assert -17.5<=float(loud['input_i'])<=-14.5
samples=[]
for s in sc:
 t=max(s['start']+.1,min(s['end']-.12,max(s['start']+.9,(max(s['cues'])+.65 if s['cues'] else s['start']+.9))));samples.append({'scene':s['id'],'time':t,'kind':s['kind']})
# Time-separated states prove actual movement at selected pivots, not just source layouts.
for line in [73,125,144,177,187,205,247,278]:
 s=next(x for x in sc if x['script_line']==line)
 for dt in [.15,.65,1.25]:samples.append({'scene':s['id'],'time':min(s['end']-.08,s['start']+dt),'kind':'motion-state'})
samples.append({'scene':'endcard','time':dur-1,'kind':'endcard'})
frames=R/'qa/encoded-frames';frames.mkdir(exist_ok=True);tiles=[];sheets=[]
for i,s in enumerate(samples):
 out=frames/f'{i:03}.jpg';subprocess.run(['ffmpeg','-y','-v','error','-ss',str(s['time']),'-i',str(p),'-frames:v','1','-q:v','2',str(out)],check=True)
 im=Image.open(out);assert im.size==(1920,1080);tile=Image.new('RGB',(640,390),'white');tile.paste(im.resize((640,360)));ImageDraw.Draw(tile).text((10,367),f"Scene {s['scene']} | {s['time']:.2f}s | {s['kind']}",fill='black');tiles.append(tile)
 if len(tiles)==12 or i==len(samples)-1:
  sheet=Image.new('RGB',(1920,390*math.ceil(len(tiles)/3)),(235,235,235))
  for j,im in enumerate(tiles):sheet.paste(im,((j%3)*640,(j//3)*390))
  sp=R/f'qa/encoded-layout-{len(sheets)+1:02}.jpg';sheet.save(sp,quality=90);sheets.append(str(sp.relative_to(R)));tiles=[]
report={'technical':'PASS','duration_seconds':dur,'expected_duration_seconds':tl['total'],'fps':fps,'video_codec':v['codec_name'],'audio_codec':a['codec_name'],'integrated_lufs':float(loud['input_i']),'true_peak_dbtp':float(loud['input_tp']),'sampled_frames':samples,'inspection_contact_sheets':sheets,'visual_review':'PENDING agent inspection of downloaded encoded frames','full_audio_listening':'NOT CHECKED','full_video_playback':'NOT CHECKED'}
(R/'qa/master_technical.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['technical','duration_seconds','fps','integrated_lufs','true_peak_dbtp']},indent=2))
