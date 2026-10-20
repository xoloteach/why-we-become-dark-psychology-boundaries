"""Why We Become: narration-driven, connected-layer 1080p motion renderer.
Transition equations adapted from gl-transitions (MIT); see third_party.
Layout/compositing primitives adapted from verified WWB benchmark commit in timeline.json.
"""
import os,sys,json,math,time,subprocess,bisect,functools,argparse
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];os.chdir(R);cv2.setNumThreads(1)
W,H,FPS=1920,1080,30
PAPER=(238,244,247);INK=(15,21,22);RUST=(60,98,200);GOLD=(58,179,232);WHITE=(244,247,250)
scenes=json.loads((R/'plans/scene_plan.json').read_text());starts=[s['start'] for s in scenes];meta=json.loads((R/'assets/asset_manifest.json').read_text());tl=json.loads((R/'plans/timeline.json').read_text());VO=tl['vo_end'];TOTAL=tl['total'];CH=[c['title'] for c in tl['chapters']]
def ease(u):u=min(1,max(0,u));return 1-(1-u)**3
def smooth(a,b,x):u=np.clip((x-a)/(b-a),0,1);return u*u*(3-2*u)
def spring(u):u=max(0,min(1,u));return (1-(1+7*u)*math.exp(-7*u))/(1-8*math.exp(-7))
@functools.lru_cache(maxsize=1200)
def glyph(t,size=34,col=INK,width=800,weight='ExtraBold'):
 font=ImageFont.truetype(str(R/f'fonts/Montserrat-{weight}.ttf'),size);d=ImageDraw.Draw(Image.new('RGBA',(1,1)));ls=[]
 for part in t.split('\n'):
  cur=''
  for word in part.split():
   z=(cur+' '+word).strip()
   if d.textlength(z,font=font)>width and cur:ls.append(cur);cur=word
   else:cur=z
  if cur:ls.append(cur)
 if not ls:ls=[' ']
 ht=round(size*1.24);ww=min(width,math.ceil(max(d.textlength(z,font=font) for z in ls)))+8;im=Image.new('RGBA',(ww,len(ls)*ht+12));d=ImageDraw.Draw(im)
 for i,z in enumerate(ls):d.text((3,i*ht-size*.12),z,font=font,fill=col[::-1]+(255,))
 return np.ascontiguousarray(np.asarray(im)[:,:,[2,1,0,3]])
def blit(f,im,x,y,alpha=1):
 if alpha<=0:return
 x,y=int(x),int(y);h,w=im.shape[:2];xa,ya=max(0,x),max(0,y);xb,yb=min(W,x+w),min(H,y+h)
 if xb<=xa or yb<=ya:return
 src=im[ya-y:yb-y,xa-x:xb-x];a=src[:,:,3:4].astype(np.float32)*(min(1,alpha)/255);dst=f[ya:yb,xa:xb];dst[:]=(dst*(1-a)+src[:,:,:3]*a).astype(np.uint8)
def text(f,t,x,y,size=34,col=INK,width=800,alpha=1,weight='ExtraBold',center=False):
 a=glyph(t,size,col,width,weight);blit(f,a,x-a.shape[1]/2 if center else x,y,alpha);return a.shape[0]
def line(f,a,b,col=RUST,th=4,p=1):
 if p<=0:return
 a=np.array(a,float);b=a+(np.array(b,float)-a)*min(1,p);cv2.line(f,tuple(a.astype(int)),tuple(b.astype(int)),col,th,cv2.LINE_AA)
def path(f,pts,col=RUST,th=5,p=1,arrow=False,marker=None):
 if p<=0:return
 pts=np.array(pts,float);lens=np.linalg.norm(np.diff(pts,axis=0),axis=1);left=lens.sum()*min(1,p);out=[pts[0]]
 for i,L in enumerate(lens):
  if left>=L:out.append(pts[i+1]);left-=L
  else:out.append(pts[i]+(pts[i+1]-pts[i])*(left/max(L,.001)));break
 out=np.array(out,np.int32);cv2.polylines(f,[out],False,col,th,cv2.LINE_AA)
 if arrow and len(out)>1 and p>.94:
  v=out[-1]-out[-2];v=v/max(np.linalg.norm(v),.001);n=np.array([-v[1],v[0]]);tip=out[-1];cv2.fillConvexPoly(f,np.array([tip,tip-v*18+n*9,tip-v*18-n*9],np.int32),col,cv2.LINE_AA)
 if marker is not None:
  left=lens.sum()*min(1,max(0,marker));q=pts[0]
  for i,L in enumerate(lens):
   if left>L:left-=L;q=pts[i+1]
   else:q=pts[i]+(pts[i+1]-pts[i])*left/max(.001,L);break
  cv2.circle(f,tuple(q.astype(int)),9,GOLD,-1,cv2.LINE_AA)
