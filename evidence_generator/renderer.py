import os
import random
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def render_pdf(filepath, evidence_id, evidence_type, title, prompt):
    """Deterministic PDF renderer for documentary evidence."""
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, f"EVIDENCE ARTIFACT: {evidence_id}")
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 1.3 * inch, f"TYPE: {evidence_type}")
    
    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 1.8 * inch, title)
    
    # Body (Prompt)
    c.setFont("Helvetica", 11)
    textobject = c.beginText()
    textobject.setTextOrigin(1 * inch, height - 2.3 * inch)
    
    # Wrap text
    lines = prompt.split('\n')
    for line in lines:
        words = line.split()
        current_line = ""
        for word in words:
            if c.stringWidth(current_line + word, "Helvetica", 11) < (width - 2 * inch):
                current_line += word + " "
            else:
                textobject.textLine(current_line)
                current_line = word + " "
        textobject.textLine(current_line)
        
    c.drawText(textobject)
    
    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(1 * inch, 1 * inch, "CONFIDENTIAL // CIVIX INVESTIGATION PLATFORM")
    
    c.showPage()
    c.save()

def _add_noise(img):
    """Add some procedural static/noise."""
    noise = Image.effect_noise(img.size, 10).convert('RGB')
    return Image.blend(img, noise, alpha=0.15)

def render_cctv(draw, width, height, evidence_id, title):
    draw.rectangle([0, 0, width, height], fill=(20, 25, 20))
    # Draw some "camera" grid lines
    for i in range(0, width, 100):
        draw.line([(i, 0), (i, height)], fill=(40, 50, 40), width=1)
    for i in range(0, height, 100):
        draw.line([(0, i), (width, i)], fill=(40, 50, 40), width=1)
    # Target box
    draw.rectangle([width//2 - 100, height//2 - 80, width//2 + 100, height//2 + 80], outline=(255, 0, 0), width=3)
    draw.text((width//2 - 95, height//2 - 100), "TARGET ACQUIRED", fill=(255, 0, 0))
    
    # HUD text
    draw.text((20, 20), "REC •", fill=(255, 0, 0))
    draw.text((20, 50), f"CAM ID: {evidence_id}", fill=(255, 255, 255))
    draw.text((20, height - 40), title, fill=(255, 255, 255))

def render_sketch(draw, width, height, evidence_id, title):
    draw.rectangle([0, 0, width, height], fill=(240, 235, 220)) # Sepia paper
    # Draw a generic silhouette outline
    draw.ellipse([width//2 - 80, height//2 - 120, width//2 + 80, height//2 + 50], outline=(50, 50, 50), width=2) # Head
    draw.ellipse([width//2 - 120, height//2 + 50, width//2 + 120, height//2 + 250], outline=(50, 50, 50), width=2) # Shoulders
    # Annotations
    draw.text((40, 40), "POLICE COMPOSITE SKETCH", fill=(0, 0, 0))
    draw.text((40, 70), f"REF: {evidence_id}", fill=(0, 0, 0))
    draw.text((40, height - 40), title, fill=(0, 0, 0))

def render_physical_evidence(draw, width, height, evidence_id, title):
    draw.rectangle([0, 0, width, height], fill=(200, 200, 200)) # Grey table
    # Draw an evidence bag
    draw.rectangle([100, 100, width - 100, height - 100], fill=(230, 230, 230), outline=(100, 100, 100), width=4)
    # Evidence tag
    draw.rectangle([150, 150, 350, 250], fill=(255, 255, 200), outline=(0, 0, 0), width=2)
    draw.text((160, 160), "EVIDENCE TAG", fill=(0, 0, 0))
    draw.text((160, 190), f"ID: {evidence_id}", fill=(0, 0, 0))
    # Item silhouette inside the bag
    draw.rectangle([width//2, height//2, width//2 + 150, height//2 + 80], fill=(50, 50, 50)) # Generic object (phone/gun shape)
    draw.text((width//2, height//2 - 30), "SEIZED ITEM", fill=(0, 0, 0))
    draw.text((100, height - 80), title, fill=(0, 0, 0))

def render_photograph(draw, width, height, evidence_id, title):
    draw.rectangle([0, 0, width, height], fill=(10, 10, 10))
    # Flash lighting effect simulation
    draw.ellipse([width//2 - 200, height//2 - 200, width//2 + 200, height//2 + 200], fill=(40, 40, 40))
    draw.text((20, 20), "FORENSIC PHOTOGRAPHY UNIT", fill=(200, 200, 200))
    draw.text((20, 50), f"REF: {evidence_id}", fill=(200, 200, 200))
    
    # Scale marker
    draw.rectangle([width//2 - 150, height//2 + 150, width//2 + 150, height//2 + 170], fill=(255, 255, 0))
    for i in range(width//2 - 150, width//2 + 150, 20):
        draw.line([(i, height//2 + 150), (i, height//2 + 170)], fill=(0, 0, 0), width=2)
    
    draw.text((20, height - 40), title, fill=(255, 255, 255))

def render_image(filepath, evidence_id, evidence_type, title, prompt):
    """Semantic graphical renderer for visual evidence."""
    width, height = 800, 600
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Set default font if possible
    font = ImageFont.load_default()
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        pass
        
    draw.font = font
    
    if evidence_type == "CCTV_FOOTAGE":
        render_cctv(draw, width, height, evidence_id, title)
    elif evidence_type == "SKETCH":
        render_sketch(draw, width, height, evidence_id, title)
    elif evidence_type == "PHYSICAL_EVIDENCE":
        render_physical_evidence(draw, width, height, evidence_id, title)
    else: # PHOTOGRAPH or default
        render_photograph(draw, width, height, evidence_id, title)

    # Apply some noise/blur to make it look less vector-perfect
    img = _add_noise(img)
    
    img.save(filepath)
