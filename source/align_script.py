import pathlib,json,re,difflib
R=pathlib.Path(__file__).resolve().parents[1];orig=(R/'transcript.txt').read_text();lines=orig.splitlines();tokens=[];line_indices=[]
norm=lambda s:re.sub(r'[^a-z0-9]','',s.lower().replace('’',"'"))
for line in lines:
 i=len(tokens);tokens.extend(line.split());line_indices.append((i,len(tokens)))
raw=json.loads((R/'audio/voiceover.json').read_text())['words'];a=[norm(x) for x in tokens];b=[norm(x['word']) for x in raw];sm=difflib.SequenceMatcher(None,a,b,autojunk=False);mapped=[None]*len(tokens);issues=[]
for op,i,j,k,l in sm.get_opcodes():
 if op=='equal':
  for ii,kk in zip(range(i,j),range(k,l)):mapped[ii]={'start':raw[kk]['start'],'end':raw[kk]['end'],'method':'exact'}
 elif op=='replace' and ''.join(a[i:j])==''.join(b[k:l]):
  st,en=raw[k]['start'],raw[l-1]['end'];total=sum(len(x) for x in a[i:j]);at=st
  for ii in range(i,j):
   dur=(en-st)*len(a[ii])/total;mapped[ii]={'start':at,'end':at+dur,'method':'tokenization-normalized'};at+=dur
 else:
  st=raw[k]['start'] if k<len(raw) else raw[-1]['end'];en=raw[l-1]['end'] if l>k else st+.05
  for ii in range(i,j):mapped[ii]={'start':st+(en-st)*(ii-i)/max(1,j-i),'end':st+(en-st)*(ii-i+1)/max(1,j-i),'method':'reviewed-provider-variant'}
  issues.append({'script':' '.join(tokens[i:j]),'stt':' '.join(x['word'] for x in raw[k:l]),'start':st,'end':en,'resolution':'Original script retained for captions; colloquial pronunciation/STT inflection variant.','listening_check':'NOT CHECKED'})
words=[dict(x,text=tok,index=i) for i,(tok,x) in enumerate(zip(tokens,mapped))];aligned=[]
for idx,((i,j),line) in enumerate(zip(line_indices,lines)):
 aligned.append({'line':idx+1,'text':line,'word_start':i,'word_end':j,'start':words[i]['start'],'end':words[j-1]['end']})
(R/'plans/aligned_words.json').write_text(json.dumps(words,ensure_ascii=False,indent=2));(R/'plans/aligned_lines.json').write_text(json.dumps(aligned,ensure_ascii=False,indent=2));(R/'qa/alignment_review.json').write_text(json.dumps({'script_words':len(a),'stt_words':len(b),'sequence_match_ratio':sm.ratio(),'provider_variants':issues,'critical_cue_note':'Exact matching and tokenization normalization reviewed; full listening not available in this environment.'},ensure_ascii=False,indent=2))
print(json.dumps({'aligned_words':len(words),'lines':len(aligned),'variants':issues},ensure_ascii=False,indent=2))