def rect(f,x,y,w,h,col):
 x,y,w,h=map(int,(x,y,w,h));r=10;cv2.rectangle(f,(x+r,y),(x+w-r,y+h),col,-1);cv2.rectangle(f,(x,y+r),(x+w,y+h-r),col,-1)
 for cx,cy in [(x+r,y+r),(x+w-r,y+r),(x+r,y+h-r),(x+w-r,y+h-r)]:cv2.circle(f,(cx,cy),r,col,-1,cv2.LINE_AA)
rng=np.random.default_rng(12);grain=rng.normal(0,.42,(H,W,1));BG={d:np.clip(np.array(INK if d else PAPER)[None,None,:]+grain*(.4 if d else 1),0,255).astype(np.uint8) for d in (False,True)}
@functools.lru_cache(maxsize=12)
def layer(key,mw,mh):
 p=R/(meta[key]['path'] if key in meta else f'assets/kit/{key}.png');a=cv2.imread(str(p),-1)
 if key in meta:x,y,x1,y1=meta[key]['bbox']
 else:
  yy,xx=np.where(a[:,:,3]>60);x,y,x1,y1=max(0,xx.min()-6),max(0,yy.min()-6),min(a.shape[1],xx.max()+7),min(a.shape[0],yy.max()+7)
 a=a[y:y1,x:x1];h,w=a.shape[:2];k=min(mw/w,mh/h);a=cv2.resize(a,(max(1,round(w*k)),max(1,round(h*k))),interpolation=cv2.INTER_AREA);return a
@functools.lru_cache(maxsize=8)
def ink_layer(key,mw,mh):
 a=layer(key,mw,mh).copy();gray=cv2.cvtColor(a[:,:,:3],cv2.COLOR_BGR2GRAY);a[:,:,3]=(a[:,:,3]*np.clip((232-gray)/80,0,1)).astype(np.uint8);a[:,:,:3]=cv2.cvtColor(gray,cv2.COLOR_GRAY2BGR);return a
def asset(f,key,cx,cy,mw,mh,alpha=1,scale=1,angle=0):
 a=layer(key,mw,mh)
 if scale!=1:a=cv2.resize(a,(max(1,round(a.shape[1]*scale)),max(1,round(a.shape[0]*scale))),interpolation=cv2.INTER_LINEAR)
 if angle:
  hh,ww=a.shape[:2];mat=cv2.getRotationMatrix2D((ww/2,hh/2),angle,1);a=cv2.warpAffine(a,mat,(ww,hh))
 blit(f,a,cx-a.shape[1]/2,cy-a.shape[0]/2,alpha)
def reveal_art(f,s,t):
 r=t-s['start'];feat=s['feature'];cx=390 if feat else (1415 if s['layout']=='right' else 505);cy=641 if feat else 555;mw,mh=(640,420) if feat else (830,570)
 fade=1;pose=None
 if s['kind']=='boundary' and s['script_line'] in [189,194,205,274,284,304,309]:
  # Connected illustration gives way to an independent complete-body pose, never a limb slice.
  swap=s['cues'][-1] if len(s['cues'])>1 else s['start']+2;fade=1-ease((t-swap)/.55)
  if t>=swap:
   u=ease((t-swap)/.7);key='C05' if s['script_line'] in [189,194,205] else 'C04';asset(f,key,cx+(u*90 if key=='C05' else 0),650,340,410,1-fade)
 a=layer(s['art'],mw,mh);ink=ink_layer(s['art'],mw,mh);ah,aw=a.shape[:2];x=cx-aw/2+(1-spring(r/.85))*32*(1 if s['layout']=='right' else -1);y=cy-ah/2+(1-spring(r/.85))*20
 cap=round(aw*ease(r/.68));fill=ease((r-.14)/.9)
 if cap>0:blit(f,ink[:,:cap],x,y,(1-fill)*fade);blit(f,a[:,:cap],x,y,fill*fade)
 # Material accent is separate from the connected hero.
 if s['kind'] in ('memory','evidence') and r<1.25:asset(f,'F01',cx,cy+mh/2-20,mw*.75,26,.13*(1-ease((r-.7)/.55)))
