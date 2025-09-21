import json
import os
import re
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend import database, models, jd_parser, resume_parser, relevance
from backend.database import engine, SessionLocal
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

models.Base.metadata.create_all(bind=engine)
database.create_initial_users()

app = FastAPI(title="Automated Resume Relevance Check System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(username: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

def get_admin_user(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return current_user

@app.post("/login/")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username, models.User.password == password).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return {"message": "Login successful", "role": user.role}

@app.post("/signup/")
def signup(username: str = Form(...), password: str = Form(...), email: str = Form(None), phone_number: str = Form(None), city: str = Form(None), state: str = Form(None), db: Session = Depends(get_db)):
    user_exists = db.query(models.User).filter(models.User.username == username).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # New: Password validation
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

    # New: Phone number validation
    if phone_number and not re.match(r'^\d{10}$', phone_number):
        raise HTTPException(status_code=400, detail="Phone number must be a 10-digit number without any special characters.")

    new_user = models.User(username=username, password=password, email=email, phone_number=phone_number, city=city, state=state, role="user")
    db.add(new_user)
    db.commit()
    return {"message": "User registered successfully", "username": username}

@app.post("/jobs/")
def create_job_endpoint(
    title: str = Form(...),
    must_have: str = Form(""),
    good_to_have: str = Form(""),
    qualifications: str = Form(""),
    branch_office: str = Form(None),
    state: str = Form(None),
    db: Session = Depends(get_db),
    user_data: models.User = Depends(get_admin_user)
):
    must = [s.strip() for s in must_have.split(",") if s.strip()]
    good = [s.strip() for s in good_to_have.split(",") if s.strip()]
    job = jd_parser.create_job(db, title=title, must_have=must, good_to_have=good, qualifications=qualifications, branch_office=branch_office, state=state)
    return {
        "id": job.id,
        "title": job.title,
        "must_have": must,
        "good_to_have": good
    }

@app.get("/jobs/")
def list_jobs(db: Session = Depends(get_db)):
    jobs = jd_parser.list_jobs(db)
    out = []
    for j in jobs:
        out.append({
            "id": j.id,
            "title": j.title,
            "must_have": json.loads(j.must_have or "[]"),
            "good_to_have": json.loads(j.good_to_have or "[]"),
            "branch_office": j.branch_office,
            "state": j.state
        })
    return out

@app.get("/profile/")
def get_user_profile(user_data: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_profile = {
        "username": user_data.username,
        "email": user_data.email,
        "phone_number": user_data.phone_number,
        "city": user_data.city,
        "state": user_data.state
    }
    return user_profile

@app.post("/upload_resume/")
async def upload_resume(
    job_id: int = Form(...),
    file: UploadFile = File(...),
    name: str = Form(None),
    email: str = Form(None),
    db: Session = Depends(get_db),
):
    # New: PDF size limit (2MB)
    if file.size > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds the 2MB limit.")

    job = jd_parser.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume_text, saved_path = await resume_parser.parse_resume_file(file)

    cand = db.query(models.Candidate).filter(models.Candidate.name == name, models.Candidate.email == email).first()
    if not cand:
        user = db.query(models.User).filter(models.User.username == name).first()
        cand = models.Candidate(
            name=name,
            email=email,
            resume_path=saved_path,
            resume_text=resume_text,
            city=user.city if user else None,
            state=user.state if user else None
        )
        db.add(cand)
        db.commit()
        db.refresh(cand)
    else:
        cand.resume_path = saved_path
        cand.resume_text = resume_text
        db.commit()
        db.refresh(cand)

    ev = relevance.final_evaluate(resume_text, job)
    
    llm_summary = None
    llm_feedback = None
    gemini_key = os.getenv("GEMINI_API_KEY")

    if gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            summary_prompt = (
                f"You are a resume analyzer. Job title: {job.title}. Overall score: {ev['score']}%. "
                f"Verdict: {ev['verdict']}. Missing skills: {', '.join(ev['missing_skills']) if ev['missing_skills'] else 'None'}. "
                f"Provide a short, one-paragraph summary of the candidate's fit for the job."
            )
            summary_response = await model.generate_content_async(summary_prompt)
            llm_summary = summary_response.text.strip()

            feedback_prompt = (
                f"You are a resume coach. Job title: {job.title}. Must-have skills: {json.loads(job.must_have)}. "
                f"Good-to-have: {json.loads(job.good_to_have)}. Candidate resume text: {resume_text[:4000]}.\n"
                f"Provide a short personalized improvement checklist (3-6 bullets) focusing on missing skills and how to show them."
            )
            feedback_response = await model.generate_content_async(feedback_prompt)
            llm_feedback = feedback_response.text.strip()
            
        except Exception as e:
            print(f"Gemini API call failed: {e}")
            pass

    evaluation = models.Evaluation(
        job_id=job.id,
        candidate_id=cand.id,
        score=ev["score"],
        verdict=ev["verdict"],
        hard_score=ev["hard_score"],
        semantic_score=ev["semantic_score"],
        missing_skills=json.dumps(ev["missing_skills"]),
        feedback=llm_feedback or ev["feedback"],
        summary=llm_summary or "No summary generated."
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return {
        "candidate_id": cand.id,
        "evaluation_id": evaluation.id,
        "score": ev["score"],
        "verdict": ev["verdict"],
        "hard_score": ev["hard_score"],
        "semantic_score": ev["semantic_score"],
        "missing_skills": ev["missing_skills"],
        "feedback": evaluation.feedback,
        "summary": evaluation.summary
    }

@app.get("/evaluations/")
def list_evaluations(db: Session = Depends(get_db), user_data: models.User = Depends(get_admin_user)):
    q = db.query(models.Evaluation)
    results = []
    for ev in q.order_by(models.Evaluation.created_at.desc()).all():
        cand = db.query(models.Candidate).filter(models.Candidate.id == ev.candidate_id).first()
        job = db.query(models.Job).filter(models.Job.id == ev.job_id).first()
        results.append({
            "evaluation_id": ev.id,
            "candidate_id": ev.candidate_id,
            "candidate_name": cand.name if cand else None,
            "job_title": job.title if job else None,
            "score": ev.score,
            "verdict": ev.verdict,
            "hard_score": ev.hard_score,
            "semantic_score": ev.semantic_score,
            "missing_skills": json.loads(ev.missing_skills or "[]"),
            "feedback": ev.feedback,
            "summary": ev.summary,
            "candidate_city": cand.city if cand else None,
            "candidate_state": cand.state if cand else None,
            "job_state": job.state if job else None,
            "job_city": job.branch_office if job else None,
            "created_at": ev.created_at.isoformat() if ev.created_at else None
        })
    return results

@app.get("/my_evaluations/")
def list_my_evaluations(db: Session = Depends(get_db), user_data: models.User = Depends(get_current_user)):
    q = db.query(models.Evaluation)
    results = []
    for ev in q.order_by(models.Evaluation.created_at.desc()).all():
        cand = db.query(models.Candidate).filter(models.Candidate.id == ev.candidate_id).first()
        job = db.query(models.Job).filter(models.Job.id == ev.job_id).first()
        if cand and cand.name == user_data.username:
            results.append({
                "evaluation_id": ev.id,
                "candidate_id": ev.candidate_id,
                "candidate_name": cand.name,
                "job_title": job.title if job else "",
                "score": ev.score,
                "verdict": ev.verdict,
                "hard_score": ev.hard_score,
                "semantic_score": ev.semantic_score,
                "missing_skills": json.loads(ev.missing_skills or "[]"),
                "feedback": ev.feedback,
                "summary": ev.summary,
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            })
    return results