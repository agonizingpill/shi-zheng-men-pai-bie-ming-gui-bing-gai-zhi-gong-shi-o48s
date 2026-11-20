import os,time,pathlib,logging
import redis
from sqlalchemy import select
from .database import Session
from .models import MatchRun,Entrance,Alias,Candidate
from .common import lock,rows,dump
from .matching import match
q=redis.from_url(os.environ['REDIS_URL'],decode_responses=True)
while True:
 pathlib.Path('/artifacts/address-heartbeat').write_text(str(time.time()))
 item=q.blpop('address:matching',timeout=2)
 if not item:continue
 with Session() as s:
  lock(s);run=s.get(MatchRun,int(item[1]))
  if not run or run.state!='queued':continue
  try:
   result=match([dump(x) for x in rows(s,Entrance)],[dump(x) for x in rows(s,Alias)]);run.result=result
   # 重试不重复登记候选：同一来源-目标入口对全表只保留一条，沿用首次判定
   existing={(x.source_id,x.target_id) for x in rows(s,Candidate)}
   for d in result['candidates']:
    if (d['source_id'],d['target_id']) in existing:continue
    s.add(Candidate(run_id=run.id,**d));existing.add((d['source_id'],d['target_id']))
   run.state='ready'
  except Exception as e:run.state='failed';run.error=str(e)[:500];logging.exception('matching failed')
  s.commit()
