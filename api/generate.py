from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import io, zipfile, json, requests
from collections import defaultdict

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

LOGO_URL = "https://okiedokie-erp-images.s3.ap-south-1.amazonaws.com/SU/2026/03/logo/2b28998e895132ae7765-Sanskaram_University-logo.jpeg"
API_BASE = "https://academic-api.odpay.in/api"

W, H = A4
MARGIN_L = 15 * mm
MARGIN_R = 15 * mm
LINE_H = 7 * mm


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


def build_pdf(group, logo_bytes, exam_date="23 November 2026"):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    fw = W - MARGIN_L - MARGIN_R

    # --- HEADER ---
    logo_img = ImageReader(io.BytesIO(logo_bytes))
    c.drawImage(logo_img, MARGIN_L, H - 27 * mm, width=16 * mm, height=16 * mm,
                preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(W / 2 + 8 * mm, H - 15 * mm, "SANSKARAM UNIVERSITY, JHAJJAR")
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2 + 8 * mm, H - 21 * mm, "Established by Haryana Govt. Act No. 3 of 2024")

    c.setLineWidth(1.5)
    c.line(MARGIN_L, H - 29 * mm, W - MARGIN_R, H - 29 * mm)
    c.setLineWidth(0.5)
    c.line(MARGIN_L, H - 30.5 * mm, W - MARGIN_R, H - 30.5 * mm)

    addr = ("Sanskaram University Address: Patauda, Jhajjar, Haryana, 124108"
            "   Mobile: +91-7056999201, +91-7056999202"
            "   Email: info@sanskaramuniversity.ac.in")
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(W / 2, H - 34 * mm, addr)

    c.setLineWidth(1)
    c.line(MARGIN_L, H - 36 * mm, W - MARGIN_R, H - 36 * mm)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W / 2, H - 43 * mm, "MEMO")

    # --- FIELDS ---
    y = H - 53 * mm
    lw = 42 * mm
    _field(c, "Date of Exam", exam_date, MARGIN_L, y, lw, fw)
    y -= LINE_H
    _field(c, "Name of the Program", group["course"], MARGIN_L, y, lw, fw)
    y -= LINE_H
    _field(c, "Course Name", group["subject"], MARGIN_L, y, lw, fw)
    y -= LINE_H
    _field(c, "Course Code", group["subjectCode"], MARGIN_L, y, lw, fw)
    y -= LINE_H
    _field(c, "Semester / Batch", group["batch"], MARGIN_L, y, lw, fw)

    # --- DISPATCHED ROLL NOS ---
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y, "Roll No. of Students whose answer book have been dispatched")
    y -= 4 * mm
    rows = _chunks(sorted(group["present"]))
    for row in rows:
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN_L + 2 * mm, y, row)
        _line(c, MARGIN_L, y, fw)
        y -= LINE_H
    for _ in range(max(0, 5 - len(rows))):
        _line(c, MARGIN_L, y, fw)
        y -= LINE_H

    # --- PRESENT COUNT ---
    y -= 3 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y, "Total number of Students Present")
    c.setFont("Helvetica", 9)
    c.drawString(MARGIN_L + 65 * mm, y, str(len(group["present"])))
    _line(c, MARGIN_L + 65 * mm, y, fw - 65 * mm)

    # --- ABSENTEES ---
    y -= LINE_H
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y, "Roll Number of Absentees")
    y -= 4 * mm
    abs_rows = _chunks(sorted(group["absent"]))
    for row in abs_rows:
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN_L + 2 * mm, y, row)
        _line(c, MARGIN_L, y, fw)
        y -= LINE_H
    for _ in range(max(0, 3 - len(abs_rows))):
        _line(c, MARGIN_L, y, fw)
        y -= LINE_H

    # --- ABSENT COUNT ---
    y -= 3 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y, "Total number of Students Absent")
    c.setFont("Helvetica", 9)
    c.drawString(MARGIN_L + 65 * mm, y, str(len(group["absent"])))
    _line(c, MARGIN_L + 65 * mm, y, fw - 65 * mm)

    # --- UNFAIR MEANS ---
    y -= LINE_H + 3 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y, "Roll Number of Unfair Means Cases")
    _line(c, MARGIN_L + 65 * mm, y, fw - 65 * mm)
    y -= LINE_H
    _line(c, MARGIN_L, y, fw)
    y -= LINE_H
    _line(c, MARGIN_L, y, fw)

    y -= LINE_H
    c.drawString(MARGIN_L, y + 2 * mm, "Total Number of Unfair Means Cases")
    _line(c, MARGIN_L + 65 * mm, y, fw - 65 * mm)

    # --- SIGNATURE ---
    sig_y = max(y - 20 * mm, 30 * mm)
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(W - MARGIN_R, sig_y, "Signature")
    c.drawRightString(W - MARGIN_R, sig_y - 6 * mm, "Center Superintendent")

    # --- FOOTER ---
    c.setLineWidth(1)
    c.line(MARGIN_L, 20 * mm, W - MARGIN_R, 20 * mm)
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(W / 2, 15 * mm, addr)

    c.save()
    buf.seek(0)
    return buf.read()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        def p(k):
            return params.get(k, [None])[0]

        entity = p("entity")
        session = p("session")
        exam_calendar = p("examCalendar")
        exam_type = p("examType") or "regular"
        exam_date_raw = p("examDate")
        exam_date_display = p("examDateDisplay") or "23 November 2026"

        token = self.headers.get("Authorization", "")

        if not all([entity, session, exam_calendar, exam_date_raw, token]):
            self._json(400, {"error": "Missing required params or Authorization header"})
            return

        # Fetch registrations
        api_url = (
            f"{API_BASE}/list/examRegistration"
            f"?entity={entity}&session={session}&examType={exam_type}"
            f"&admitCardStatus=approved&examDate={exam_date_raw}&examCalendar={exam_calendar}"
        )
        try:
            resp = requests.get(api_url, headers={"Authorization": token}, timeout=30)
            registrations = resp.json()
            if not isinstance(registrations, list):
                self._json(502, {"error": "ERP API error", "detail": registrations})
                return
        except Exception as e:
            self._json(502, {"error": str(e)})
            return

        # Group by stream+subject
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
            if att == "present":
                g["present"].append(r["studentRegNo"])
            else:
                g["absent"].append(r["studentRegNo"])

        if not groups:
            self._json(404, {"error": "No registrations found for given params"})
            return

        # Fetch logo once
        try:
            logo_bytes = requests.get(LOGO_URL, timeout=15).content
        except Exception:
            logo_bytes = None

        # Build zip in memory
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for (stream, _), g in sorted(groups.items()):
                pdf_bytes = build_pdf(g, logo_bytes, exam_date_display)
                safe = stream.replace("/", "-").replace(" ", "_")[:60]
                zf.writestr(f"Memo_{safe}.pdf", pdf_bytes)

        zip_data = zip_buf.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", 'attachment; filename="ExamMemos.zip"')
        self.send_header("Content-Length", str(len(zip_data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(zip_data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()

    def _json(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
