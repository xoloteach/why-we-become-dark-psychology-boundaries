import pathlib,json,cv2,numpy as np,time
R=pathlib.Path(__file__).resolve().parents[1]; cv2.setNumThreads(2)
assert hasattr(cv2,'dnn_superres'),'opencv-contrib is required for FSRCNN reconstruction'
sr=cv2.dnn_superres.DnnSuperResImpl_create();sr.readModel(str(R/'assets/models/FSRCNN_x4.pb'));sr.setModel('fsrcnn',4)

for folder in ['assets/native','assets/layers','assets/kit','qa']:(R/folder).mkdir(parents=True,exist_ok=True)
report={}; inset=5
special={'S03':([(49,465),(481,897),(912,1326)],[(49,269),(283,504),(518,738)]),'S06':([(29,456),(475,902),(921,1348)],[(20,250),(269,501),(519,749)]),'S08':([(28,457),(469,908),(920,1348)],[(18,259),(271,505),(517,750)])}
omit={'S02_P01':'Generated pseudo-writing in memory cloud; clearer alternate available.','S05_P05':'Baked clock shows a different time from the six-o’clock example.','S06_P04':'Tiny baked wording; repeat pattern is explained with code-drawn nodes.','S07_P09':'Generated board lettering; alternate evidence panel selected.','S10_P02':'Secondary figure clipped by source-panel edge.','S16_P04':'Dense scribble crowding; alternate pressure panel is clearer.','S19_P09':'Unspecified plotted curves risk implying unsupported measurements.','S21_P01':'Spiked object is an unnecessarily aggressive metaphor.'}
notes=['S01: readable emotional poses; reserve subtitle lane in final composition.','S02: omit P01 pseudo-writing; remaining panels usable.','S03: remove outside header and each frame border using reviewed coordinates.','S04: blank bubbles and concern-deflection contrast usable.','S05: omit P05 wrong clock; draw exact six-o’clock example in code.','S06: reviewed framed-panel geometry; omit P04 tiny baked text.','S07: omit P09 generated lettering; evidence and acknowledgement panels usable.','S08: reviewed framed-panel geometry; character identity retained; secondary designs accepted.','S09: gift/debt metaphor and tension usable; ribbon stays connected in scene illustration.','S10: omit P02 clipped exiting person; other poses usable.','S11: ordinary-human, professional-assessment and blank-label imagery usable.','S12: concrete behavioral examples, shared-work and responsibility usable.','S13: accountability/apology/change/recurrence variants usable.','S14: calm limit, leave and return sequence usable.','S15: emotion/choice/autonomy contrast usable.','S16: omit P04 crowding scribbles; compassion and follow-through alternatives usable.','S17: disappointment/respect versus guilt contrast usable.','S18: friendship/romance/family/workplace examples usable.','S19: omit P09 unsupported wave plots; five questions use code labels.','S20: trusted support and safety imagery usable.','S21: omit P01 spiked prop; use remaining grounded/autonomy imagery.','K1: all nine full-body poses usable; pose swaps only, not a joint rig.','K2: nine distinct props usable; heart silhouettes differ, use crossfade rather than exact morph.','K3: six materials usable; bottom row empty, ignored; no alpha assumed.']
(R/'qa/source_art_review_prior.md').write_text('# Historical source-art notes — current validation pending\n\n'+'\n'.join('- '+x for x in notes)+'\n')
def matte(b,effect=False):
 edge=np.concatenate([b[:8].reshape(-1,3),b[-8:].reshape(-1,3),b[:,:8].reshape(-1,3),b[:,-8:].reshape(-1,3)])
 bg=np.median(edge,axis=0);delta=np.max(abs(b.astype(np.float32)-bg),axis=2)
 alpha=np.clip((delta-12)/37,0,1).astype(np.float32)
 if not effect:
  solid=(alpha>.42).astype(np.uint8)*255;cont,_=cv2.findContours(solid,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);inside=np.zeros_like(solid)
  for c in cont:
   if cv2.contourArea(c)>100:cv2.drawContours(inside,[c],-1,255,-1)
  alpha=np.maximum(alpha,cv2.GaussianBlur(inside,(3,3),.45)/255)
 n,l,stats,_=cv2.connectedComponentsWithStats((alpha>.1).astype(np.uint8),8)
 if not effect:
  for j in range(1,n):
   if stats[j,cv2.CC_STAT_AREA]<18:alpha[l==j]=0
 rgba=np.dstack([b,np.clip(alpha*255,0,255).astype(np.uint8)])
 yy,xx=np.where(alpha>.3);box=[max(0,int(xx.min())-5),max(0,int(yy.min())-5),min(b.shape[1],int(xx.max())+6),min(b.shape[0],int(yy.max())+6)] if len(xx) else [0,0,b.shape[1],b.shape[0]]
 return rgba,box
