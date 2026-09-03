import os
import random
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

OUT_DIR = "scratch/test_docs_upgraded"
os.makedirs(OUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
title_style = styles['Heading1']
normal_style = styles['Normal']
alert_style = ParagraphStyle('Alert', parent=normal_style, textColor=colors.red)

def build_pdf(filename, title, content_paragraphs):
    path = os.path.join(OUT_DIR, filename)
    doc = SimpleDocTemplate(path, pagesize=letter)
    story = []
    
    story.append(Paragraph("SYNTHETIC / FICTIONAL — FOR CIVIX PROTOTYPE TESTING ONLY", alert_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))
    
    for para in content_paragraphs:
        if isinstance(para, str):
            story.append(Paragraph(para, normal_style))
            story.append(Spacer(1, 12))
        elif isinstance(para, list):
            # Table
            t = Table(para)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            story.append(t)
            story.append(Spacer(1, 12))
    
    doc.build(story)

def build_txt(filename, content):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("SYNTHETIC / FICTIONAL — FOR CIVIX PROTOTYPE TESTING ONLY\n")
        f.write("="*60 + "\n\n")
        f.write(content)

def build_image(filename, text):
    if not HAS_PIL:
        return
    path = os.path.join(OUT_DIR, filename)
    img = Image.new('RGB', (600, 300), color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 20), "SYNTHETIC / FICTIONAL — FOR CIVIX PROTOTYPE TESTING ONLY", fill=(255, 0, 0))
    y = 60
    for line in text.split('\n'):
        d.text((20, y), line, fill=(0, 0, 0))
        y += 20
    img.save(path)

# 1. FIR (PDF)
build_pdf("FIR_002_Noida.pdf", "FIRST INFORMATION REPORT (FIR)", [
    "FIR Number: FIR-2026-08-NOIDA-0042",
    "Date: 2026-08-31",
    "Reporting Officer: Inspector Amit Kumar, Sector 18 Police Station, Noida",
    "Incident Location: Sector 18 Market, Noida, Uttar Pradesh",
    "Suspect Apprehended: Vikram Singh (Alias: Vicky), DOB: 1985-04-12.",
    "Narrative:",
    "During a routine patrol near Sector 18 Market, Noida, officers intercepted a White Maruti Dzire bearing registration HR-26-XX-1122. The vehicle was driven by Vikram Singh. Upon searching the vehicle, officers discovered 5 kilograms of suspected contraband concealed in the trunk.",
    "Vikram Singh claimed he was an employee of 'Horizon Logistics Pvt Ltd' and was merely transporting a package given to him by an associate named Arun 'Tony' Das. The suspect stated the delivery was destined for a warehouse in Okhla.",
    "A mobile phone (Device ID: DEV-8833, Number: +91-9898989898) was seized from the suspect. The vehicle HR-26-XX-1122 has been impounded for forensic analysis."
])

# 2. Forensic Exam (PDF)
build_pdf("FORENSIC_008_Delhi.pdf", "FORENSIC EXAMINATION REPORT", [
    "Report ID: LAB-2026-DEL-991",
    "Date: 2026-09-02",
    "Subject: Examination of White Maruti Dzire (HR-26-XX-1122)",
    "Findings:",
    "1. The interior of the vehicle (HR-26-XX-1122) yielded multiple latent fingerprints matching Vikram Singh.",
    "2. A torn piece of a financial ledger was found under the passenger seat. The ledger fragment explicitly mentions 'Zenith Enterprises' and lists an HDFC Bank Account: 50100234XXXX.",
    "3. Trace amounts of chemical precursors were detected in the trunk lining.",
    "Conclusions:",
    "The vehicle has likely been used for repeated transport of contraband. The connection to Zenith Enterprises requires further financial investigation."
])

# 3. Intelligence Memo (PDF)
build_pdf("INTEL_004_Gurugram.pdf", "INTELLIGENCE & SURVEILLANCE MEMORANDUM", [
    "Memo Ref: INT-2026-GGM-08",
    "Date: 2026-08-30",
    "Subject: Surveillance of Neha Gupta at Cyber Hub",
    "Observation Narrative:",
    "At 18:30 hrs, target Neha Gupta was observed at Cyber Hub, Gurugram. She met with an unidentified male, later identified with 80% confidence as Rajat Sharma, known director of Zenith Enterprises.",
    "The two individuals conversed for approximately 45 minutes at a coffee shop. Neha Gupta handed over a yellow envelope to Rajat Sharma.",
    "Rajat Sharma departed the location at 19:15 hrs in a Black Toyota Fortuner bearing registration DL-9C-AA-9988. Neha Gupta left on foot towards the metro station.",
    "Intelligence suggests Neha Gupta coordinates financial transactions for Horizon Logistics Pvt Ltd and acts as a liaison to Zenith Enterprises."
])

