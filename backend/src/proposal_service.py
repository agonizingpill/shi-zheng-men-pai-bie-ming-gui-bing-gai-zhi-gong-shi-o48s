from .models import Entrance,Alias,Evidence,Proposal,Objection,Notice,Redirect
from .common import *
def pair(s,a,b):
 x=get(s,Entrance,a);y=get(s,Entrance,b)
 if a==b:fail('不能归并到自身')
 if x.street!=y.street or x.number!=y.number:fail('道路或门牌主号冲突，不得归并')
 if (x.sub or '')!=(y.sub or ''):fail('附号不一致：带附号入口按完整号码匹配，仅凭主号书证不能立案，请先补证')
 return x,y
def create(s,d):
 lock(s);pair(s,d['source_id'],d['target_id']);x=Proposal(**d);s.add(x);s.flush();return x
def object_to(s,d):
 lock(s);p=get(s,Proposal,d['proposal_id'])
 if p.state not in ['draft','public']:fail('只能在生效前提交异议')
 x=Objection(**d);s.add(x);s.flush();return x
def resolve(s,id,d):
 lock(s);x=get(s,Objection,id);p=get(s,Proposal,x.proposal_id)
 if x.state!='open' or p.state not in ['draft','public']:fail('异议已经处理或提案不可复核')
 x.state='resolved';x.decision=d['decision'];x.resolution=d['resolution']
 if x.decision=='split':
  p.state='rejected'
  for n in rows(s,Notice):
   if n.proposal_id==p.id:n.state='withdrawn'
 return x
# 附号更正与公示并发：错配提案退回复核；已生效公示不动，留原号可查
def send_back(s,id,d):
 lock(s);p=get(s,Proposal,id)
 if p.state not in ['draft','public']:fail('只可退回未生效提案')
 if any(x.state=='active' and x.proposal_id==p.id for x in rows(s,Redirect)):fail('公示已生效，保留原号可查，不再退回复核')
 p.state='review';p.review_reason=d['review_reason']
 for n in rows(s,Notice):
  if n.proposal_id==p.id and n.state=='public':n.state='withdrawn'
 return p
def resubmit(s,id,d):
 lock(s);p=get(s,Proposal,id)
 if p.state!='review':fail('只有退回复核的提案可重新提交')
 pair(s,p.source_id,p.target_id);p.state='draft';p.review_reason='';p.reason=d['reason'];return p
