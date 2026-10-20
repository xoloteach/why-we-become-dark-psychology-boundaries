"""Sample every scene's settled layout; this does not establish full playback QA."""
from pathlib import Path
import json,subprocess,math
import numpy as np,cv2
from PIL import Image,ImageDraw
import render as r
R=Path(__file__).resolve().parents[1];out=R/'qa/layout';out.mkdir(parents=True,exist_ok=True)
orig=r.text;violations=[];current=None

def tracked(f,t,x,y,size=34,col=r.INK,width=800,alpha=1,weight='ExtraBold',center=False):
 a=r.glyph(t,size,col,width,weight);xx=x-a.shape[1]/2 if center else x
 if alpha>.8 and (xx<45 or xx+a.shape[1]>1875 or y+a.shape[0]>890):violations.append({'scene':current,'text':t,'box':[round(xx),round(y),a.shape[1],a.shape[0]]})
 return orig(f,t,x,y,size,col,width,alpha,weight,center)
r.text=tracked
pages=[];tiles=[];manifest=[]
for s in r.scenes:
 current=s['id'];t=max(s['start']+.1,min(s['end']-.12,max(s['start']+.9,(max(s['cues'])+.65 if s['cues'] else s['start']+.9))))
 f=r.frame(t);small=Image.fromarray(cv2.cvtColor(cv2.resize(f,(640,360)),cv2.COLOR_BGR2RGB));canvas=Image.new('RGB',(640,390),'white');canvas.paste(small);d=ImageDraw.Draw(canvas);d.text((12,367),f"Scene {s['id']:03} | {s['script_line']} | {t:.2f}s | {s['kind']}",fill='black');tiles.append(canvas);manifest.append({'scene':s['id'],'time':t,'panel':s['art']})
 if len(tiles)==12 or s is r.scenes[-1]:
  sheet=Image.new('RGB',(1920,390*math.ceil(len(tiles)/3)),(235,235,235))
  for i,a in enumerate(tiles):sheet.paste(a,((i%3)*640,(i//3)*390))
  p=out/f'layout-{len(pages)+1:02}.jpg';sheet.save(p,quality=90);pages.append(str(p.relative_to(R)));tiles=[]
(R/'qa/layout_manifest.json').write_text(json.dumps({'samples':manifest,'contact_sheets':pages,'geometry_flags':violations,'scope':'sampled source layouts, not captioned encoded full playback'},indent=2)+'\n')
print(json.dumps({'scenes_sampled':len(manifest),'contact_sheets':len(pages),'geometry_flags':violations},indent=2))
# Actual libass-captioned source samples at layout/rhetorical pivots.
for line in [73,125,159,187,247,278,313]:
 s=next(x for x in r.scenes if x['script_line']==line);t=min(s['end']-.15,max(s['start']+1.1,s['cues'][-1]+.8 if s['cues'] else s['start']+1.1));p=out/f'captioned-line-{line}.png'
 f=r.frame(t)
 cmd=['ffmpeg','-y','-v','error','-f','rawvideo','-pixel_format','bgr24','-video_size','1920x1080','-i','pipe:0','-vf',f'setpts=PTS+{t}/TB,subtitles=plans/captions.ass:fontsdir=fonts','-frames:v','1',str(p)]
 subprocess.run(cmd,input=f.tobytes(),check=True)
print('Captioned inspection samples ready')
