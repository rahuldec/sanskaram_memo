import json, os
from collections import defaultdict
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

LOGO = "/private/tmp/claude-501/-Users-rahulsharma-Downloads/b758f585-9a28-4142-a4e7-8e1331a8036c/scratchpad/su_logo.jpeg"
OUT_DIR = "/Users/rahulsharma/Downloads/ExamMemos_Nov23_2026"
os.makedirs(OUT_DIR, exist_ok=True)

with open('/private/tmp/claude-501/-Users-rahulsharma-Downloads/b758f585-9a28-4142-a4e7-8e1331a8036c/scratchpad/examReg.json') as f:
    data = json.load(f)

# Group by (stream, subjectName)
groups = defaultdict(lambda: {
    'present': [], 'absent': [],
    'course': '', 'stream': '', 'subject': '', 'subjectCode': '', 'batch': ''
})
for r in data:
    key = (r['stream'], r['subjectName'])
    att = r.get('examDetail', {}).get('attendanceValue', 'absent')
    g = groups[key]
    g['course'] = r['course']
    g['stream'] = r['stream']
    g['subject'] = r['subjectName']
    g['subjectCode'] = r['subjectCode']
    g['batch'] = r.get('batch', '')
    if att == 'present':
        g['present'].append(r['studentRegNo'])
    else:
        g['absent'].append(r['studentRegNo'])

W, H = A4
MARGIN_L = 15*mm
MARGIN_R = 15*mm
LINE_H = 7*mm

def draw_field_line(c, label, value, x, y, label_w, total_w):
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y, label)
    c.setFont("Helvetica", 9)
    c.drawString(x + label_w, y, value)
    c.line(x + label_w, y - 1*mm, x + total_w, y - 1*mm)

def draw_line(c, x, y, w):
    c.line(x, y - 1*mm, x + w, y - 1*mm)

def chunk_roll_numbers(rolls, cols=6):
    """Split roll numbers into rows of `cols` per line."""
    rows = []
    for i in range(0, len(rolls), cols):
        rows.append("   ".join(rolls[i:i+cols]))
    return rows

