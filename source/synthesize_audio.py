"""Resume-safe Deepgram narration; each completed chunk is pushed before proceeding.
Usage: DEEPGRAM_API_KEY=<externally provided> python source/synthesize_audio.py
Requires ffmpeg/ffprobe and Git authentication. Never stores provider credentials.
"""
from pathlib import Path
import os,json,re,hashlib,urllib.request,urllib.error,subprocess,time
from checkpoint import checkpoint
R=Path(__file__).resolve().parents[1];A=R/'audio';A.mkdir(exist_ok=True)
key=os.environ['DEEPGRAM_API_KEY'];text=(R/'transcript.txt').read_text().strip();digest=hashlib.sha256(text.encode()).hexdigest()
chunks=[];cur=[]
for line in text.splitlines():
 if cur and len(' '.join(cur))+len(line)>1700:chunks.append('\n'.join(cur));cur=[]
 cur.append(line)
if cur:chunks.append('\n'.join(cur))
manifest={'script_sha256':digest,'model':'flux-cole-en','endpoint':'/v2/speak','chunks':[{'id':i,'text':s,'sha256':hashlib.sha256(s.encode()).hexdigest()} for i,s in enumerate(chunks)]}
(A/'synthesis_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def status(stage,**kw):
 p={'stage':stage,'model':'flux-cole-en','script_sha256':digest,**kw};(A/'status.json').write_text(json.dumps(p,indent=2)+'\n');print(json.dumps(p),flush=True)
def probe(path):
 return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],text=True))
status('synthesizing',chunks_total=len(chunks),chunks_completed=0);checkpoint('Checkpoint narration manifest before provider calls')
try:
 for i,s in enumerate(chunks):
  path=A/f'raw_{i:02}.mp3'
  if path.exists():probe(path)
  else:
   req=urllib.request.Request('https://api.deepgram.com/v2/speak?model=flux-cole-en&encoding=mp3',data=json.dumps({'text':s}).encode(),headers={'Authorization':'Token '+key,'Content-Type':'application/json'},method='POST')
   try:
    with urllib.request.urlopen(req,timeout=300) as response:
     data=response.read();ctype=response.headers.get('Content-Type','')
   except urllib.error.HTTPError as e:raise RuntimeError('Narration provider HTTP '+str(e.code)) from None
   if not ctype.startswith('audio/') or len(data)<1000:raise RuntimeError('Narration provider returned non-audio content')
   tmp=path.with_suffix('.tmp.mp3');tmp.write_bytes(data);probe(tmp);tmp.replace(path)
  status('synthesizing',chunks_total=len(chunks),chunks_completed=i+1)
  checkpoint(f'Back up original narration chunk {i+1}/{len(chunks)}')
 # Continuous raw stream; DSP and pause trimming precede timestamp alignment.
 concat=A/'concat.txt';concat.write_text(''.join(f"file 'raw_{i:02}.mp3'\n" for i in range(len(chunks))))
 af='highpass=f=80,equalizer=f=220:width_type=o:width=1.2:g=2.5,equalizer=f=3500:width_type=o:width=1.5:g=-2.2,equalizer=f=10000:width_type=o:width=1.0:g=1.8,acompressor=threshold=0.12:ratio=3.2:attack=15:release=220,silenceremove=stop_periods=-1:stop_duration=0.4:stop_threshold=-45dB,loudnorm=I=-16:LRA=11:TP=-1.0'
 subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-af',af,'-ar','48000','-ac','1','-c:a','pcm_s16le',str(A/'narration_master.wav')],check=True)
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(A/'narration_master.wav'),'-c:a','flac',str(A/'narration_master.flac')],check=True)
 duration=probe(A/'narration_master.wav');status('processed; alignment pending',duration_seconds=duration,chunks_total=len(chunks),chunks_completed=len(chunks),narration_flac_sha256=hashlib.sha256((A/'narration_master.flac').read_bytes()).hexdigest())
 checkpoint('Back up processed lossless narration before alignment')
 # Word timestamps refer to exactly the processed audio above.
 wav=(A/'narration_master.wav').read_bytes();req=urllib.request.Request('https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true&punctuate=true',data=wav,headers={'Authorization':'Token '+key,'Content-Type':'audio/wav'},method='POST')
 try:
  with urllib.request.urlopen(req,timeout=300) as response:raw=json.load(response)
 except urllib.error.HTTPError as e:raise RuntimeError('Alignment provider HTTP '+str(e.code)) from None
 words=raw['results']['channels'][0]['alternatives'][0]['words']
 if not words:raise RuntimeError('No alignment words returned')
 (A/'voiceover.json').write_text(json.dumps({'words':words,'duration_seconds':duration,'audio_sha256':hashlib.sha256(wav).hexdigest(),'model':'nova-3'},ensure_ascii=False,indent=2)+'\n')
 status('ready for script alignment',duration_seconds=duration,word_count=len(words),chunks_total=len(chunks),chunks_completed=len(chunks))
 checkpoint('Back up processed-audio word timestamp estimates')
except Exception as e:
 status('blocked',error=str(e),chunks_total=len(chunks),chunks_completed=len(list(A.glob('raw_*.mp3'))))
 checkpoint('Record blocked narration stage and preserve completed chunks')
 raise