for i in range(1,25):
 code=f'S{i:02d}' if i<=21 else f'K{i-21}'
 im=cv2.imread(str(R/'assets/sheets'/f'{code}.jpg'));h,w=im.shape[:2];gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
 if code.startswith('S'):
  if code in special:xs,ys=special[code]
  else:
   cuts=[]
   for prof,size in [(gray.mean(0),w),(gray.mean(1),h)]:
    cs=[0]
    for frac in [1/3,2/3]:
     c=round(size*frac);rad=round(size*.035);lo=max(0,c-rad);hi=min(size,c+rad);cs.append(lo+int(np.argmin(prof[lo:hi])))
    cs.append(size);cuts.append(cs)
   xs=[(cuts[0][j],cuts[0][j+1]) for j in range(3)];ys=[(cuts[1][j],cuts[1][j+1]) for j in range(3)]
 else:xs=[(round(w*j/3),round(w*(j+1)/3)) for j in range(3)];ys=[(round(h*j/3),round(h*(j+1)/3)) for j in range(3)]
 for j in range(1,10):
  row,col=divmod(j-1,3);x0,x1=xs[col];y0,y1=ys[row];pad=5 if code.startswith('S') else 8
  a=im[y0+pad:y1-pad,x0+pad:x1-pad];ident=f'{code}_P{j:02d}' if code.startswith('S') else f'{"C" if code=="K1" else "P" if code=="K2" else "F"}{j:02d}'
  if code=='K3' and j>6:continue
  native=R/'assets/native'/f'{ident}.png';cv2.imwrite(str(native),a)
  b=sr.upsample(a);l=cv2.resize(a,(b.shape[1],b.shape[0]),interpolation=cv2.INTER_LANCZOS4);b=cv2.addWeighted(b,.78,l,.22,0);b=cv2.addWeighted(b,1.08,cv2.GaussianBlur(b,(0,0),.8),-.08,0)
  rgba,box=matte(b,code=='K3');target=R/('assets/layers' if code.startswith('S') else 'assets/kit')/f'{ident}.png';cv2.imwrite(str(target),rgba)
  report[ident]={'source_sheet':code,'cell':j,'native':list(a.shape[1::-1]),'upscaled':list(b.shape[1::-1]),'crop':[x0+pad,y0+pad,x1-pad,y1-pad],'bbox':box,'path':str(target.relative_to(R)),'reconstruction':'FSRCNN 4x with 22% Lanczos blend; restrained sharpening','status':'omit' if ident in omit else 'available','reason':omit.get(ident),'alpha':'matte extracted and enclosed pale interiors preserved' if code!='K3' else 'luma/alpha material extracted from paper'}
 print(code,'ready',flush=True)
(R/'assets/upscale_report.json').write_text(json.dumps(report,indent=2));(R/'assets/asset_manifest.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'panels':189,'omitted_before_timing':len(omit),'kit_assets':24}),flush=True)
