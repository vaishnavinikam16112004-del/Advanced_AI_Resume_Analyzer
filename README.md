# Advanced AI Resume Analyzer

A working Flask + SQLite project starter with all 12 requested modules: user registration/login, PDF/DOCX/TXT upload, resume scoring, strengths/weaknesses, ATS checklist, job-role matching, skill-gap suggestions, resume builder/print-to-PDF, cover-letter drafts, mock interview questions, application tracker, dashboard, history and score comparison.

## Run in Windows VS Code
1. Extract this ZIP and open the `Advanced_AI_Resume_Analyzer` folder in VS Code.
2. Open Terminal > New Terminal.
3. Run:
   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   python app.py
   ```
4. Open `http://127.0.0.1:5000` in Chrome/Edge and register an account.
5. Upload a text-based PDF, DOCX or TXT resume and explore the dashboard.

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again.

## Important project notes
- The scoring and matching engine is rule/keyword based. It is an educational estimate, not a certified ATS score or guarantee of employment.
- The cover-letter and interview generators use local templates/rules. No paid API key is required; connect an AI provider later only through secure server-side environment variables.
- Scanned image-only PDFs need OCR, not included here. Maximum upload size is 8 MB.
- Before public deployment, set a strong random `SECRET_KEY`, use persistent database storage, HTTPS, CSRF protection, rate limiting, backups and a data-retention/privacy policy. Do not commit passwords, API keys, `.env`, database files or private resumes.
