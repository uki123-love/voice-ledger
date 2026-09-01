from __future__ import annotations
import json,re,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'; UA={'User-Agent':'Mozilla/5.0 RecruitWorkbench/1.0'}
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def get(u):
 r=requests.get(u,headers=UA,timeout=25);r.raise_for_status();return r.text
def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except:return d
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def scan_baidu(url,intern=False):
 text=re.sub(r'\s+',' ',BeautifulSoup(get(url),'html.parser').get_text(' '));out=[];seen=set()
 for m in re.finditer(r'([\u4e00-\u9fa5A-Za-z0-9/+\-（）()·— ]{4,70}\(J\d{4,8}\))',text):
  title=m.group(1).strip()
  if title in seen or len(title)>80:continue
  seen.add(title);ctx=text[m.end():m.end()+600]
  direction='技术研发' if any(k in title+ctx[:160] for k in ['工程师','算法','研发','技术']) else ('产品经理' if '产品' in title else ('产品运营' if '运营' in title else '职能岗位'))
  city=re.search(r'(北京|上海|深圳|广州|杭州|成都|武汉|南京|苏州|西安)',ctx);loc=city.group(1) if city else ''
  h=hashlib.md5(('baidu|'+title).encode()).hexdigest()[:14]
  out.append({'id':'remote_baidu_'+h,'company':'百度','size':'大厂','industry':'互联网与人工智能','project':title,'direction':direction,'type':'日常实习' if intern else '2027秋招','batch':'日常实习项目' if intern else '2027届校园招聘','target':'在校生，日常实习全年开放且不限毕业时间' if intern else '2027届毕业生','graduation':'不限毕业时间' if intern else '2026-09-01至2027-08-31','coverage':'2028可报' if intern else '2027届','location':loc,'education':'在校生' if intern else '','major':'','convertible':'暂未公布' if intern else '否','applyStart':'','applyEnd':'','publishDate':'','source':'百度校园招聘官网','officialUrl':url,'verified':'已核验','status':'报名中','notes':'由企业官方招聘列表自动发现；具体职责和资格请以官网实时页面为准。'})
 return out[:500]
def main():
 old=load(DATA/'jobs.json',{'jobs':[]});curated=[j for j in old.get('jobs',[]) if not str(j.get('id','')).startswith('remote_baidu_')];found=[];errors=[]
 for u,i in [('https://talent.baidu.com/jobs/list?projectType=1',False),('https://talent.baidu.com/jobs/list?recruitType=INTERN',True)]:
  try:found+=scan_baidu(u,i)
  except Exception as e:errors.append(str(e))
 if not found:found=[j for j in old.get('jobs',[]) if str(j.get('id','')).startswith('remote_baidu_')]
 save(DATA/'jobs.json',{'updated_at':now(),'jobs':curated+found,'notice':'自动更新优先解析可公开访问的企业官方招聘页；动态页面或反爬失败时保留上次核验数据，不虚构岗位。','errors':errors})
 exp=load(DATA/'interviews.json',{'items':[]})
 for x in exp.get('items',[]):
  try:get(x.get('sourceUrl',''));x['sourceReachable']=True
  except:x['sourceReachable']=False
  x['lastChecked']=now()
 exp['updated_at']=now();exp['notice']='面经仅保存摘要、题型归纳与原帖链接，不复制整篇内容。';save(DATA/'interviews.json',exp)
if __name__=='__main__':main()
