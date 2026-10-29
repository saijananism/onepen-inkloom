import streamlit as st
import google.generativeai as genai

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
import sqlite3, os, re, datetime, uuid

DB = "inkloom.db"
APP_PASSWORD = os.getenv("APP_PASSWORD", "onepen2026")

st.set_page_config(page_title="Inkloom AI", page_icon="🛡️", layout="wide")

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS guidelines(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT, rule TEXT, severity TEXT, suggestion TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS facts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim TEXT, approved_statement TEXT, source TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS submissions(
        id TEXT PRIMARY KEY, title TEXT, content_type TEXT, content TEXT,
        status TEXT, created_at TEXT, updated_at TEXT);
    CREATE TABLE IF NOT EXISTS findings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id TEXT, category TEXT, severity TEXT, excerpt TEXT,
        explanation TEXT, source TEXT, suggestion TEXT, status TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id TEXT, actor TEXT, action TEXT, details TEXT, created_at TEXT);
    """)
    if con.execute("SELECT COUNT(*) c FROM guidelines").fetchone()["c"] == 0:
        now = datetime.datetime.utcnow().isoformat()
        rules = [
            ("Tone", "Avoid absolute guarantees such as guarantee, 100%, risk-free or always.", "High",
             "Use evidence-based language such as 'designed to help'."),
            ("Claims", "Do not make product claims without an approved fact or source.", "High",
             "Link the claim to an approved fact or soften the statement."),
            ("Terminology", "Use 'Inkloom AI' rather than 'Inkloom' alone in the first mention.", "Medium",
             "Replace 'Inkloom' with 'Inkloom AI'."),
            ("Accessibility", "Meaningful images should have descriptive alt text.", "Medium",
             "Add descriptive alt text or mark the image as decorative."),
        ]
        for c, r, s, g in rules:
            con.execute("INSERT INTO guidelines(category,rule,severity,suggestion,created_at) VALUES(?,?,?,?,?)",
                        (c, r, s, g, now))
        con.execute("INSERT INTO facts(claim,approved_statement,source,created_at) VALUES(?,?,?,?)",
                    ("security",
                     "Inkloom AI uses industry-standard security controls to help protect customer data.",
                     "Approved Security FAQ v1.0", now))
    con.commit()
    con.close()

init_db()

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🛡️ Inkloom AI")
    st.caption("Intelligent brand governance before publication — Team ONEPEN")
    password = st.text_input("Enter access password", type="password")
    if st.button("Sign in"):
        if password == APP_PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.info("Demo password: onepen2026")
    st.stop()

tabs = st.tabs(["📝 Review content", "📚 Brand knowledge", "✅ Approvals", "📊 Insights"])

with tabs[0]:
    st.header("Review content before publication")
    title = st.text_input("Content title", "Spring campaign post")
    content_type = st.selectbox("Content type", ["Social post", "Email", "Web copy", "Document"])
    content = st.text_area("Paste content", height=200,
        value="Inkloom guarantees 100% security for all your brand assets. Our tool is risk-free and always accurate.")

    if st.button("Run brand-governance review", type="primary"):
        sid = str(uuid.uuid4())[:8]
        now = datetime.datetime.utcnow().isoformat()
        con = db()
        con.execute("INSERT INTO submissions(id,title,content_type,content,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                    (sid, title, content_type, content, "Under review", now, now))
        con.execute("INSERT INTO events(submission_id,actor,action,details,created_at) VALUES(?,?,?,?,?)",
                    (sid, "Creator", "Submitted content", title, now))

        count = 0
        for g in con.execute("SELECT * FROM guidelines").fetchall():
            rule = g["rule"].lower()
            hit = None

            if "absolute guarantees" in rule:
                words = ["guarantee", "guarantees", "100%", "risk-free", "always"]
                found = [w for w in words if w in content.lower()]
                if found:
                    hit = ", ".join(found)

            elif "product claims" in rule:
                if re.search(r"\b(guarantee|guarantees|best|number one|risk-free)\b", content, re.I):
                    hit = "Potential unsupported claim"

            elif "inkloom ai" in rule:
                if "Inkloom" in content and "Inkloom AI" not in content:
                    hit = "Uses Inkloom without AI"

            elif "alt text" in rule:
                if "image" in content.lower() and "alt text" not in content.lower():
                    hit = "Image mentioned without alt text"

            if hit:
                count += 1
                suggestion = g["suggestion"]
                if "guarantee" in hit:
                    suggestion = ("Replace with: Inkloom AI uses industry-standard security controls "
                                  "to help protect customer data.")
                con.execute("""INSERT INTO findings
                    (submission_id,category,severity,excerpt,explanation,source,suggestion,status,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                    (sid, g["category"], g["severity"], content[:180],
                     f"Flagged because: {hit}. Rule: {g['rule']}",
                     f"Brand guideline - {g['category']}", suggestion, "Open", now))

        con.execute("INSERT INTO events(submission_id,actor,action,details,created_at) VALUES(?,?,?,?,?)",
                    (sid, "Inkloom AI", "Review completed", f"{count} issue categories flagged", now))
        con.commit()
        con.close()
        st.session_state.last = sid
        st.success(f"Review complete. Submission ID: {sid}")

    if "last" in st.session_state:
        sid = st.session_state.last
        con = db()
        findings = con.execute("SELECT * FROM findings WHERE submission_id=?", (sid,)).fetchall()
        st.subheader("Findings")
        if not findings:
            st.success("No issues found.")
        for f in findings:
            with st.expander(f"[{f['severity']}] {f['category']}"):
                st.markdown(f"**Affected content:** {f['excerpt']}")
                st.markdown(f"**Why flagged:** {f['explanation']}")
                st.markdown(f"**Guideline:** {f['source']}")
                st.markdown(f"**Suggested correction:** {f['suggestion']}")
                decision = st.selectbox("Decision", ["Open", "Accepted", "Rejected", "Needs human review"], key=f"d{f['id']}")
                if st.button("Save decision", key=f"s{f['id']}"):
                    con.execute("UPDATE findings SET status=? WHERE id=?", (decision, f["id"]))
                    con.execute("INSERT INTO events(submission_id,actor,action,details,created_at) VALUES(?,?,?,?,?)",
                                (sid, "Creator", "Decision", f"{f['category']} - {decision}",
                                 datetime.datetime.utcnow().isoformat()))
                    con.commit()
                    st.rerun()
        con.close()