def diagram(f,s,t,x,y,w=790,h=310):
 kind=s['kind'];r=t-s['start'];D=s['end']-s['start'];labs=s['labels'];n=len(labs);cue=s['cues'];rev=[spring((t-c)/.55) for c in cue];cur=max([i for i,c in enumerate(cue) if t>=c]or[-1]);fg=WHITE if s['dark'] else INK;muted=(154,166,172) if s['dark'] else (110,118,123);soft=(36,43,48) if s['dark'] else (220,231,238);pr=ease(r/.7)
 def label(i,xx,yy,size=33,width=w,center=False):
  if 0<=i<n:text(f,labs[i],xx,yy,size,RUST if i==cur else fg,width,alpha=rev[i],center=center)
 if kind=='stack':
  rh=min(67,(h-10-(n-1)*12)/max(1,n))
  for i,l in enumerate(labs):
   a=rev[i]
   if a<=0:continue
   yy=y+i*(rh+12);xx=x+(1-a)*45;rect(f,xx,yy,w-8,rh,RUST if i==cur else soft);text(f,f'{i+1:02d}',xx+15,yy+12,23,WHITE if i==cur else fg,65,alpha=a);text(f,l,xx+83,yy+8,29,WHITE if i==cur else fg,w-105,alpha=a)
 elif kind in ('focus','quote','memory'):
  for i in range(n):
   a=rev[i];yy=y+i*min(112,h/max(n,1));line(f,(x,yy+6),(x,yy+66),RUST if i==cur else muted,5,a);label(i,x+32+(1-a)*25,yy,38 if n<3 else 32,w-46)
  if kind=='memory' and cur>=0:
   yy=y+h-14;pts=[(x+30+j*(w-60)/32,yy+math.sin(j*.48)*10*(1-ease((r-1)/max(1,D-2)))) for j in range(33)];path(f,pts,muted,2,pr)
 elif kind=='contrast':
  line(f,(x+w/2,y),(x+w/2,y+h-26),muted,2,pr)
  for i in range(min(2,n)):
   a=rev[i];cx=x+w*(.25 if i==0 else .75)
   if a<=0:continue
   cv2.ellipse(f,(int(cx),int(y+65)),(45,45),-90,0,360*a,RUST if i else fg,4,cv2.LINE_AA);text(f,'A' if i==0 else 'B',cx,y+40,35,fg,100,alpha=a,center=True);label(i,cx,y+142,30,int(w/2-40),True)
  if n>2:label(n-1,x+20,y+h-30,28,w-40)
 elif kind=='chain':
  gap=36;cw=(w-gap*(n-1))/max(1,n)
  for i in range(n):
   a=rev[i];xx=x+i*(cw+gap)
   if a>0:
    rect(f,xx,y+30,cw,150,soft);label(i,xx+cw/2,y+62,31,int(cw-30),True);line(f,(xx+18,y+168),(xx+cw-18,y+168),RUST,4,a)
   if i and rev[i]>.8:path(f,[(xx-gap+5,y+105),(xx-8,y+105)],RUST,4,ease((t-cue[i]-.25)/.5),True)
 elif kind=='loop':
  count=min(4,n);cw=(w-125)/2;hh=100;pos=[(x,y),(x+w-cw,y),(x+w-cw,y+192),(x,y+192)]
  for i in range(count):
   a=rev[i];xx,yy=pos[i]
   if a>0:rect(f,xx+(1-a)*15,yy,cw,hh,RUST if i==cur else soft);text(f,labs[i],xx+cw/2,yy+20,28,WHITE if i==cur else fg,int(cw-34),alpha=a,center=True)
  links=[[(x+cw+6,y+50),(x+w-cw-12,y+50)],[(x+w-cw/2,y+105),(x+w-cw/2,y+181)],[(x+w-cw-7,y+242),(x+cw+13,y+242)],[(x+cw/2,y+187),(x+cw/2,y+113)]]
  for i in range(count):
   j=(i+1)%count
   if rev[i]>.88 and rev[j]>.88:path(f,links[i],RUST,4,ease((t-max(cue[i],cue[j])-.33)/.6),True)
 elif kind=='paths':
  for i in range(min(n,2)):
   a=rev[i];yy=y+75+i*151;label(i,x,yy-50,31,w-25)
   pts=[(x+12,yy),(x+w-26,yy)] if i==0 else [(x+12,yy),(x+160,yy),(x+300,yy-25),(x+450,yy+16),(x+w-26,yy-17)]
   path(f,pts,fg if i==0 else RUST,4,a,True,marker=max(0,min(1,(t-cue[i]-.5)/max(1,s['end']-cue[i]-.6))) if a>.9 else None)
  if n>2:label(n-1,x,y+h-5,26,w)
 elif kind=='clock':
  a=rev[0] if rev else 0;asset(f,'P03',x+140,y+140,235,235,pr)
  if a>0:
   # Explicit six o'clock. No accidental five/two o'clock baked source dial.
   line(f,(x+140,y+140),(x+140,y+213),fg,6,a);line(f,(x+140,y+140),(x+140,y+45),fg,4,a);cv2.circle(f,(int(x+140),int(y+140)),7,RUST,-1,cv2.LINE_AA)
  label(0,x+310,y+45,88,w-310);label(1,x+310,y+180,33,w-310)
 elif kind=='evidence':
  prop='P02' if s['script_line'] in [75,98] else 'P04';asset(f,prop,x+140,y+140,225,245,pr)
  for i in range(n):label(i,x+300,y+i*124+13,33,w-310)
  if cur>=0:
   for j in range(3):line(f,(x+90,y+104+j*24),(x+183,y+104+j*24),RUST if j==2 else muted,3,ease((t-cue[cur]-.18-j*.10)/.45))
 elif kind=='affection':
  a=rev[0] if rev else 0;asset(f,'F04',x+135,y+140,250,230,.15*a);asset(f,'P05',x+135,y+145,210,220,a,scale=.82+.18*spring((t-cue[0])/.65) if n else 1)
  for i in range(n):label(i,x+300,y+25+i*128,34,w-305)
  if n>1 and rev[-1]>.1:
   a=rev[-1];asset(f,'P08',x+135+30*a,y+252,245,65,a,scale=.65+.35*a);line(f,(x+260,y+255),(x+480,y+255),RUST,4,a)
 elif kind=='warmth':
  # These are symbolic warmth states, not a quantitative relationship meter.
  frac=ease((t-cue[-1])/.75) if n>1 else ease(r/.8);first='P06' if s['script_line'] in [137,265] else 'P07';second='P07' if first=='P06' else 'P06'
  asset(f,first,x+150-8*frac,y+147,235,225,1-frac);asset(f,second,x+150+8*(1-frac),y+147,235,225,frac)
  for i in range(n):label(i,x+320,y+32+i*134,34,w-330)
 elif kind=='boundary':
  bx=x+215;line(f,(bx,y+10),(bx,y+h-6),RUST,6,pr);asset(f,'F02',bx,y+152,32,300,.09*pr)
  # A limit line stops an incoming pressure dot; an exit decision remains on our side.
  if cur>=0:
   u=ease((t-cue[cur])/.8);cv2.circle(f,(int(x+w-25-(w-265)*u),int(y+145)),10,fg,-1,cv2.LINE_AA)
  for i in range(n):label(i,x+260,y+i*min(86,h/max(n,1)),31,w-275)
 elif kind=='checklist':
  q=next((i for i,c in enumerate([247,249,251,253,256],1) if s['script_line']==c),None)
  if q:
   for i in range(5):cv2.circle(f,(int(x+28+i*67),int(y+18)),17,RUST if i+1==q else muted,3,cv2.LINE_AA)
  asset(f,'C08',x+120,y+190,145,225,pr)
  for i in range(n):label(i,x+260,y+79+i*105,33,w-270)

