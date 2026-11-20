import re,hashlib,json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import precision_score,recall_score
from sklearn.model_selection import train_test_split
NUM={'零':0,'〇':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
def cn_to_int(t):
 if t.isdigit():return int(t)
 if '十' in t:
  a,b=t.split('十');return (NUM.get(a,1) if a else 1)*10+(NUM.get(b,0) if b else 0)
 return int(''.join(str(NUM[x]) for x in t))
def number(text):
 m=re.search(r'([0-9零〇一二三四五六七八九十]+)(?:号|[-－])',text)
 if not m:return None
 return cn_to_int(m.group(1))
# 附号：十八号之一 / 18号附1 / 老门牌简写 18-1 都规范为阿拉伯数字串；无附号返回 ''
def sub_number(text):
 m=re.search(r'号?\s*(?:之|附|[-－])\s*([0-9零〇一二三四五六七八九十]+)(?![0-9])',text)
 return str(cn_to_int(m.group(1))) if m else ''
def normalize(text):
 n=number(text)
 if n is None:return text
 out=re.sub(r'([0-9零〇一二三四五六七八九十]+)号',f'{n}号',text)
 for pat in (r'号\s*之\s*([0-9零〇一二三四五六七八九十]+)',r'号\s*附\s*([0-9零〇一二三四五六七八九十]+)',r'号?\s*[-－]\s*([0-9零〇一二三四五六七八九十]+)'):
  m=re.search(pat,out)
  if m:
   out=out[:m.start()]+f'号之{cn_to_int(m.group(1))}'+out[m.end():];break
 return out
def full_key(text):return (number(text),sub_number(text))
# Simulated labelled historical alias pairs. Split before TFIDF fit/threshold selection.
def evaluation():
 pairs=[]
 for street in ['长桥路','青石街','河滨路','新民巷','榕树街','学府路','东湖路','西堤路','南苑街','北园街','柳岸路','梅花巷']:
  pairs.extend([(street+'18号',street+'十八号',1),(street+'18号南入口',street+'十八号南门',1),(street+'18号之一',street+'18-1',1),(street+'18号',street+'81号',0),(street+'18号',street+'19号',0),(street+'18号之一',street+'18号',0)])
 tr,te=train_test_split(list(range(len(pairs))),test_size=.25,stratify=[x[2] for x in pairs],random_state=42)
 vec=TfidfVectorizer(analyzer='char',ngram_range=(1,3));vec.fit([normalize(t) for i in tr for t in pairs[i][:2]])
 def pred(ids,threshold):
  out=[]
  for i in ids:
   a,b,_=pairs[i];v=vec.transform([normalize(a),normalize(b)]);sim=float((v[0]@v[1].T).toarray()[0,0]);out.append(int(full_key(a)==full_key(b) and sim>=threshold))
  return out
 threshold=max([.35,.45,.55,.65,.75],key=lambda z:(precision_score([pairs[i][2] for i in tr],pred(tr,z),zero_division=0)+recall_score([pairs[i][2] for i in tr],pred(tr,z),zero_division=0),z))
 y=[pairs[i][2] for i in te];pr=pred(te,threshold)
 return {'seed':42,'train_pairs':len(tr),'holdout_pairs':len(te),'train_ids':tr,'holdout_ids':te,'precision':precision_score(y,pr,zero_division=0),'recall':recall_score(y,pr,zero_division=0),'threshold':threshold,'label_source':'模拟历史别名对；不代表真实地址精度'}
def match(entrances,aliases):
 if len(entrances)<2 or len(aliases)<2:raise ValueError('至少两个入口和两个有文字的别名')
 texts=[normalize(a['text']) for a in aliases];vec=TfidfVectorizer(analyzer='char',ngram_range=(1,3));v=vec.fit_transform(texts);sim=(v@v.T).toarray();dist=np.clip(1-sim,0,2);np.fill_diagonal(dist,0)
 labels=AgglomerativeClustering(n_clusters=None,distance_threshold=.55,metric='precomputed',linkage='average').fit_predict(dist)
 eval=evaluation();candidates=[]
 for i,x in enumerate(entrances):
  for y in entrances[i+1:]:
   ix=[j for j,a in enumerate(aliases) if a['entrance_id']==x['id']];iy=[j for j,a in enumerate(aliases) if a['entrance_id']==y['id']]
   if not ix or not iy:continue
   score=float(max(sim[a,b] for a in ix for b in iy))
   if score<.2:continue
   same_street=x['street']==y['street'];same_number=x['number']==y['number'];same_sub=(x.get('sub') or '')==(y.get('sub') or '')
   # 完整号码（街道+主号+附号）相符才是可立案候选；只撞主号（含正门与附号相混）仅作待查线索
   full_match=same_street and same_number and same_sub
   candidates.append({'source_id':x['id'],'target_id':y['id'],'similarity':round(score,6),'conflict':int(not full_match),'kind':'match' if full_match else 'clue'})
 return {'algorithm':'字符TF-IDF+AgglomerativeClustering average linkage','source_sha256':hashlib.sha256(json.dumps([entrances,aliases],ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'evaluation':eval,'clusters':[{'alias_id':a['id'],'label':int(k)} for a,k in zip(aliases,labels)],'candidates':candidates}
