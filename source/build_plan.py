import pathlib,json,re,hashlib,math
R=pathlib.Path(__file__).resolve().parents[1];lines=json.loads((R/'plans/aligned_lines.json').read_text());words=json.loads((R/'plans/aligned_words.json').read_text());audio=json.loads((R/'audio/status.json').read_text());VO=audio['duration_seconds'];TOTAL=math.ceil((VO+4)*30)/30
# start-line | illustration | headline | semantic engine | phrase=label (in spoken order)
rows='''1|S01_P01|The apology trap|chain|conversation=Conversation;apologizing=Apology
4|S01_P04|You raised a concern|focus|how something made you feel=Your feelings
5|S01_P05|The subject changed|chain|what happened=What happened;your attitude=Your attitude
7|S01_P07|Now you are the problem|stack|too sensitive=Too sensitive;misunderstood=You misunderstood;created problems=You create problems
10|S01_P08|You stop explaining|focus|stopped trying=Silence;exhausted=Exhaustion
14|S02_P02|Self-trust starts slipping|stack|memory=Memory;judgment=Judgment;right to feel upset=Your feelings
17|S02_P04|Responsibility reverses|chain|person who hurt you=You were hurt;make things right=You make it right
20|S02_P05|Not every conflict|focus|not every=Not every difficult conversation;manipulation=Is manipulation
24|S02_P06|Look for the pattern|loop|pattern=Repeated dismissal;feelings=Your feelings;boundaries=Your boundaries;mistakes=Your mistakes
29|S02_P08|Unequal responsibility|contrast|theirs=Their actions;responsibility=No accountability
30|S02_P09|Keeping the peace|focus|changing yourself=Becoming smaller;keep the peace=Keeping the peace
32|S03_P01|Manipulation or boundaries?|contrast|manipulation=Manipulation;healthy boundaries=Healthy boundaries
33|S03_P02|Recognize patterns|stack|gaslighting=Gaslighting;love-bombing=Love-bombing;controlling=Control
34|S03_P09|Understanding, not suspicion|contrast|every disagreement=Disagreement ≠ abuse;personality disorder=Difficult ≠ diagnosed
37|S03_P02|What should healthy feel like?|focus|suspicious=Not suspicion;healthy relationships=Understanding
39|S03_P03|Start with a concern|quote|didn't like=I did not like that
42|S03_P05|Uncomfortable can be healthy|focus|uncomfortable=Discomfort is possible
43|S03_P06|Two perspectives can exist|contrast|what they meant=Their meaning;your interpretation=Your interpretation
45|S03_P07|Both people have feelings|contrast|your words hurt them=Their feelings matter;both people=Both perspectives matter
48|S04_P01|A different response|focus|different response=Watch what follows
50|S04_P02|Deflecting the concern|quote|bad person=You make me the bad person;sensitive=You are too sensitive
52|S04_P03|Character replaces context|quote|remember everything wrong=You remember it wrong;grateful=You should be grateful
54|S04_P05|Where did the concern go?|chain|original problem=Original concern;defending your character=Defending yourself
56|S04_P04|Defending your right to feel|stack|ungrateful=Not ungrateful;too sensitive=Not too sensitive
58|S04_P07|Unresolved, again|focus|without addressing=The concern stays unresolved
59|S04_P08|Concern becomes defense|chain|brought up a concern=Raise a concern;defending yourself=Defend your character
63|S04_P09|Disagreeing is not surrender|contrast|healthy communication=Room to disagree;gaining control=Pressure to surrender
67|S05_P01|What is gaslighting?|focus|gaslighting=Look beyond the buzzword
69|S05_P02|Different memory is not proof|contrast|remembering=Different recollections;not every disagreement=Not automatic manipulation
71|S05_P03|A pattern that undermines reality|memory|denying=Denial alone is not proof;question their own=Self-trust is undermined
73|S05_P06|The six-o’clock agreement|clock|six=6:00;much later=Late arrival
75|S05_P08|The agreement is denied|evidence|never agreed=The agreement is disputed;clearly=You remember clearly
77|S06_P02|One incident is not proof|focus|imagining=Your memory is dismissed;doesn't prove=One incident ≠ proof
79|S06_P03|There may be ambiguity|contrast|unclear=Unclear messages;differently=Different recollections
81|S06_P05|Then it keeps happening|loop|keeps happening=Recurrence;deny=Denial;never happened=Erasure;memory is terrible=Undermining
85|S06_P06|Doubting your own reality|memory|question their behavior=You question behavior;wrong with your ability=You are made to doubt yourself
87|S06_P07|Silence replaces certainty|focus|keeping quiet=Speaking less;stop trusting=Trusting yourself less
89|S06_P08|Even when you were there|chain|asking them=Their version;you were there=Your own experience
91|S07_P01|The important distinction|contrast|disagrees=Different memory;repeated pattern=Repeated undermining
93|S07_P07|Repeated, not isolated|stack|denying=Denying;distorting=Distorting;undermining=Undermining
94|S07_P02|Step back and check|focus|don't assume=Do not assume;broader pattern=Look at the wider pattern
97|S07_P03|Document when safe|evidence|appropriate and safe=Only when appropriate and safe;keep track=Record important agreements
98|S07_P04|Clarify the agreement|evidence|Written messages=Written messages;actually agreed=What was agreed?
99|S07_P05|Can they acknowledge evidence?|focus|acknowledge evidence=Acknowledge evidence;remembered that differently=Correct a mistaken recollection
102|S07_P06|Can they admit a mistake?|contrast|mistaken=I was mistaken;distrust yourself=You cannot trust yourself
104|S07_P08|Honesty over perfect memory|stack|perfect memory=Not perfect memory;honesty=Honesty;accountability=Accountability
106|S08_P01|Love-bombing|focus|Love-bombing=Watch the pattern, not just intensity
109|S08_P02|Intense from the beginning|stack|unlike anyone=You are unlike anyone;message=Constant messages;everything=Everything about you
112|S08_P05|The future arrives early|chain|future=Future plans;promises=Enormous promises
114|S08_P04|It can feel incredible|affection|gifts=Gifts;incredible=Intense attention
118|S08_P06|Seen, wanted, understood|stack|seen=Seen;wanted=Wanted;understands=Understood
121|S08_P07|Intensity is not proof|focus|not automatically=Not automatically manipulation;expressive=People can be expressive
124|S08_P08|Fast is not always unhealthy|focus|without becoming unhealthy=Respect matters more than speed
125|S08_P09|Watch for pressure|stack|rush intimacy=Rush intimacy;bypass your boundaries=Bypass boundaries;obligation=Create obligation
126|S09_P01|I want to go slowly|boundary|take things slowly=Respect my pace
128|S09_P02|A limit meets guilt|quote|become upset=Your limit disappoints them;must not care=You must not care
131|S09_P03|Gifts become leverage|affection|everything they've done=Everything I did for you;need time=You should not need time
133|S09_P05|Your boundary becomes blame|boundary|boundary=Your limit;hurting them=Reframed as harm
135|S09_P07|A gift becomes a debt|affection|gift=A gift;debt=A debt
137|S10_P01|Warmth disappears|warmth|warmth disappears=Warmth withdraws;distant=Distance
140|S10_P04|Then affection returns|warmth|pulling away=You pull away;affection returns=Warmth returns
141|S10_P05|The promises return|stack|promises=Promises;apologies=Apologies;hoping=Hope
144|S10_P07|The push-pull is exhausting|loop|push and pull=Warmth;exhausting=Withdrawal;good moments=Chasing the good moments
147|S10_P06|Do not judge only the beginning|focus|beginning=Intensity at the beginning
149|S10_P08|Watch the response to no|boundary|say no=What happens when you say no?
150|S10_P09|Behavior should match promises|contrast|promises=What they promise;behavior=What they do
151|S10_P09|Genuine affection respects pace|paths|respect your pace=Your pace;doesn't need to rush=No pressure to surrender
154|S11_P01|Traits are not a diagnosis|contrast|traits=Narcissistic traits;narcissist=An online label
156|S11_P02|Use the term carefully|focus|not how=Do not diagnose from a label
157|S11_P03|Selfish sometimes is human|focus|particular situation=A particular behavior;without=Not a clinical diagnosis
158|S11_P04|Look beyond a few traits|stack|empathy=Empathy;defensive=Defensiveness;attention=Attention-seeking
159|S11_P06|Assessment needs a professional|focus|complex=Complex condition;qualified professional=Qualified professional
160|S11_P07|Observe what actually happens|evidence|few interactions=Not a few interactions;actually observe=Observable behavior
162|S12_P01|Expecting special treatment|focus|special treatment=Special treatment
164|S12_P02|Whose needs count?|contrast|your needs=Your needs;theirs=Their needs
165|S12_P03|Credit without responsibility|contrast|take credit=Claim the credit;avoid responsibility=Avoid responsibility
166|S12_P06|How is feedback received?|stack|humiliation=Humiliation;blame=Blame;retaliation=Retaliation
167|S12_P07|Other people matter equally|contrast|feelings=Feelings;needs=Needs;perspectives=Perspectives
169|S12_P08|One incident is not everything|focus|One incident=One incident is not the whole person;Everyone=Everyone can struggle
172|S13_P01|Look at the response to feedback|focus|pattern=The pattern;attention=What happens when it is raised?
174|S13_P02|Reflection without blame|chain|reflect=Reflect;apologize=Apologize;blaming you=Without blame
176|S13_P04|Does change follow?|focus|genuine effort=Genuine effort;change=Behavioral change
177|S13_P05|Or does blame return?|loop|address the problem=Raise the problem;argument=Another argument;real problem=You become the problem
178|S13_P09|No diagnosis required|focus|psychological label=No label required;unacceptable=You can reject harmful behavior
179|S13_P08|You can recognize hurt|focus|hurting you=Notice the impact;inside=Do not invent hidden motives
181|S14_P01|What a boundary means|focus|healthy boundaries=Your limits matter
182|S14_P02|A boundary is not control|stack|controlling=Not control;punish=Not punishment;demand=Not total compliance
185|S14_P04|Name what you will accept|boundary|willing to accept=What I will accept;what you will do=What I will do
187|S14_P05|A practical example|quote|willing to discuss=I am willing to discuss this;not willing=Not willing to be insulted
189|S14_P08|Pause, then return calmer|boundary|end this conversation=End this conversation;return to it=Return when calmer
190|S15_P01|Feelings are still allowed|contrast|not allowed=Not banning feelings;feel angry=Anger is allowed
194|S15_P02|You choose participation|boundary|not going to continue=I will not continue insults
195|S15_P03|They keep their perspective|stack|feelings=Their feelings;opinions=Their opinions;disagree=Their right to disagree
198|S15_P05|Your participation is your choice|paths|right to decide=Your right to decide;participate=What you participate in
199|S15_P06|Control dictates their choices|contrast|Control=Control;another person's choices=Their choices
201|S15_P07|A boundary clarifies yours|boundary|your own=Your own choices
202|S16_P01|Following through is the hard part|focus|hardest part=Not just saying it;following through=Following through
205|S16_P02|A limit without an exit|boundary|won't continue=I will not continue;remain=But you stay
207|S16_P03|Time to think|quote|time to think=I need time;pressuring=Repeated pressure
209|S16_P06|Relief can hide the pattern|focus|won't accept=A limit you intended;conflict disappears=Relief is not repair
211|S16_P07|Difficulty is not weakness|focus|not=Not weakness;care about=Care and dependence can complicate limits
213|S16_P08|Know your own limits|focus|limits=Your limits;values=Your values
214|S16_P09|Choose values over pressure|paths|decisions=Your decisions;immediate pressure=Not immediate pressure
215|S17_P01|Healthy does not mean perfect|stack|disappoint=Disappointment;misunderstand=Misunderstanding;mistakes=Mistakes
220|S17_P02|Repair without self-abandonment|contrast|nobody ever gets upset=Not conflict-free;abandon themselves=Not self-abandonment
222|S17_P03|I cannot help today|quote|can't help=I cannot help today;exhausted=I am exhausted
224|S17_P04|Disappointment is allowed|focus|disappointment=They may feel disappointed;available=They may wish you were available
226|S17_P05|Respecting the answer|chain|another day=Another day?;respect your answer=Your no still stands
228|S17_P07|Guilt changes the dynamic|quote|little I matter=I guess I do not matter
230|S17_P08|The history becomes leverage|affection|everything I've done=After everything I did for you
232|S18_P01|The feeling is not the issue|focus|disappointed=Disappointment itself is allowed
234|S18_P02|Pressure is the issue|chain|guilty=Guilt;decision=Surrendering your decision
235|S18_P03|It can happen anywhere|stack|friendships=Friendships;romantic relationships=Romantic relationships;families=Families;workplaces=Workplaces
236|S18_P07|Intentions may be unclear|contrast|intentionally=Intentional;learned=Learned patterns
238|S18_P08|Respond to the behavior|focus|intentions=You need not prove intent;behavior=Respond to behavior
239|S18_P09|Acknowledge, do not absorb|contrast|acknowledge=Acknowledge their feelings;responsibility=Do not carry every feeling
241|S18_P04|Care does not mean agreement|contrast|care=You can care;without agreeing=You can still decline
243|S18_P05|Love can coexist with a limit|focus|love=You can love someone;not healthy=And recognize an unhealthy dynamic
245|S19_P01|Five questions to ask yourself|checklist|ordinary=Ordinary conflict or a pattern?;few questions=Five questions
247|S19_P02|Can you safely say no?|checklist|say no=1 / Can you say no?;punished=Without repeated punishment or pressure
249|S19_P03|Can you raise a concern?|checklist|express a concern=2 / Can you express concerns?;attack=Without a character attack
251|S19_P04|Can they acknowledge impact?|checklist|acknowledge the impact=3 / Can they acknowledge impact?;intend=Even without harmful intent
253|S19_P05|Do apologies lead to change?|checklist|meaningful changes=4 / Do apologies lead to change?;same actions=Or do the same actions return?
256|S19_P07|Are you free to be yourself?|checklist|free=5 / Do you have independence?;friendships=Opinions, friendships and interests
258|S19_P08|Has your world become smaller?|paths|world smaller=Your world becomes smaller;afraid=To avoid their reaction
260|S19_P01|No single answer is proof|focus|No single answer=No single answer proves manipulation;repeated patterns=Look at repeated patterns
262|S19_P08|Pay attention to the impact|stack|afraid=Afraid;isolated=Isolated;guilty=Constantly guilty;judgment=Unable to trust yourself
263|S20_P01|Do not blame yourself|focus|recognize yourself=If this feels familiar;blame yourself=Do not blame yourself
265|S20_P02|Good and painful can coexist|warmth|genuine affection=Genuine affection;dismissive=Hurtful behavior
269|S20_P03|An apology can coexist with recurrence|contrast|apologize sincerely=A sincere apology;repeat=Repeated behavior
271|S20_P03|Confusion is understandable|memory|good parts=The good parts;painful parts=The painful parts;foolish=Confusion is not foolishness
274|S20_P04|You do not have to confront now|boundary|confront=No immediate confrontation required;take time=Take time to think
276|S20_P05|Talk to someone you trust|evidence|someone you trust=Trusted support
277|S20_P06|Write down what is happening|evidence|Write down=Document the pattern
278|S20_P07|Safety comes first|focus|unsafe=If you feel unsafe;prioritize your safety=Prioritize safety;support=Seek appropriate support
279|S21_P02|You do not need to win|focus|win every argument=No need to win every argument;force someone=No forced confession required
282|S21_P02|Ask a more useful question|quote|make this person understand=How do I make them understand?
284|S21_P06|What protects your well-being?|boundary|protect my well-being=What protects my well-being?;continues=If the behavior continues
286|S21_P03|Not manipulation in return|focus|manipulate people back=Not a lesson in retaliation
287|S21_P07|Not endless suspicion|memory|every message=Not every message;hidden meanings=Not every disagreement
290|S21_P03|Room for both people|contrast|both people=Both people have room;one person's=Not one person's control
292|S21_P06|Boundaries make room for honesty|chain|don't eliminate conflict=Conflict can still exist;honesty=Honesty has room
294|S21_P04|Closeness without ownership|paths|independence=Independence;closeness without ownership=Closeness without ownership
296|S21_P05|Nobody has to become smaller|contrast|grow=Both people grow;smaller=Nobody has to shrink
299|S21_P09|Pause before blaming yourself|focus|question your feelings=Pause;you're the problem=Do not assume you are the problem
301|S07_P01|Look at the pattern|stack|pattern=The pattern;responsibility=Responsibility;boundary=The response to a boundary
304|S21_P06|Compassion has limits|boundary|compassionate=Compassion;endlessly available=Not endless availability
306|S21_P07|Forgiveness is not erasure|contrast|forgive=You can forgive;pretending nothing happened=Without erasing what happened
307|S21_P02|Understanding is not acceptance|contrast|understand=Understand why;without accepting=Choose what you accept
309|S21_P04|Care without unlimited access|boundary|care deeply=Care deeply;unlimited access=Not unlimited access
311|S21_P09|Keep your trust in yourself|focus|trusting yourself=Your self-trust;comfortable=Not the price of their comfort
313|S21_P08|Room to speak, disagree and say no|stack|speak=Speak;disagree=Disagree;say no=Say no
316|S21_P09|Room to be yourself|focus|be yourself=Be yourself;fearing=Without constant fear
318|S21_P09|Think deeper. Live better. Become more.|stack|Think deeper=Think deeper;Live better=Live better;Become more=Become more
'''
chapter_starts=[1,32,67,106,154,181,215,245,263,279];chapters=['The apology trap','Conflict or control?','Gaslighting','Love-bombing','Traits, not diagnoses','Boundaries versus control','Disappointment or pressure?','Five questions','Compassion and safety','Room to be yourself']
records=[]
for raw in rows.strip().splitlines():
 no,art,title,kind,labs=raw.split('|');no=int(no);records.append({'line':no,'art':art,'title':title,'kind':kind,'labs':[p.split('=',1) for p in labs.split(';')]})
