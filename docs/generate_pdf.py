"""
PDF Generator Script using ReportLab
Compiles the comprehensive project documentation and evaluation charts into
a formal, multi-page academic PDF report.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Reinforcement Learning Edge AI: Fire & Gas Monitor (M5Stamp ESP32-S3)")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, footer_text)
        self.drawString(54, 40, "Confidential & Academic Submission - November 2026")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 52, 558, 52)
        
        self.restoreState()

def build_pdf(filename="docs/PROJECT_PROPOSAL_REPORT.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0f172a"),
        alignment=0,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#0f766e"),
        backColor=colors.HexColor("#f0fdf4"),
        borderColor=colors.HexColor("#10b981"),
        borderWidth=1,
        borderPadding=8,
        spaceBefore=6,
        spaceAfter=10
    )

    table_text_style = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1e293b")
    )

    table_head_style = ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    # Title Page Banner
    story.append(Paragraph("Reinforcement Learning-Driven Adaptive Duty-Cycling for Ultra-Low-Power Edge IoT Fire & Gas Monitoring", title_style))
    story.append(Paragraph("<b>Project Proposal & Technical Report</b> | Target Platform: M5Stamp ESP32-S3 + Bosch BME680 + 3.2V LiFePO4", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563eb"), spaceAfter=15))

    # Meta Table
    meta_data = [
        [Paragraph("<b>Project Title:</b> RL-Driven Adaptive Fire & Gas IoT Monitor", table_text_style), Paragraph("<b>Roll No / Student ID:</b> [Insert Your Roll No Here]", table_text_style)],
        [Paragraph("<b>GitHub Repository:</b> https://github.com/[User]/RL-Edge-AI-Fire-Gas-Monitor", table_text_style), Paragraph("<b>Dataset Reference:</b> Kaggle IoT Smoke & Gas Dataset", table_text_style)],
        [Paragraph("<b>Target Hardware:</b> M5Stamp ESP32-S3 + BME680", table_text_style), Paragraph("<b>Power System:</b> 3.2V 600mAh LiFePO4 + INA219 Fuel Gauge", table_text_style)],
        [Paragraph("<b>Cloud Telemetry:</b> AWS IoT Core + DynamoDB", table_text_style), Paragraph("<b>Alerting:</b> Amazon SNS (Instant Email)", table_text_style)]
    ]
    meta_table = Table(meta_data, colWidths=[250, 250])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "Autonomous environmental and fire monitoring systems in remote or battery-constrained environments "
        "face a fundamental trade-off: <b>energy preservation vs. detection responsiveness</b>. Traditional "
        "metal-oxide semiconductor (MOS) and volatile organic compound (VOC) gas sensors (such as the Bosch BME680) "
        "require an internal micro-hotplate heated to over 300°C to facilitate gas-surface adsorption, consuming between "
        "10 mA and 15 mA per measurement burst. Simultaneously, wireless transceivers (Wi-Fi 802.11b/g/n) draw 120 mA to "
        "200 mA during radio activity. Operating continuously depletes standard battery cells within hours, while prolonged "
        "fixed sleep intervals (e.g., polling every 10–15 minutes) introduce dangerous detection delays during fires.",
        body_style
    ))
    story.append(Paragraph(
        "This project presents an <b>Edge Reinforcement Learning (RL) framework</b> executing on an <b>M5Stamp ESP32-S3</b>. "
        "The agent dynamically modulates micro-hotplate heating bursts, deep sleep cycles (15 µA), and Wi-Fi transmissions "
        "based on environmental trends and real-time battery State-of-Charge (SoC). Simulation results confirm a "
        "<b>70.3% reduction in energy consumption</b> over fixed high-rate sampling while ensuring 100% fire detection within 65 seconds.",
        body_style
    ))

    # Hardware Architecture & BOM
    story.append(Paragraph("2. Hardware Stack & Bill of Materials (BOM)", h1_style))
    story.append(Paragraph(
        "The hardware was selected for long-term reliability and zero calendar degradation. Unlike standard Li-ion chemistries "
        "which degrade after a few months, <b>3.2V LiFePO4 cells</b> feature virtually zero degradation over thousands of cycles.",
        body_style
    ))

    bom_data = [
        [Paragraph("Item / Subsystem", table_head_style), Paragraph("Component", table_head_style), Paragraph("Key Role", table_head_style), Paragraph("Robu Price", table_head_style)],
        [Paragraph("Microcontroller", table_text_style), Paragraph("M5Stamp ESP32-S3", table_text_style), Paragraph("Dual-core 240MHz, 15µA sleep, Wi-Fi radio", table_text_style), Paragraph("₹1,209", table_text_style)],
        [Paragraph("Gas & Env Sensor", table_text_style), Paragraph("SmartElex BME680 Board", table_text_style), Paragraph("Pulsed micro-hotplate VOC/gas, T, P, H", table_text_style), Paragraph("₹1,049", table_text_style)],
        [Paragraph("Fuel Gauge", table_text_style), Paragraph("INA219 I2C Module", table_text_style), Paragraph("Real-time mA/mV Coulomb counter for SoC", table_text_style), Paragraph("₹139", table_text_style)],
        [Paragraph("Battery Cell", table_text_style), Paragraph("Orange IFR14500 (AA)", table_text_style), Paragraph("3.2V 600mAh LiFePO4 (no degradation)", table_text_style), Paragraph("₹149", table_text_style)],
        [Paragraph("Battery Holder", table_text_style), Paragraph("1x AA Holder with Wires", table_text_style), Paragraph("Safe single-cell 3.2V connection", table_text_style), Paragraph("₹25", table_text_style)],
        [Paragraph("Dedicated Charger", table_text_style), Paragraph("TP5000 3.6V LFP Module", table_text_style), Paragraph("3.65V CC/CV charging (solder jumper F)", table_text_style), Paragraph("₹99", table_text_style)],
        [Paragraph("Hardware BMS", table_text_style), Paragraph("1S 12A 3.6V LiFePO4 Board", table_text_style), Paragraph("Over-discharge cutoff protection at 2.0V", table_text_style), Paragraph("₹89", table_text_style)],
    ]
    bom_table = Table(bom_data, colWidths=[90, 130, 210, 70])
    bom_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(bom_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<b>Power Protection Note:</b> The TP5000 handles charging only; the separate 1S BMS board guarantees that cell voltage "
        "never drops below 2.0V. The 1x AA holder prevents series overvoltage, delivering a stable 3.2V nominal rail directly to the ESP32.",
        callout_style
    ))

    # Page Break for RL & Results
    story.append(PageBreak())

    # Reinforcement Learning Formulation
    story.append(Paragraph("3. Edge Reinforcement Learning Formulation (MDP)", h1_style))
    story.append(Paragraph(
        "The decision problem is modeled as a discrete Markov Decision Process (MDP) designed for sub-microsecond embedded execution:",
        body_style
    ))
    story.append(Paragraph("• <b>State Space (54 Discrete States):</b> Formed by quantizing Temperature (3 bins), Gas Resistance (3 bins), Gas Derivative (2 bins), and Battery SoC (3 bins). Calculated as <code>state_idx = (T*18) + (G*6) + (dG*3) + SoC</code>.", bullet_style))
    story.append(Paragraph("• <b>Action Space (4 Control Profiles):</b>", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- <i>Action 0 (DEEP_SLEEP_LONG):</i> Sleep 600s, no heater, radio OFF (~15 µA).", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- <i>Action 1 (NORMAL_CYCLE):</i> Sleep 60s, pulse micro-hotplate 30ms, radio OFF (~2.38 mJ).", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- <i>Action 2 (ELEVATED_SCAN):</i> Sleep 10s, pulse micro-hotplate 50ms, radio OFF.", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- <i>Action 3 (EMERGENCY_ALERT):</i> Sleep 2s, full sensor scan, turn ON Wi-Fi, publish alert JSON to AWS (~576 mJ).", bullet_style))
    story.append(Paragraph("• <b>Reward Function:</b> Penalizes energy consumed while heavily rewarding timely fire detection and penalizing false alarms.", bullet_style))
    story.append(Paragraph("• <b>On-Chip Model Compression:</b> Tabular Q-learning produces a 54x4 floating point matrix exported as <code>q_table_export.h</code>. Total RAM footprint is only <b>864 bytes</b>, requiring zero neural network runtime libraries.", bullet_style))

    story.append(Spacer(1, 8))

    # Experimental Results & Figures
    story.append(Paragraph("4. Experimental Results & Verification", h1_style))
    story.append(Paragraph(
        "We performed 1500 training episodes and 50 stochastic test episodes evaluating the RL agent against fixed baselines:",
        body_style
    ))

    res_data = [
        [Paragraph("Strategy", table_head_style), Paragraph("Energy Consumed", table_head_style), Paragraph("Energy Savings", table_head_style), Paragraph("Detection Delay", table_head_style), Paragraph("Detection Rate", table_head_style)],
        [Paragraph("Fixed High-Rate (10s)", table_text_style), Paragraph("21.23 Joules", table_text_style), Paragraph("Baseline (0%)", table_text_style), Paragraph("18.4 seconds", table_text_style), Paragraph("100%", table_text_style)],
        [Paragraph("Fixed Low-Rate (600s)", table_text_style), Paragraph("3.12 Joules", table_text_style), Paragraph("-85.3%", table_text_style), Paragraph("312.0 seconds", table_text_style), Paragraph("42% (Missed window)", table_text_style)],
        [Paragraph("<b>RL Adaptive (Ours)</b>", table_text_style), Paragraph("<b>6.29 Joules</b>", table_text_style), Paragraph("<b>-70.3% Savings</b>", table_text_style), Paragraph("<b>65.0 seconds</b>", table_text_style), Paragraph("<b>100%</b>", table_text_style)],
    ]
    res_table = Table(res_data, colWidths=[130, 95, 95, 95, 85])
    res_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2563eb")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#eff6ff")]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(res_table)
    story.append(Spacer(1, 10))

    # Embed Plots if available
    chart_path = "docs/figures/energy_comparison.png"
    train_path = "docs/figures/training_curve.png"
    if os.path.exists(chart_path) and os.path.exists(train_path):
        plot_table = Table([
            [Image(train_path, width=245, height=138), Image(chart_path, width=245, height=138)]
        ], colWidths=[250, 250])
        plot_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(plot_table)
        story.append(Spacer(1, 8))

    # Cloud & Local Dashboard
    story.append(Paragraph("5. Cloud Telemetry & Local React Dashboard", h1_style))
    story.append(Paragraph(
        "• <b>AWS IoT Core & DynamoDB:</b> Telemetry is published as JSON payloads. An IoT Core Rule routes every incoming packet into an Amazon DynamoDB table (<code>M5Stack_Telemetry</code>) for permanent logging under the AWS Free Tier.",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Amazon SNS Email Alerting:</b> The IoT rule evaluates <code>WHERE fire_alert = true OR temperature_c > 50.0</code> and pushes an urgent notification to the user's email within 2 seconds.",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Local Demonstration Dashboard:</b> Built using <b>React 18, Vite, TailwindCSS, and Recharts</b>, communicating via a local FastAPI proxy. It renders real-time KPI cards, dynamic hazard graphs, Coulomb counting battery curves, and includes a <b>'Simulate Fire Hazard'</b> trigger for live demonstration to professors.",
        body_style
    ))

    # Timeline to Demonstration
    story.append(Paragraph("6. Project Timeline & Demonstration Roadmap", h1_style))
    story.append(Paragraph("• <b>Nov 10 (Today):</b> Proposal submission, simulation environment, Q-table training, firmware generation, cloud schemas, and local dashboard ready.", bullet_style))
    story.append(Paragraph("• <b>Nov 12 – 15:</b> Hardware package arrival from Robu.in. Soldering TP5000 3.6V LFP jumper, assembling 1S BMS, and verifying I2C sensor bus on breadboard.", bullet_style))
    story.append(Paragraph("• <b>Nov 16 – 17:</b> Flashing M5Stamp ESP32-S3 firmware, performing lighter/gas canister sensitivity test, and validating live AWS email alerts.", bullet_style))
    story.append(Paragraph("• <b>Nov 18:</b> Formal project demonstration and live evaluation with course evaluators.", bullet_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {filename}")

if __name__ == "__main__":
    build_pdf()
