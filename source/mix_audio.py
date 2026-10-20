"""Restrained, cue-driven CC0 effects and an original quiet ambient bed.
No effects placed merely because there is an edit. All gains/events are auditable.
"""
from pathlib import Path
import json,subprocess,wave,math
import numpy as np
R=Path(__file__).resolve().parents[1];sr=48000;tl=json.loads((R/'plans/timeline.json').read_text());sc=json.loads((R/'plans/scene_plan.json').read_text());N=round(tl['total']*sr)
with wave.open(str(R/'audio/narration_master.wav')) as f:
 assert f.getsampwidth()==2 and f.getnchannels()==1;vo=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
mix=np.zeros((N,2),np.float32);mix[:len(vo)]=vo[:,None]
# 100 Hz speech-level envelope; no expensive full-rate convolution.
block=480;pad=np.pad(vo,(0,(-len(vo))%block));rms=np.sqrt(np.mean(pad.reshape(-1,block)**2,axis=1));duck=np.clip(.32/(1+12*rms),.13,.32)
# Quiet original score: long pentatonic pads, no suspense stings or manipulative horror cues.
# Rendered in one-second blocks to bound memory.
for sec in range(math.ceil(N/sr)):
 a=sec*sr;b=min(N,a+sr);t=np.arange(a,b,dtype=np.float64)/sr;env=np.minimum(np.clip(t/4,0,1),np.clip((tl['total']-t)/5,0,1));control=np.interp(t,np.arange(len(duck))*.01,duck,left=.32,right=.32)
 chord=int(sec//32)%4;freqs=[[130.813,195.998,261.626],[110,164.814,220],[87.307,130.813,174.614],[97.999,146.832,195.998]][chord];swell=(.5-.5*np.cos(2*np.pi*(t%32)/32))*.6+.4
 l=np.zeros(len(t));rr=np.zeros(len(t))
 for i,hz in enumerate(freqs):
  l+=(np.sin(2*np.pi*hz*t+.15*i)+.13*np.sin(2*np.pi*hz*2*t))*.0016/(i+1)
  rr+=(np.sin(2*np.pi*hz*t+.22*i)+.13*np.sin(2*np.pi*hz*2*t+.12))*.0016/(i+1)
 mix[a:b,0]+=l*env*control*swell;mix[a:b,1]+=rr*env*control*swell
# Meaningful accents only, with at least .7 s spacing. CC0 source preserved.
events=[]
def event(t,file,db,why):
 if any(abs(x['time']-t)<.7 for x in events):return
 events.append({'time':round(t,3),'file':file,'peak_dbfs':db,'purpose':why,'license':'CC0-1.0'})
for c in tl['chapters'][1:]:event(c['start'],'rpg-audio/bookFlip1.ogg',-31,'Soft paper chapter handoff')
for s in sc:
 if s['script_line'] in [97,98,160,276]:event(s['cues'][-1],'rpg-audio/bookOpen.ogg',-32,'Documenting or acknowledging observable evidence')
 if s['script_line'] in [114,135,230]:event(s['cues'][0],'interface-sounds/drop_002.ogg',-32,'A gift enters the explanatory foreground')
 if s['script_line'] in [137,140]:event(s['cues'][-1],'interface-sounds/minimize_003.ogg',-34,'Warmth state changes, without a horror sting')
 if s['script_line'] in [189,194,205,274,284,304,309]:event(s['cues'][-1],'rpg-audio/cloth2.ogg',-32,'A complete-body pose changes with an autonomous decision')
 if s['script_line'] in [247,249,251,253,256]:event(s['cues'][0],'interface-sounds/click_003.ogg',-30,'One of five reflection questions receives focus')
 if s['script_line'] in [73]:event(s['cues'][0],'interface-sounds/click_001.ogg',-32,'The six o’clock agreement appears')
cache={}
for e in events:
 name=e['file']
 if name not in cache:
  data=subprocess.check_output(['ffmpeg','-v','error','-i',str(R/'assets/sfx'/name),'-f','f32le','-ac','1','-ar',str(sr),'-']);s=np.frombuffer(data,np.float32).copy();s-=np.mean(s);s/=max(.00001,np.max(np.abs(s)));fade=min(len(s)//3,round(sr*.007));s[:fade]*=np.linspace(0,1,fade);s[-fade:]*=np.linspace(1,0,fade);cache[name]=s
 s=cache[name]*10**(e['peak_dbfs']/20);a=round(e['time']*sr);b=min(N,a+len(s));pan=-.12 if e['purpose'].startswith('Soft') else .12;mix[a:b,0]+=s[:b-a]*(1-pan);mix[a:b,1]+=s[:b-a]*(1+pan)
np.clip(mix,-.98,.98,out=mix)
with wave.open(str(R/'audio/mix_prenorm.wav'),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((mix*32767).astype(np.int16).tobytes())
(R/'plans/sfx_cues.json').write_text(json.dumps(sorted(events,key=lambda x:x['time']),indent=2));print('SFX events',len(events),flush=True)
cmd=['ffmpeg','-y','-hide_banner','-i',str(R/'audio/mix_prenorm.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-'];p=subprocess.run(cmd,capture_output=True,text=True);j=json.loads(p.stderr[p.stderr.rfind('{'):]);(R/'audio/mix_measurement.json').write_text(json.dumps(j,indent=2))
af=f"loudnorm=I=-16:TP=-1.5:LRA=7:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
subprocess.run(['ffmpeg','-y','-v','error','-i',str(R/'audio/mix_prenorm.wav'),'-af',af,'-ar','48000','-c:a','pcm_s16le',str(R/'audio/final_mix.wav')],check=True)
print('Final mix ready',flush=True)
