from __future__ import annotations
import hashlib,json,re,sys,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
SOURCES=json.loads((ROOT/'sources.json').read_text(encoding='utf-8'))
OUT=ROOT/'data/jobs.json'
S=requests.Session();S.headers.update({'User-Agent':'Mozilla/5.0 (compatible; MathExamWorkbench2028/1.0)'})
TARGET=[r'2028届',r'2028年应届',r'2028年度应届',r'毕业时间[^。；\n]{0,30}2028']
MATH=[r'数学类',r'基础数学',r'计算数学',r'应用数学',r'概率论与数理统计',r'运筹学与控制论',r'统计学类',r'统计学',r'应用统计',r'学科教学.?数学',r'专业不限',r'不限专业']
RECRUIT=[r'招录',r'招考',r'招聘',r'选调',r'公务员',r'事业单位',r'人才引进',r'高校毕业生']
EXCLUDE=[r'社会招聘',r'博士后',r'仅限博士',r'要求博士']

def clean(s):return re.sub(r'\s+',' ',s or '').strip()
def get(url):
 r=S.get(url,timeout=20,allow_redirects=True);r.raise_for_status();r.encoding=r.apparent_encoding or r.encoding;return r.text,r.url
def text(html):
 s=BeautifulSoup(html,'html.parser')
 for t in s(['script','style','noscript']):t.decompose()
 return clean(s.get_text(' ',strip=True))
def hit(ps,s):return any(re.search(p,s,re.I) for p in ps)
def links(base,html):
 out=[];seen=set();s=BeautifulSoup(html,'html.parser')
 for a in s.find_all('a',href=True):
  t=clean(a.get_text(' ',strip=True));u=urljoin(base,a['href'])
  if len(t)>=4 and u.startswith('http') and hit(RECRUIT,t) and u not in seen:seen.add(u);out.append((t,u))
 return out[:150]
def same_domain(a,b):
 x=urlparse(a).netloc.split(':')[0];y=urlparse(b).netloc.split(':')[0];return x==y or x.endswith('.'+y) or y.endswith('.'+x)
def typ(s,default):
 for k,v in [('定向选调','定向选调'),('选调','普通选调'),('公务员','国考'),('辅导员','辅导员'),('教师','教师编'),('人才引进','人才引进'),('事业单位','事业单位')]:
  if k in s:return v
 return default
def date(s,labels):
 for lab in labels:
  m=re.search(lab+r'[^0-9]{0,12}(20\d{2})[年\-/\.](\d{1,2})[月\-/\.](\d{1,2})',s)
  if m:return f'{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'
 return ''
def rec(src,title,url,body):
 jid='real_'+hashlib.sha1(url.encode()).hexdigest()[:16]
 match='可以报名' if re.search(r'专业不限|不限专业',body) else '高度匹配' if hit(MATH[:-2],body) else '需要确认'
 return {'id':jid,'agency':title[:80],'jobName':'公告级候选（需核对职位表）','department':'','type':typ(body,src.get('type','其他编制岗位')),'region':'','year':'2028','batch':'','establishment':'','education':'硕士研究生（待核对）','degree':'硕士（待核对）','major':'官方页面命中数学/统计/专业不限关键词，需核对职位表','match':match,'freshReq':'官方页面明确出现2028届/2028年应届','coverage2028':'是','politics':'待确认','grassroots':'','hukou':'','age':'','studentLeader':'','awards':'','certs':'','count':'','applyStart':date(body,['报名开始','报名时间']),'applyEnd':date(body,['报名截止','截止时间']),'writtenDate':date(body,['笔试时间','笔试']),'interviewDate':date(body,['面试时间','面试']),'subjects':'','publishDate':date(body,['发布时间','发布日期']),'source':src['name'],'noticeTitle':title,'noticeUrl':url,'positionUrl':'','applyUrl':'','status':'报名中' if '报名中' in body else '待确认','notes':'自动采集自官方网页。具体专业代码、学历、应届身份及其他限制必须打开官方公告/职位表复核。','verified':False}
def scan(src):
 jobs=[]
 try:h,base=get(src['url'])
 except Exception as e:print('SOURCE_FAIL',src['name'],e,file=sys.stderr);return jobs
 for title,u in links(base,h):
  if not same_domain(base,u):continue
  try:ph,fu=get(u);body=text(ph)
  except Exception:continue
  if hit(TARGET,body) and hit(MATH,body) and not hit(EXCLUDE,body):jobs.append(rec(src,title,fu,body))
  time.sleep(.12)
 return jobs
def main():
 jobs=[]
 for src in SOURCES:print('Scanning',src['name']);jobs.extend(scan(src))
 ded={j['id']:j for j in jobs}
 payload={'updated_at':datetime.now(timezone.utc).isoformat(),'jobs':list(ded.values()),'notice':'仅收录官方页面明确出现2028届/2028年应届且命中数学/统计/专业不限关键词的候选记录；自动结果不替代资格审查。'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8');print('Wrote',len(ded),'records')
if __name__=='__main__':main()