with tabs[1]:
    st.header("Brand knowledge base")
    left, right = st.columns(2)

    with left:
        st.subheader("Add guideline")
        with st.form("guideline"):
            category = st.selectbox("Category", ["Tone", "Claims", "Terminology", "Accessibility", "Visual"])
            rule = st.text_area("Rule")
            severity = st.selectbox("Severity", ["High", "Medium", "Low"])
            suggestion = st.text_area("Suggested correction")
            if st.form_submit_button("Add guideline") and rule:
                con = db()
                con.execute("INSERT INTO guidelines(category,rule,severity,suggestion,created_at) VALUES(?,?,?,?,?)",
                            (category, rule, severity, suggestion, datetime.datetime.utcnow().isoformat()))
                con.commit()
                con.close()
                st.success("Guideline added")

        st.subheader("Guidelines")
        for g in db().execute("SELECT * FROM guidelines ORDER BY id DESC").fetchall():
            st.markdown(f"**[{g['severity']}] {g['category']}** — {g['rule']}")

    with right:
        st.subheader("Add approved fact")
        with st.form("fact"):
            claim = st.text_input("Claim topic")
            approved = st.text_area("Approved statement")
            source = st.text_input("Approved source")
            if st.form_submit_button("Add fact") and claim and approved:
                con = db()
                con.execute("INSERT INTO facts(claim,approved_statement,source,created_at) VALUES(?,?,?,?)",
                            (claim, approved, source, datetime.datetime.utcnow().isoformat()))
                con.commit()
                con.close()
                st.success("Fact added")

        st.subheader("Approved facts")
        for f in db().execute("SELECT * FROM facts ORDER BY id DESC").fetchall():
            st.markdown(f"**{f['claim']}** — {f['approved_statement']}  \n_Source: {f['source']}_")

with tabs[2]:
    st.header("Approvals")
    con = db()
    submissions = con.execute("SELECT * FROM submissions ORDER BY created_at DESC").fetchall()

    if not submissions:
        st.info("No submissions yet.")

    for s in submissions:
        open_findings = con.execute(
            "SELECT COUNT(*) c FROM findings WHERE submission_id=? AND status='Open'",
            (s["id"],)).fetchone()["c"]
        high_risk = con.execute(
            "SELECT COUNT(*) c FROM findings WHERE submission_id=? AND status='Open' AND severity='High'",
            (s["id"],)).fetchone()["c"]

        with st.expander(f"{s['title']} — {s['status']} | Open: {open_findings} | High risk: {high_risk}"):
            st.markdown(s["content"])

            if high_risk > 0:
                st.warning("High-severity issues require human review.")

            a, b, c = st.columns(3)

            if a.button("Approve", key=f"a{s['id']}"):
                if high_risk > 0:
                    st.error("Resolve high-severity findings first.")
                else:
                    con.execute("UPDATE submissions SET status='Approved', updated_at=? WHERE id=?",
                                (datetime.datetime.utcnow().isoformat(), s["id"]))
                    con.execute("INSERT INTO events(submission_id,actor,action,details,created_at) VALUES(?,?,?,?,?)",
                                (s["id"], "Reviewer", "Approved", "Content approved",
                                 datetime.datetime.utcnow().isoformat()))
                    con.commit()
                    st.rerun()

            if b.button("Request changes", key=f"r{s['id']}"):
                con.execute("UPDATE submissions SET status='Changes requested', updated_at=? WHERE id=?",
                            (datetime.datetime.utcnow().isoformat(), s["id"]))
                con.execute("INSERT INTO events(submission_id,actor,action,details,created_at) VALUES(?,?,?,?,?)",
                            (s["id"], "Reviewer", "Changes requested", "Reviewer asked for revisions",
                             datetime.datetime.utcnow().isoformat()))
                con.commit()
                st.rerun()

            if c.button("Audit trail", key=f"t{s['id']}"):
                for e in con.execute("SELECT * FROM events WHERE submission_id=? ORDER BY created_at",
                                     (s["id"],)).fetchall():
                    st.markdown(f"- `{e['created_at'][:19]}` **{e['actor']}** — {e['action']}: {e['details']}")
    con.close()

with tabs[3]:
    st.header("Governance insights")
    con = db()
    total = con.execute("SELECT COUNT(*) c FROM submissions").fetchone()["c"]
    approved = con.execute("SELECT COUNT(*) c FROM submissions WHERE status='Approved'").fetchone()["c"]
    issues = con.execute("SELECT category, COUNT(*) c FROM findings GROUP BY category").fetchall()

    a, b, c = st.columns(3)
    a.metric("Content reviewed", total)
    b.metric("Approved", approved)
    c.metric("Approval rate", f"{(approved / total * 100):.0f}%" if total else "0%")

    if issues:
        st.bar_chart({i["category"]: i["c"] for i in issues})
    else:
        st.info("Run reviews to see insights.")
    con.close()
