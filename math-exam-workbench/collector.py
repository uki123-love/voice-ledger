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
S=requests.Session();S.headers.update({'User-Agent':'Mozilla/5.0 (compatible; TeacherEstablishmentWorkbench2028/2.0)'})
TARGET=[r'2028届',r'2028年应届',r'2028年度应届',r'毕业时间[^。；\n]{0,30}2028']
MATH=[r'数学类',r'基础数学',r'计算数学',r'应用数学',r'概率论与数理统计',r'运筹学与控制论',r'统计学类',r'统计学',r'应用统计',r'学科教学.?数学',r'专业不限',r'不限专业']
RECRUIT=[r'公开招聘.{0,12}教师',r'招聘.{0,12}教师',r'教师招聘',r'教育系统.{0,12}招聘',r'公办中小学.{0,12}招聘',r'事业编制教师',r'在编教师']
TEACHER=[r'教师',r'教育系统',r'教育局',r'教育委员会',r'教委',r'公办中小学',r'学校']
ESTABLISHMENT=[r'事业编制',r'事业编制内',r'在编教师',r'纳入事业单位编制',r'正式事业编',r'事业单位编制人员']
EXCLUDE=[r'编外',r'劳务派遣',r'临聘',r'代课教师',r'购买服务',r'员额制',r'合同制教师',r'博士后',r'仅限博士',r'要求博士']
TITLE_EXCLUDE=[r'拟聘',r'公示',r'体检',r'面试公告',r'成绩',r'资格复审',r'补录',r'递补',r'考察']

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
 return '教师编'
def date(s,labels):
 for lab in labels:
  m=re.search(lab+r'[^0-9]{0,12}(20\d{2})[年\-/\.](\d{1,2})[月\-/\.](\d{1,2})',s)
  if m:return f'{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'
 return ''
def rec(src,title,url,body):
 jid='real_'+hashlib.sha1(url.encode()).hexdigest()[:16]
 match='可以报名' if re.search(r'专业不限|不限专业',body) else '高度匹配' if hit(MATH[:-2],body) else '需要确认'
 return {'id':jid,'agency':title[:80],'jobName':'数学教师编制岗位候选（需核对岗位表）','department':src.get('department','教育局/学校待核对'),'type':'教师编','region':src.get('region',''),'year':'2028','batch':'','establishment':'教师事业编制（官方正文已命中编制关键词）','education':'硕士研究生（待核对）','degree':'硕士（待核对）','major':'官方页面命中数学/统计/学科教学（数学）/专业不限关键词，需核对岗位表','match':match,'freshReq':'官方页面明确出现2028届/2028年应届','coverage2028':'是','politics':'待确认','grassroots':'','hukou':'','age':'','studentLeader':'','awards':'','certs':'教师资格证要求待核对','count':'','applyStart':date(body,['报名开始','报名时间']),'applyEnd':date(body,['报名截止','截止时间']),'writtenDate':date(body,['笔试时间','笔试']),'interviewDate':date(body,['面试时间','面试']),'subjects':'','publishDate':date(body,['发布时间','发布日期']),'source':src['name'],'noticeTitle':title,'noticeUrl':url,'positionUrl':'','applyUrl':'','status':'报名中' if '报名中' in body else '待确认','notes':'自动采集自教育局或政府官方网页，且正文明确命中教师与事业编制关键词。具体学校、专业代码、教师资格证、学历及其他限制必须打开官方公告/岗位表复核。','verified':False}
def scan(src):
 jobs=[]
 try:h,base=get(src['url'])
 except Exception as e:print('SOURCE_FAIL',src['name'],e,file=sys.stderr);return jobs
 for title,u in links(base,h):
  if not same_domain(base,u):continue
  try:ph,fu=get(u);body=text(ph)
  except Exception:continue
  if hit(TARGET,body) and hit(MATH,body) and hit(TEACHER,body) and hit(ESTABLISHMENT,body) and not hit(EXCLUDE,body) and not hit(TITLE_EXCLUDE,title):jobs.append(rec(src,title,fu,body))
  time.sleep(.12)
 return jobs
def main():
 jobs=[]
 for src in SOURCES:print('Scanning',src['name']);jobs.extend(scan(src))
 ded={j['id']:j for j in jobs}
 payload={'updated_at':datetime.now(timezone.utc).isoformat(),'jobs':list(ded.values()),'notice':'仅收录市级或区县级教育局/政府官网中，明确出现2028届、数学相关条件及教师事业编制关键词的候选记录；自动结果不替代教育局或学校资格审查。'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8');print('Wrote',len(ded),'records')
if __name__=='__main__':main()
