from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
import io, zipfile, requests as http
from collections import defaultdict

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

app = FastAPI()

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjpbXSwicXVhbGlmaWNhdGlvbnMiOltdLCJ3b3JrRXhwZXJpZW5jZSI6W10sIm1vYmlsZSI6Ijg3OTg5ODk4OTgiLCJwYXNzd29yZCI6Ijg3OTg5ODk4OTgiLCJuYW1lIjoiVXRpbGl0eSIsInBlcm1pc3Npb25Hcm91cE5hbWUiOiJVdGlsaXR5IiwiZW50aXR5R3JvdXAiOlt7Im5hbWUiOiJTYW5za2FyYW0gVW5pdmVyc2l0eSIsImVudGl0eVR5cGUiOiJ1bml2ZXJzaXR5IiwibG9nbyI6Imh0dHBzOi8vb2tpZWRva2llLWVycC1pbWFnZXMuczMuYXAtc291dGgtMS5hbWF6b25hd3MuY29tL1NVLzIwMjYvMDMvbG9nby8yYjI4OTk4ZTg5NTEzMmFlNzc2NS1TYW5za2FyYW1fVW5pdmVyc2l0eS1sb2dvLmpwZWciLCJxYWMiOiJTVSIsImRpc3BsYXlOYW1lIjoiU2Fuc2thcmFtIFVuaXZlcnNpdHkiLCJlbnRpdHlJZCI6IjY5Y2E1NTZiZTc4N2ZiMDAxMGZmYWIxZiJ9XSwiZW50aXR5IjoiNjljYTU1NmJlNzg3ZmIwMDEwZmZhYjFmIiwic2Vzc2lvbiI6IjIwMjYtMjcgT2RkIiwic3RhdHVzIjp0cnVlLCJfaWQiOiI2YjA2ZGUzYTMwNTM0ZjAwMGZkMWJiNGMiLCJ0b2tlblZlcnNpb24iOjIsImlhdCI6MTc5NTYxMjIxOH0.QMlZ7-HJ3ttGO8g9Su-L6_mU1z2B53_sKUL3dbJvDSY"
LOGO_URL = "https://okiedokie-erp-images.s3.ap-south-1.amazonaws.com/SU/2026/03/logo/2b28998e895132ae7765-Sanskaram_University-logo.jpeg"
API_BASE = "https://academic-api.odpay.in/api"

W, H = A4
ML = 15 * mm
MR = 15 * mm
LH = 7 * mm


def _line(c, x, y, w):
    c.line(x, y - 1 * mm, x + w, y - 1 * mm)


def _field(c, label, value, x, y, lw, fw):
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y, label)
    c.setFont("Helvetica", 9)
    c.drawString(x + lw, y, str(value))
    c.line(x + lw, y - 1 * mm, x + fw, y - 1 * mm)


def _chunks(lst, n=8):
    return ["   ".join(lst[i:i + n]) for i in range(0, len(lst), n)] or [""]