def scene_frame(i,t):
 s=scenes[i];r=t-s['start'];f=BG[s['dark']].copy();fg=WHITE if s['dark'] else INK;muted=(155,166,175) if s['dark'] else (110,118,123)
 text(f,'WHY WE BECOME',90,61,27,fg,430,weight='Black');text(f,f"{s['chapter']:02d} / {CH[s['chapter']-1].upper()}",1818,65,23,muted,1040,center=False) if False else None
 # Right aligned chapter without guessing text width.
 z=glyph(f"{s['chapter']:02d} / {CH[s['chapter']-1].upper()}",23,muted,1110);blit(f,z,1830-z.shape[1],65)
 line(f,(90,139),(1830,139),(40,47,52) if s['dark'] else (221,230,236),1)
 tx=100 if s['feature'] or s['layout']=='right' else 1030;tw=1720 if s['feature'] else 790;size=86 if s['feature'] else 82
 while glyph(s['title'],size,fg,tw,'Black').shape[0]>(205 if s['feature'] else 235) and size>54:size-=2
 text(f,s['title'],tx+(1-spring(r/.7))*28,214,size,fg,tw,alpha=ease(r/.4),weight='Black');line(f,(tx,202),(tx+115,202),RUST,5,ease((r-.1)/.65))
 reveal_art(f,s,t)
 dx=930 if s['feature'] else tx;diagram(f,s,t,dx,510,880 if s['feature'] else 790,310)
 # Captions occupy y~920-1000, separate from editorial artwork and diagrams.
 line(f,(90,1036),(1830,1036),(40,47,52) if s['dark'] else (221,230,236),2);line(f,(90,1036),(1830,1036),RUST,3,t/VO)
 return f
