import re
SKILLS=['python','java','javascript','c++','sql','mysql','mongodb','html','css','react','node.js','express','flask','django','machine learning','deep learning','tensorflow','pytorch','pandas','numpy','power bi','tableau','aws','azure','docker','git','github','rest api','communication','problem solving','leadership','excel','linux','spring','data structures']
ROLE_SKILLS={'software developer':['java','python','javascript','sql','git','rest api','data structures','problem solving'],'full stack developer':['html','css','javascript','react','node.js','mongodb','sql','git'],'data analyst':['sql','excel','python','pandas','power bi','tableau'],'machine learning engineer':['python','machine learning','deep learning','tensorflow','pandas','numpy'],'python developer':['python','flask','django','sql','git','rest api'],'java developer':['java','sql','spring','rest api','git','data structures']}
def extract_text(path,ext):
 if ext=='txt': return open(path,encoding='utf-8',errors='ignore').read()
 if ext=='pdf':
  from pypdf import PdfReader
  return '\n'.join(p.extract_text() or '' for p in PdfReader(path).pages)
 if ext=='docx':
  from docx import Document
  d=Document(path); return '\n'.join(p.text for p in d.paragraphs)+'\n'+'\n'.join(cell.text for t in d.tables for row in t.rows for cell in row.cells)
 raise ValueError('Unsupported format')
def analyze_resume(t):
 x=t.lower(); skills=[s for s in SKILLS if s in x]; sections={'Contact information':bool(re.search(r'[\w.+-]+@[\w.-]+\.\w+',t)),'Education':'education' in x or 'college' in x or 'university' in x,'Experience':'experience' in x or 'internship' in x,'Projects':'project' in x,'Skills':'skill' in x,'Summary/objective':'summary' in x or 'objective' in x}; score=min(100,25+4*len(skills)+5*sum(sections.values())+(10 if len(t.split())>250 else 0)); strengths=[]; weaknesses=[]
 if skills: strengths.append(f'Detected {len(skills)} relevant skills.')
 for k,v in sections.items():
  if v: strengths.append(k+' section found.')
  else: weaknesses.append('Add or clearly label the '+k+' section.')
 if len(skills)<5:weaknesses.append('Add more job-relevant skills that you genuinely know.')
 if not re.search(r'\b(built|developed|created|improved|designed|implemented|managed|analyzed)\b',x):weaknesses.append('Use action verbs to describe your contributions.')
 if not re.search(r'\b\d+%|\b\d+\s+(users|projects|records|customers)\b',x):weaknesses.append('Add truthful measurable results where possible.')
 return {'score':score,'skills':skills,'sections':sections,'strengths':strengths,'weaknesses':weaknesses,'ats_tips':['Use a simple one-column layout.','Use standard headings.','Avoid tables, graphics and text in images for key details.','Tailor keywords to each job description.','Proofread spelling, dates and contact details.']}
def recommend_jobs(skills):
 have={s.lower() for s in skills}; out=[]
 for role,need in ROLE_SKILLS.items():
  matched=[s for s in need if s in have]; missing=[s for s in need if s not in have]; out.append({'role':role.title(),'match':round(len(matched)/len(need)*100),'matched':matched,'missing':missing})
 return sorted(out,key=lambda x:x['match'],reverse=True)
def skill_gap(skills,role):
 need=ROLE_SKILLS.get(role.lower(),ROLE_SKILLS['software developer']); have={s.lower() for s in skills}; return [{'skill':s,'suggestion':f'Learn {s} fundamentals and build a small practical project using it.'} for s in need if s not in have]
def generate_cover_letter(name,role,company,resume):
 skills=[s for s in SKILLS if s in resume.lower()]; return f'''Dear Hiring Manager,\n\nI am applying for the {role} position at {company}. This opportunity matches my career interests and my motivation to build useful technology solutions.\n\nThrough my studies and projects, I have developed knowledge of {', '.join(skills[:6]) if skills else 'technical concepts and problem solving'}. I enjoy learning, collaborating and solving problems. I would value the opportunity to contribute to your team while continuing to grow professionally.\n\nThank you for considering my application.\n\nSincerely,\n{name}'''
def interview_questions(text,role):
 found=[s for s in SKILLS if s in text.lower()]; return [f'Explain a project from your resume and the problem it solves.',f'Why do you want to work as a {role}?','What challenge did you face in a project and how did you solve it?','How do you test your code?','Describe how you learn a new technology.']+[f'Explain your practical experience with {s}.' for s in found[:6]]