def generate_memo(group, exam_date="23 November 2026"):
    stream = group['stream']
    course = group['course']
    subject = group['subject']
    sub_code = group['subjectCode']
    batch = group['batch']
    present = sorted(group['present'])
    absent = sorted(group['absent'])

    safe_name = stream.replace('/', '-').replace(' ', '_')[:60]
    filepath = os.path.join(OUT_DIR, f"Memo_{safe_name}.pdf")

    c = canvas.Canvas(filepath, pagesize=A4)
    c.setTitle(f"Exam Memo - {stream}")

    # --- HEADER ---
    # Logo: sits entirely above the double divider line (top ~12mm, height 16mm → bottom at 28mm from top)
    logo = ImageReader(LOGO)
    c.drawImage(logo, MARGIN_L, H - 27*mm, width=16*mm, height=16*mm, preserveAspectRatio=True, mask='auto')

    # University name — centred in the space to the right of the logo
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(W/2 + 8*mm, H - 15*mm, "SANSKARAM UNIVERSITY, JHAJJAR")
    c.setFont("Helvetica", 9)
    c.drawCentredString(W/2 + 8*mm, H - 21*mm, "Established by Haryana Govt. Act No. 3 of 2024")

    # Double divider — below the logo and title block
    c.setLineWidth(1.5)
    c.line(MARGIN_L, H - 29*mm, W - MARGIN_R, H - 29*mm)
    c.setLineWidth(0.5)
    c.line(MARGIN_L, H - 30.5*mm, W - MARGIN_R, H - 30.5*mm)

    # Contact info — below the double divider
    addr = "Sanskaram University Address: Patauda, Jhajjar, Haryana, 124108   Mobile: +91-7056999201, +91-7056999202   Email: info@sanskaramuniversity.ac.in"
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(W/2, H - 34*mm, addr)

    # Single separator below contact
    c.setLineWidth(1)
    c.line(MARGIN_L, H - 36*mm, W - MARGIN_R, H - 36*mm)

    # MEMO title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W/2, H - 43*mm, "MEMO")

    # --- FIELDS ---
    y = H - 53*mm
    fw = W - MARGIN_L - MARGIN_R  # full usable width
    lw = 42*mm  # label width

    draw_field_line(c, "Date of Exam", exam_date, MARGIN_L, y, lw, fw)
    y -= LINE_H
    draw_field_line(c, "Name of the Program", course, MARGIN_L, y, lw, fw)
    y -= LINE_H
    draw_field_line(c, "Course Name", subject, MARGIN_L, y, lw, fw)
    y -= LINE_H
    draw_field_line(c, "Course Code", sub_code, MARGIN_L, y, lw, fw)
    y -= LINE_H
    draw_field_line(c, "Semester / Batch", batch, MARGIN_L, y, lw, fw)

    # --- DISPATCHED ROLL NUMBERS ---
    y -= 8*mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y, "Roll No. of Students whose answer book have been dispatched")
    y -= 4*mm

    present_rows = chunk_roll_numbers(present, cols=8)
    if not present_rows:
        present_rows = [""]
    for row_text in present_rows:
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN_L + 2*mm, y, row_text)
        draw_line(c, MARGIN_L, y, fw)
        y -= LINE_H

    # pad to at least 5 lines total
    drawn = len(present_rows)
    for _ in range(max(0, 5 - drawn)):
        draw_line(c, MARGIN_L, y, fw)
        y -= LINE_H

    # --- PRESENT COUNT ---
    y -= 3*mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y, "Total number of Students Present")
    c.setFont("Helvetica", 9)
    c.drawString(MARGIN_L + 65*mm, y, str(len(present)))
    draw_line(c, MARGIN_L + 65*mm, y, fw - 65*mm)

    # --- ABSENTEES ---
    y -= LINE_H
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y, "Roll Number of Absentees")
    y -= 4*mm

    absent_rows = chunk_roll_numbers(absent, cols=8)
    if not absent_rows:
        absent_rows = [""]
    for row_text in absent_rows:
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN_L + 2*mm, y, row_text)
        draw_line(c, MARGIN_L, y, fw)
        y -= LINE_H

    for _ in range(max(0, 3 - len(absent_rows))):
        draw_line(c, MARGIN_L, y, fw)
        y -= LINE_H

    # --- ABSENT COUNT ---
    y -= 3*mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y, "Total number of Students Absent")
    c.setFont("Helvetica", 9)
    c.drawString(MARGIN_L + 65*mm, y, str(len(absent)))
    draw_line(c, MARGIN_L + 65*mm, y, fw - 65*mm)

    # --- UNFAIR MEANS ---
    y -= LINE_H + 3*mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y, "Roll Number of Unfair Means Cases")
    draw_line(c, MARGIN_L + 65*mm, y, fw - 65*mm)
    y -= LINE_H
    draw_line(c, MARGIN_L, y, fw)
    y -= LINE_H
    draw_line(c, MARGIN_L, y, fw)

    # Label drawn 5pt above its underline so text and line don't collide
    y -= LINE_H
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN_L, y + 2*mm, "Total Number of Unfair Means Cases")
    draw_line(c, MARGIN_L + 65*mm, y, fw - 65*mm)

    # --- SIGNATURE ---
    sig_y = max(y - 20*mm, 30*mm)
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(W - MARGIN_R, sig_y, "Signature")
    c.drawRightString(W - MARGIN_R, sig_y - 6*mm, "Center Superintendent")

    # --- FOOTER ---
    c.setLineWidth(1)
    c.line(MARGIN_L, 20*mm, W - MARGIN_R, 20*mm)
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(W/2, 15*mm, addr)

    c.save()
    return filepath

# Generate all
print("Generating memos...")
for key, g in sorted(groups.items()):
    path = generate_memo(g)
    print(f"  Created: {os.path.basename(path)}  (Present: {len(g['present'])}, Absent: {len(g['absent'])})")

print(f"\nDone. {len(groups)} PDFs saved to: {OUT_DIR}")