assert all(a['line']<=b['line'] for a,b in zip(records,records[1:])); norm=lambda s:re.sub(r'[^a-z0-9]','',s.lower().replace('’',"'"));ws=[norm(w['text']) for w in words]
scenes=[];missing=[];assetplan=[]
for i,r in enumerate(records):
 st=lines[r['line']-1]['start'];en=lines[records[i+1]['line']-1]['start'] if i+1<len(records) else VO
 # Two different actions inside the long boundary sentence use its exact spoken subphrase.
 if i and st==scenes[-1]['start']:
  query=['end','this','conversation'];a=lines[r['line']-1]['word_start'];b=lines[r['line']-1]['word_end'];hits=[j for j in range(a,b-len(query)+1) if ws[j:j+len(query)]==query];st=words[hits[0]]['start'];scenes[-1]['end']=st
 a=lines[r['line']-1]['word_start'];b=lines[records[i+1]['line']-1]['word_start'] if i+1<len(records) else len(words)
 cue=[];labels=[]
 for phrase,label in r['labs']:
  q=[norm(x) for x in phrase.split()];hits=[j for j in range(a,max(a,b-len(q)+1)) if ws[j:j+len(q)]==q]
  if hits:
   ti=words[hits[0]]['start']
   if st<=ti<en:cue.append(ti);labels.append(label)
   else:missing.append({'scene':i,'phrase':phrase,'reason':'outside scene; withheld'})
  else:missing.append({'scene':i,'phrase':phrase,'reason':'no exact cue; withheld'})
 ch=max(j+1 for j,x in enumerate(chapter_starts) if r['line']>=x);feat=r['kind'] in ('clock','boundary','affection','warmth','evidence','checklist')
 dark=r['line'] in [24,67,125,144,172,199,245,278,284,311,316]
 kit={'boundary':['C04','C05','F05'],'clock':['P03','F02'],'affection':['P05','P08','F04'],'warmth':['P06','P07','F04'],'evidence':['P02' if r['line'] in [75,98] else 'P04','C07','F01'],'checklist':['C08','F01']}.get(r['kind'],[])
 transition='directionalwipe' if r['line'] in chapter_starts[1:] else ('fadecolor' if i and dark!=scenes[-1]['dark'] else 'ink-reveal')
 s={'id':i,'start':st,'end':en,'art':r['art'],'kind':r['kind'],'title':r['title'],'labels':labels,'cues':cue,'dark':dark,'layout':'right' if (i//2)%2==0 else 'left','chapter':ch,'feature':feat,'phrase':' '.join(x['text'] for x in lines[r['line']-1:(records[i+1]['line']-1 if i+1<len(records) else len(lines))]),'script_line':r['line'],'kit':kit,'transition':transition}
 scenes.append(s);assetplan.append({'scene':i,'spoken_phrase':s['phrase'],'asset_ids':[r['art']]+kit,'roles':{'illustration':'one connected layer; no artificial body cuts','kit':'independent foreground props/pose swaps','graphics':'code-drawn semantic explanation'},'semantic_action':r['kind'],'trigger':st,'peak':min(st+.75,en-.1),'settle':min(st+1.1,en-.05),'label_cues':list(zip(labels,cue)),'pivots':'full-body feet for pose swaps; prop center for pop and ribbon stretch; no unsupported joints','next_transition':transition})
for i in range(len(scenes)-1):scenes[i]['end']=scenes[i+1]['start']
assert all(s['end']>s['start'] for s in scenes)
(R/'plans/scene_plan.json').write_text(json.dumps(scenes,ensure_ascii=False,indent=2));(R/'plans/motion_plan.json').write_text(json.dumps(assetplan,ensure_ascii=False,indent=2));(R/'qa/cue_exceptions.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2))
ch=[{'chapter':i+1,'title':title,'start':lines[line-1]['start']} for i,(line,title) in enumerate(zip(chapter_starts,chapters))];tl={'vo_end':VO,'total':TOTAL,'fps':30,'chapters':ch,'audio_sha256':hashlib.sha256((R/'audio/narration_master.wav').read_bytes()).hexdigest(),'source_commit':'24482a17b033efb8c7bffadc4691e8519e446c96'}
(R/'plans/timeline.json').write_text(json.dumps(tl,indent=2));review='# Panel-by-panel narration synchronization\n\n| Scene | Panel | Start | End | Meaning | Labels/cues |\n|---|---|---:|---:|---|---|\n'
for s in scenes:review+=f"| {s['id']:03d} | {s['art']} | {s['start']:.3f} | {s['end']:.3f} | {s['kind']}: {s['title']} | "+'; '.join(f'{l} @ {c:.3f}' for l,c in zip(s['labels'],s['cues']))+' |\n'
(R/'delivery/panel_sync_review.md').write_text(review)
# Source words remain untouched. Caption display uses the supplied words, not STT paraphrases.
def ass_time(t):
 cs=round(t*100);return f'{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}'
head='''[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Montserrat ExtraBold,56,&H00FFFFFF,&H00FFFFFF,&H0016150F,&H80000000,-1,0,0,0,100,100,0,0,1,4,1.3,2,130,130,84,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'''
groups=[];cur=[]
for i,w in enumerate(words):
 cur.append(w)
 endmark=w['text'].endswith(('.', '?','!','.”','?”'))
 if len(cur)>=6 or (len(cur)>=3 and endmark) or i==len(words)-1:groups.append(cur);cur=[]
sub=head;srt='';si=0
for g in groups:
 st=g[0]['start'];en=max(st+.12,g[-1]['end']);
 for j,w in enumerate(g):
  a=max(st,w['start']);b=g[j+1]['start'] if j+1<len(g) else en
  if b<=a:continue
  txt=' '.join(('{\\c&H003C62C8&}'+x['text']+'{\\c&H00FFFFFF&}') if k==j else x['text'] for k,x in enumerate(g))
  sub+=f'Dialogue: 0,{ass_time(a)},{ass_time(b)},Default,,0,0,0,,{txt}\n'
 si+=1
 def srttime(t):
  ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
 srt+=f'{si}\n{srttime(st)} --> {srttime(en)}\n'+ ' '.join(x['text'] for x in g)+'\n\n'
(R/'plans/captions.ass').write_text(sub);(R/'delivery/captions.srt').write_text(srt)
seo=(R/'delivery/seo-draft.md').read_text();chap='\n'.join(f"- {int(c['start'])//60:02d}:{int(c['start'])%60:02d} {c['title']}" for c in ch);seo=re.sub(r'## Chapters.*?\n## Search phrases','## Chapters\n'+chap+'\n\n## Search phrases',seo,flags=re.S);(R/'delivery/seo.md').write_text(seo)
print(json.dumps({'scenes':len(scenes),'duration_seconds':VO,'total_seconds':TOTAL,'used_panel_ids':len(set(s['art'] for s in scenes)),'cue_exceptions':missing,'min_scene_seconds':min(s['end']-s['start'] for s in scenes)},indent=2))