# 4. Financial Report (PDF)
build_pdf("FINANCIAL_015_Delhi.pdf", "FINANCIAL INVESTIGATION SUMMARY", [
    "Report Ref: FIN-2026-09-03",
    "Subject: Zenith Enterprises and Horizon Logistics",
    "Account Details:",
    "1. HDFC Bank Acct: 50100234XXXX (Registered to Neha Gupta)",
    "2. SBI Bank Acct: 30499122XXXX (Registered to Zenith Enterprises, Signatory: Rajat Sharma)",
    "Transaction Analysis:",
    [
        ["Date", "Sender", "Recipient", "Amount (INR)", "Remarks"],
        ["2026-08-28", "Horizon Logistics", "HDFC Acct (Neha)", "500,000", "Consulting Fees"],
        ["2026-08-29", "HDFC Acct (Neha)", "SBI Acct (Zenith)", "450,000", "Vendor Payment"],
        ["2026-08-30", "Cash Deposit", "SBI Acct (Zenith)", "2,000,000", "Unexplained"]
    ],
    "Summary:",
    "There is a clear pattern of layering funds from Horizon Logistics through Neha Gupta's personal accounts into Zenith Enterprises, controlled by Rajat Sharma. The massive cash deposit on Aug 30 correlates with the envelope handover observed at Cyber Hub."
])

# 5. CDR (TXT)
build_txt("CDR_018_NCR.txt", """CALL DETAIL RECORD (CDR) ANALYSIS
Target Numbers:
- +91-9898989898 (Vikram Singh)
- +91-7777777777 (Neha Gupta)
- +91-9999988888 (Rajat Sharma)

Logs (2026-08-30 to 2026-08-31):
2026-08-30 17:00 | +91-7777777777 calls +91-9999988888 (Duration: 120s) | Location: Gurugram Tower A
2026-08-30 19:30 | +91-9999988888 calls +91-9898989898 (Duration: 45s) | Location: Gurugram Sector 29
2026-08-31 08:15 | +91-9898989898 sends SMS to +91-7777777777: "Pickup from Arun today. Need the Honda ready."
2026-08-31 10:00 | +91-7777777777 calls +91-9898989898 (Duration: 300s) | Location: Noida Sector 18
""")

# 6. GPS Movement (TXT)
build_txt("GPS_022_Vehicle.txt", """AUTOMATED TOLL PLAZA & ANPR LOGS
Date: 2026-08-31

Vehicle: HR-26-XX-1122 (White Maruti Dzire)
- 09:12 | Faridabad Toll Plaza (Inbound to Delhi)
- 10:45 | DND Flyway (Delhi to Noida)
- 11:30 | Sector 18 Noida ANPR Camera

Vehicle: DL-9C-AA-9988 (Black Toyota Fortuner)
- 14:20 | Golf Course Road, Gurugram ANPR Camera
- 15:10 | NH-48 Toll Plaza

Vehicle: UP-16-ZZ-4455 (Silver Honda City)
- 11:15 | Okhla Industrial Area Camera 4
""")

# 7. Search & Seizure (PDF)
build_pdf("SEIZURE_025_Okhla.pdf", "SEARCH AND SEIZURE MEMO", [
    "Memo Ref: SS-2026-09-04",
    "Location: Warehouse 42, Okhla Industrial Area, Delhi",
    "Date: 2026-09-04",
    "Items Seized:",
    "1. A Silver Honda City bearing registration UP-16-ZZ-4455, found parked inside the warehouse.",
    "2. Various shipping manifests bearing the logo of Horizon Logistics Pvt Ltd.",
    "3. A diary containing contact details for Arun 'Tony' Das.",
    "Observations:",
    "The warehouse appears to be a transit hub. The presence of the Silver Honda City confirms the communications intercepted on Aug 31 between Vikram Singh and Neha Gupta."
])

# 8. Witness Interview (PDF)
build_pdf("INTERVIEW_030_Das.pdf", "WITNESS INTERVIEW TRANSCRIPT", [
    "Interviewee: Arun Das (Alias: Tony)",
    "Date: 2026-09-05",
    "Location: Cyber Cell HQ, Delhi",
    "Transcript Excerpt:",
    "Officer: Explain your relationship with Vikram Singh and Horizon Logistics.",
    "Arun: I just manage the Okhla warehouse. Vicky (Vikram) comes by to pick up packages. I don't know what's inside.",
    "Officer: And who pays you?",
    "Arun: Neha Gupta transfers the money. But the real boss is Rajat Sharma. He owns Zenith Enterprises and uses a safehouse at 14B, Golf Course Road, Gurugram.",
    "Officer: Did you provide the Silver Honda City?",
    "Arun: Yes, Rajat told me to keep it ready at Warehouse 42 for a drop."
])

# 9. Device Extraction (TXT)
build_txt("DEVICE_EXT_035.txt", """DIGITAL DEVICE EXTRACTION REPORT
Device: iPhone 13 (DEV-8833)
Owner: Vikram Singh
Extraction Date: 2026-09-01

WhatsApp Chat Export with "Neha Coordinator" (+91-7777777777):
[2026-08-30 20:00] Neha: Met with RS. The funds are cleared into Zenith.
[2026-08-30 20:05] Vikram: Good. I am doing the run tomorrow morning. 
[2026-08-30 20:06] Neha: Don't use the Fortuner. RS says it's hot. Take the Dzire.
[2026-08-31 07:00] Vikram: On my way to Faridabad toll.
[2026-08-31 11:40] Vikram: I'm at Sector 18. Seeing cops. Call Tony.
""")

# 10. Image Evidence (JPG)
build_image("PHOTO_040_Logistics.jpg", """
=================================
    HORIZON LOGISTICS PVT LTD
    
    Vikram Singh
    Field Operations Manager
    
    Ph: +91-9898989898
    HQ: Warehouse 42, Okhla, Delhi
=================================
""")

print("Dataset generated successfully.")
