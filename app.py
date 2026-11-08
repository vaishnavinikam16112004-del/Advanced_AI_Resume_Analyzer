import os, re, json, sqlite3, secrets
from io import BytesIO
from datetime import datetime
from functools import wraps
from xml.sax.saxutils import escape
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from resume_utils import extract_text, analyze_resume, recommend_jobs, skill_gap, generate_cover_letter, interview_questions
app=Flask(__name__); app.secret_key=os.getenv('SECRET_KEY','change-this-secret-before-deployment'); DB=os.getenv('DATABASE_PATH','resume_analyzer.db'); os.makedirs('uploads',exist_ok=True)
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
 with db() as c:
  c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,password TEXT); CREATE TABLE IF NOT EXISTS analyses(id INTEGER PRIMARY KEY,user_id INTEGER,filename TEXT,resume_text TEXT,score INTEGER,result TEXT,created_at TEXT); CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY,user_id INTEGER,company TEXT,role TEXT,status TEXT,applied_date TEXT,notes TEXT);''')
init_db()
def login_required(f):
 @wraps(f)
 def w(*a,**k):
  if 'user_id' not in session: return redirect(url_for('login'))
  return f(*a,**k)
 return w
@app.route('/')
def home(): return redirect(url_for('dashboard')) if 'user_id' in session else render_template('home.html')
@app.route('/register',methods=['GET','POST'])
def register():
 if request.method=='POST':
  try:
   with db() as c: c.execute('INSERT INTO users(name,email,password) VALUES(?,?,?)',(request.form['name'],request.form['email'].lower(),generate_password_hash(request.form['password'])))
   flash('Account created. Please log in.'); return redirect(url_for('login'))
  except sqlite3.IntegrityError: flash('Email already registered.')
 return render_template('auth.html',mode='Register')
@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  with db() as c: u=c.execute('SELECT * FROM users WHERE email=?',(request.form['email'].lower(),)).fetchone()
  if u and check_password_hash(u['password'],request.form['password']): session.clear(); session['user_id']=u['id']; session['name']=u['name']; return redirect(url_for('dashboard'))
  flash('Invalid email or password.')
 return render_template('auth.html',mode='Login')
@app.route('/logout')
def logout(): session.clear(); return redirect('/')
@app.route('/dashboard')
@login_required
def dashboard():
 with db() as c:
  a=c.execute('SELECT * FROM analyses WHERE user_id=? ORDER BY id DESC LIMIT 5',(session['user_id'],)).fetchall(); apps=c.execute('SELECT * FROM applications WHERE user_id=? ORDER BY id DESC',(session['user_id'],)).fetchall(); total=c.execute('SELECT COUNT(*) n FROM analyses WHERE user_id=?',(session['user_id'],)).fetchone()['n']
 return render_template('dashboard.html',analyses=a,applications=apps,total=total)
@app.route('/analyze',methods=['GET','POST'])
@login_required
def analyze():
 if request.method=='POST':
  f=request.files.get('resume'); ext=f.filename.rsplit('.',1)[-1].lower() if f and f.filename else ''
  if ext not in {'pdf','docx','txt'}: flash('Choose a PDF, DOCX or TXT file.'); return redirect(url_for('analyze'))
  name=secure_filename(secrets.token_hex(4)+'_'+f.filename); path=os.path.join('uploads',name); f.save(path)
  try: text=extract_text(path,ext)
  except Exception as e: flash('Could not read file: '+str(e)); return redirect(url_for('analyze'))
  if len(text.strip())<50: flash('Not enough readable text. Try a text-based PDF or DOCX.'); return redirect(url_for('analyze'))
  result=analyze_resume(text)
  with db() as c: cur=c.execute('INSERT INTO analyses(user_id,filename,resume_text,score,result,created_at) VALUES(?,?,?,?,?,?)',(session['user_id'],f.filename,text,result['score'],json.dumps(result),datetime.now().strftime('%Y-%m-%d %H:%M'))); aid=cur.lastrowid
  return redirect(url_for('detail',aid=aid))
 return render_template('analyze.html')
def getrow(aid):
 with db() as c: return c.execute('SELECT * FROM analyses WHERE id=? AND user_id=?',(aid,session['user_id'])).fetchone()
@app.route('/analysis/<int:aid>')
@login_required
def detail(aid):
 r=getrow(aid)
 if not r:return redirect('/history')
 result=json.loads(r['result']); return render_template('analysis.html',row=r,result=result,jobs=recommend_jobs(result['skills']))
@app.route('/analysis/<int:aid>/download')
@login_required
def download_report(aid):
 r=getrow(aid)
 if not r:return redirect('/history')
 result=json.loads(r['result'])
 jobs=recommend_jobs(result['skills'])
 buffer=BytesIO()
 styles=getSampleStyleSheet()
 styles.add(ParagraphStyle(name='ReportTitle',parent=styles['Title'],textColor=colors.HexColor('#302a67'),fontSize=22,leading=28,alignment=0,spaceAfter=8))
 styles.add(ParagraphStyle(name='ReportSection',parent=styles['Heading2'],textColor=colors.HexColor('#5144c9'),fontSize=14,leading=18,spaceBefore=15,spaceAfter=7))
 styles.add(ParagraphStyle(name='ReportBody',parent=styles['BodyText'],textColor=colors.HexColor('#34415b'),fontSize=10,leading=15,spaceAfter=5))
 styles.add(ParagraphStyle(name='ReportMuted',parent=styles['BodyText'],textColor=colors.HexColor('#6b7891'),fontSize=9,leading=13))
 def paragraph_text(value):
  value=str(value).encode('cp1252','replace').decode('cp1252')
  value=re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',value)
  return escape(value)
 story=[
  Paragraph('Resume Analysis Report',styles['ReportTitle']),
  Paragraph(paragraph_text(r['filename']),styles['ReportBody']),
  Paragraph(f"Analyzed on {paragraph_text(r['created_at'])}",styles['ReportMuted']),
  Spacer(1,10),
 ]
 score_table=Table([[Paragraph('<b>Resume score</b>',styles['ReportBody']),Paragraph(f"<b>{int(result['score'])}/100</b>",styles['ReportTitle'])]],colWidths=[115*mm,45*mm])
 score_table.setStyle(TableStyle([
  ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f2f0ff')),
  ('BOX',(0,0),(-1,-1),0.7,colors.HexColor('#e1defe')),
  ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
  ('LEFTPADDING',(0,0),(-1,-1),12),
  ('TOPPADDING',(0,0),(-1,-1),12),
  ('BOTTOMPADDING',(0,0),(-1,-1),12),
 ]))
 story.extend([score_table,Paragraph('Educational estimate only; this is not a certified ATS result.',styles['ReportMuted'])])
 sections=[
  ('Detected skills',result.get('skills',[]),'No known skills detected.'),
  ('Strengths',result.get('strengths',[]),'No strengths were recorded.'),
  ('Improvement opportunities',result.get('weaknesses',[]),'No improvement notes were recorded.'),
  ('ATS checklist',result.get('ats_tips',[]),'No checklist items were recorded.'),
 ]
 for heading,items,empty_message in sections:
  story.append(Paragraph(heading,styles['ReportSection']))
  if items:
   story.extend(Paragraph(f'&bull; {paragraph_text(item)}',styles['ReportBody']) for item in items)
  else:
   story.append(Paragraph(empty_message,styles['ReportMuted']))
 story.append(Paragraph('Job role matches',styles['ReportSection']))
 for job in jobs[:5]:
  story.append(Paragraph(f"<b>{paragraph_text(job['role'])} - {int(job['match'])}% match</b>",styles['ReportBody']))
  story.append(Paragraph(f"Matched skills: {paragraph_text(', '.join(job['matched']) or 'None')}",styles['ReportMuted']))
  story.append(Paragraph(f"Skills to develop: {paragraph_text(', '.join(job['missing']) or 'None')}",styles['ReportMuted']))
 doc=SimpleDocTemplate(buffer,pagesize=A4,rightMargin=20*mm,leftMargin=20*mm,topMargin=18*mm,bottomMargin=18*mm,title='Resume Analysis Report')
 doc.build(story)
 buffer.seek(0)
 filename=secure_filename(r['filename']) or 'resume'
 stem=os.path.splitext(filename)[0]
 return send_file(buffer,mimetype='application/pdf',as_attachment=True,download_name=f'{stem}-analysis-report.pdf')
@app.route('/history')
@login_required
def history():
 with db() as c: rows=c.execute('SELECT * FROM analyses WHERE user_id=? ORDER BY id DESC',(session['user_id'],)).fetchall()
 return render_template('history.html',rows=rows)
@app.route('/tools',methods=['GET','POST'])
@login_required
def tools():
 out={}
 if request.method=='POST':
  role=request.form.get('role','Software Developer'); txt=request.form.get('resume_text',''); act=request.form.get('action')
  if act=='cover':out['cover']=generate_cover_letter(request.form.get('name','Candidate'),role,request.form.get('company','the company'),txt)
  if act=='interview':out['questions']=interview_questions(txt,role)
  if act=='gap':out['gap']=skill_gap([s.strip() for s in request.form.get('skills','').split(',')],role)
  out.update(role=role,text=txt)
 return render_template('tools.html',**out)
@app.route('/builder',methods=['GET','POST'])
@login_required
def builder():
 if request.method=='POST': return render_template('builder_preview.html',data={k:request.form.get(k,'') for k in ['name','email','phone','location','summary','education','skills','projects','experience']})
 return render_template('builder.html')
@app.route('/applications',methods=['GET','POST'])
@login_required
def applications():
 if request.method=='POST':
  with db() as c:c.execute('INSERT INTO applications(user_id,company,role,status,applied_date,notes) VALUES(?,?,?,?,?,?)',(session['user_id'],request.form['company'],request.form['role'],request.form['status'],request.form.get('applied_date',''),request.form.get('notes','')))
  flash('Application saved.'); return redirect(url_for('applications'))
 with db() as c: rows=c.execute('SELECT * FROM applications WHERE user_id=? ORDER BY id DESC',(session['user_id'],)).fetchall()
 return render_template('applications.html',rows=rows)
@app.route('/application/delete/<int:aid>',methods=['POST'])
@login_required
def delete_app(aid):
 with db() as c:c.execute('DELETE FROM applications WHERE id=? AND user_id=?',(aid,session['user_id']))
 return redirect('/applications')
@app.route('/compare')
@login_required
def compare():
 with db() as c: rows=c.execute('SELECT filename,score,created_at FROM analyses WHERE user_id=? ORDER BY id DESC LIMIT 2',(session['user_id'],)).fetchall()
 return render_template('compare.html',rows=rows)
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT',5000)),debug=True)