@functools.lru_cache(maxsize=1)
def endcard():
 a=cv2.imread(str(R/'assets/subscribe-end-card.jpeg'));h,w=a.shape[:2];k=min(W/w,H/h);a=cv2.resize(a,(round(w*k),round(h*k)));f=BG[False].copy();x=(W-a.shape[1])//2;y=(H-a.shape[0])//2;f[y:y+a.shape[0],x:x+a.shape[1]]=a;return f
# CPU implementations retain the equations and license from the MIT upstream GLSL.
def transition(fr,to,p,kind,dark=False):
 if kind=='directionalwipe':
  # direction=(1,0), center=.5, smoothness=.16; from/to order preserved.
  uv=np.linspace(0,1,W,dtype=np.float32);m=(1-smooth(-.16,0,uv-p*1.16))[None,:,None]
  return (fr*(1-m)+to*m).astype(np.uint8)
 if kind=='fadecolor':
  color=np.array(INK if dark else PAPER,dtype=np.float32);phase=.4
  a=fr*smooth(1-phase,0,p)+color*(1-smooth(1-phase,0,p));b=to*smooth(phase,1,p)+color*(1-smooth(phase,1,p));return (a*(1-p)+b*p).astype(np.uint8)
 return to

def frame(t):
 if t>=VO:
  p=ease((t-VO)/.4);return cv2.addWeighted(scene_frame(len(scenes)-1,VO-.01),1-p,endcard(),p,0) if p<1 else endcard().copy()
 i=max(0,bisect.bisect_right(starts,t)-1);f=scene_frame(i,t);r=t-starts[i]
 if i and r<.28 and scenes[i]['transition'] in ('directionalwipe','fadecolor'):
  prev=scene_frame(i-1,starts[i]-.001);f=transition(prev,f,r/.28,scenes[i]['transition'],scenes[i]['dark'])
 return f

def render(start,duration,out,captions=True):
 end=min(TOTAL,start+duration);n=round((end-start)*FPS);out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
 vf=f"subtitles=plans/captions.ass:fontsdir=fonts" if captions else 'null'
 # ASS runs on absolute video PTS, trim only after overlay for a QA segment.
 if start:vf=f"setpts=PTS+{start}/TB,"+vf+f",setpts=PTS-{start}/TB"
 audio='audio/final_mix.wav' if (R/'audio/final_mix.wav').exists() else 'audio/narration_master.wav'
 cmd=['ffmpeg','-y','-hide_banner','-loglevel','warning','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-ss',str(start),'-i',audio,'-map','0:v','-map','1:a','-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','18','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','apad','-t',str(n/FPS),'-movflags','+faststart',str(out)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE);t0=time.time()
 try:
  for j in range(n):
   p.stdin.write(frame(start+j/FPS).tobytes())
   if j%900==0:print(json.dumps({'frame':j,'frames':n,'seconds':round(time.time()-t0,1),'speed_fps':round((j+1)/max(.01,time.time()-t0),2)}),flush=True)
 finally:p.stdin.close()
 rc=p.wait();assert rc==0,rc;print(json.dumps({'output':str(out),'elapsed':time.time()-t0,'frames':n}),flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--start',type=float,default=0);ap.add_argument('--duration',type=float,default=TOTAL);ap.add_argument('--out',default='delivery/episode-v1.mp4');ap.add_argument('--still',type=float);ap.add_argument('--no-captions',action='store_true');a=ap.parse_args()
 if a.still is not None:cv2.imwrite(a.out,frame(a.still))
 else:render(a.start,a.duration,a.out,not a.no_captions)
