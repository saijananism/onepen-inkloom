# Inkloom AI

Intelligent brand governance before publication — Team ONEPEN.

Inkloom AI reviews marketing content before it goes live, combining deterministic brand-rule checks with Google Gemini semantic review. It gives every submission a compliance score, flags issues with explained fixes, manages a Creator → Reviewer → Admin approval workflow, and produces a downloadable PDF compliance report.

## Features

- Role-based access: Creator, Reviewer, Admin
- Content submission and automated guideline review (tone, claims, terminology, accessibility)
- Color-coded Compliance Score (0–100) based on finding severity
- Gemini AI semantic review and AI-safe rewrite suggestions
- Findings with severity, explanation, source, and suggested correction
- Approval workflow with high-severity gate and publishing control
- Reviewer priority alerts for high-risk submissions
- Downloadable PDF compliance report
- Full audit trail per submission
- Governance insights dashboard
- Brand knowledge base (guidelines and approved facts)

## Tech Stack

- Python, Streamlit
- SQLite
- Google Gemini (google-generativeai)
- fpdf2

## Run locally

1. Clone the repo:

git clone https://github.com/saijananism/onepen-inkloom.git
cd onepen-inkloom

2. Install dependencies:

pip install -r requirements.txt

3. Create a file at `.streamlit/secrets.toml` and add:

GEMINI_API_KEY = "your_gemini_api_key"

4. Run the app:

streamlit run app.py

## Demo logins

- Creator: creator / creator2026
- Reviewer: reviewer / reviewer2026
- Admin: admin / admin2026

## Live app

https://nd7weo2gkpc8ijm3cyorsd.streamlit.app/