def build_pdf(g, logo_bytes, exam_date):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    fw = W - ML - MR
    addr = ("Sanskaram University Address: Patauda, Jhajjar, Haryana, 124108"
            "   Mobile: +91-7056999201, +91-7056999202"
            "   Email: info@sanskaramuniversity.ac.in")

    if logo_bytes:
        c.drawImage(ImageReader(io.BytesIO(logo_bytes)), ML, H - 27 * mm,
                    width=16 * mm, height=16 * mm, preserveAspectRatio=True, mask='auto')
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(W / 2 + 8 * mm, H - 15 * mm, "SANSKARAM UNIVERSITY, JHAJJAR")
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2 + 8 * mm, H - 21 * mm, "Established by Haryana Govt. Act No. 3 of 2024")
    c.setLineWidth(1.5)
    c.line(ML, H - 29 * mm, W - MR, H - 29 * mm)
    c.setLineWidth(0.5)
    c.line(ML, H - 30.5 * mm, W - MR, H - 30.5 * mm)
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(W / 2, H - 34 * mm, addr)
    c.setLineWidth(1)
    c.line(ML, H - 36 * mm, W - MR, H - 36 * mm)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W / 2, H - 43 * mm, "MEMO")

    y = H - 53 * mm
    lw = 42 * mm
    _field(c, "Date of Exam", exam_date, ML, y, lw, fw)
    y -= LH
    _field(c, "Name of the Program", g["course"], ML, y, lw, fw)
    y -= LH
    _field(c, "Course Name", g["subject"], ML, y, lw, fw)
    y -= LH
    _field(c, "Course Code", g["subjectCode"], ML, y, lw, fw)
    y -= LH
    _field(c, "Semester / Batch", g["batch"], ML, y, lw, fw)

    y -= 8 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(ML, y, "Roll No. of Students whose answer book have been dispatched")
    y -= 4 * mm
    rows = _chunks(sorted(g["present"]))
    for row in rows:
        c.setFont("Helvetica", 9)
        c.drawString(ML + 2 * mm, y, row)
        _line(c, ML, y, fw)
        y -= LH
    for _ in range(max(0, 5 - len(rows))):
        _line(c, ML, y, fw)
        y -= LH

    y -= 3 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(ML, y, "Total number of Students Present")
    c.setFont("Helvetica", 9)
    c.drawString(ML + 65 * mm, y, str(len(g["present"])))
    _line(c, ML + 65 * mm, y, fw - 65 * mm)

    y -= LH
    c.setFont("Helvetica-Bold", 9)
    c.drawString(ML, y, "Roll Number of Absentees")
    y -= 4 * mm
    abs_rows = _chunks(sorted(g["absent"]))
    for row in abs_rows:
        c.setFont("Helvetica", 9)
        c.drawString(ML + 2 * mm, y, row)
        _line(c, ML, y, fw)
        y -= LH
    for _ in range(max(0, 3 - len(abs_rows))):
        _line(c, ML, y, fw)
        y -= LH

    y -= 3 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(ML, y, "Total number of Students Absent")
    c.setFont("Helvetica", 9)
    c.drawString(ML + 65 * mm, y, str(len(g["absent"])))
    _line(c, ML + 65 * mm, y, fw - 65 * mm)

    y -= LH + 3 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(ML, y, "Roll Number of Unfair Means Cases")
    _line(c, ML + 65 * mm, y, fw - 65 * mm)
    y -= LH
    _line(c, ML, y, fw)
    y -= LH
    _line(c, ML, y, fw)
    y -= LH
    c.drawString(ML, y + 2 * mm, "Total Number of Unfair Means Cases")
    _line(c, ML + 65 * mm, y, fw - 65 * mm)

    sig_y = max(y - 20 * mm, 30 * mm)
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(W - MR, sig_y, "Signature")
    c.drawRightString(W - MR, sig_y - 6 * mm, "Center Superintendent")

    c.setLineWidth(1)
    c.line(ML, 20 * mm, W - MR, 20 * mm)
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(W / 2, 15 * mm, addr)

    c.save()
    buf.seek(0)
    return buf.read()


@app.get("/")
@app.get("/api/generate")
def generate(
    entity: str,
    session: str,
    examCalendar: str,
    examDate: str,
    examType: str = "regular",
    examDateDisplay: str = "23 November 2026",
):
    api_url = (
        f"{API_BASE}/list/examRegistration"
        f"?entity={entity}&session={session}&examType={examType}"
        f"&admitCardStatus=approved&examDate={examDate}&examCalendar={examCalendar}"
    )
    try:
        resp = http.get(api_url, headers={"Authorization": TOKEN}, timeout=30)
        registrations = resp.json()
        if not isinstance(registrations, list):
            return JSONResponse({"error": "ERP API error", "detail": registrations}, status_code=502)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=502)

    groups = defaultdict(lambda: {
        "present": [], "absent": [],
        "course": "", "stream": "", "subject": "", "subjectCode": "", "batch": ""
    })
    for r in registrations:
        key = (r["stream"], r["subjectName"])
        g = groups[key]
        g["course"] = r["course"]
        g["stream"] = r["stream"]
        g["subject"] = r["subjectName"]
        g["subjectCode"] = r["subjectCode"]
        g["batch"] = r.get("batch", "")
        att = r.get("examDetail", {}).get("attendanceValue", "absent")
        (g["present"] if att == "present" else g["absent"]).append(r["studentRegNo"])

    if not groups:
        return JSONResponse({"error": "No registrations found"}, status_code=404)

    try:
        logo_bytes = http.get(LOGO_URL, timeout=15).content
    except Exception:
        logo_bytes = None

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for (stream, _), g in sorted(groups.items()):
            pdf_bytes = build_pdf(g, logo_bytes, examDateDisplay)
            safe = stream.replace("/", "-").replace(" ", "_")[:60]
            zf.writestr(f"Memo_{safe}.pdf", pdf_bytes)

    zip_buf.seek(0)
    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="ExamMemos.zip"'}
    )
