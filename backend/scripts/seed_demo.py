from src.database import Session,Base,engine
from src.models import *
from src.security import password_hash
from src.common import rows

def seed():
 Base.metadata.create_all(engine)
 with Session() as s:
  for role in ['operator','supervisor','viewer']:
   if not any(x.email==role+'@changqiao.local' for x in rows(s,User)):s.add(User(email=role+'@changqiao.local',password=password_hash('Address2026!'),role=role))
  if not s.get(Registry,1):s.add(Registry(id=1,now='2026-11-18T09:00:00'))
  if not any(x.code=='CQ-018-A' for x in rows(s,Entrance)):
   for code,num,label,lat in [('CQ-018-A',18,'长桥路18号正门',31.210),('CQ-018-B',18,'长桥路十八号旧门牌',31.2101),('CQ-081',81,'长桥路81号',31.211),('CQ-018-C',18,'长桥路18号南入口',31.2102)]:
    e=Entrance(code=code,street='长桥路',number=num,sub='',label=label,lat=lat,lng=121.48);s.add(e);s.flush();a=Alias(entrance_id=e.id,text=label);s.add(a);s.flush();s.add(Evidence(alias_id=a.id,reference='照片-'+code,description='2026年11月现场门牌照片与老地籍图位置核验说明'))
   s.flush();es=rows(s,Entrance);p=Proposal(code='P031',source_id=es[1].id,target_id=es[0].id,reason='历史十八号门牌与现18号正门同宗同入口');s.add(p);s.flush();s.add(Objection(proposal_id=p.id,code='Y031',note='住户认为旧门牌对应独立南入口，申请现场复核',state='open'))
  # 附号场景：老门牌把“十八号之一”简写成 18-1，旧档分不清正门与附号
  if not any(x.code=='CQ-018-D' for x in rows(s,Entrance)):
   gate=next(x for x in rows(s,Entrance) if x.code=='CQ-018-A')
   d_=Entrance(code='CQ-018-D',street='长桥路',number=18,sub='1',label='长桥路18号之一侧门',lat=31.2103,lng=121.48);s.add(d_);s.flush()
   for text in [d_.label,'长桥路18-1老门牌']:
    a=Alias(entrance_id=d_.id,text=text);s.add(a);s.flush();s.add(Evidence(alias_id=a.id,reference='照片-'+d_.code+'-'+str(a.id),description='附号侧门现场核验：老门牌18-1为18号之一简写，与18号正门不是同一入口'))
   # 旧档误把附号并入正门的错配提案，已退回复核，等待补证
   s.add(Proposal(code='P032',source_id=d_.id,target_id=gate.id,reason='旧档只写主号18号，未区分附号，误将侧门并入正门',state='review',review_reason='附号更正：18-1系18号之一，与正门完整号码不符，退回复核补证'))
  s.commit()
if __name__=='__main__':seed()
