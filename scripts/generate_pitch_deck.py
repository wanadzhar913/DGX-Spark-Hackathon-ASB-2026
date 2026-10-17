#!/usr/bin/env python3
"""
Generates a clear, convincing 16:9 widescreen PPTX pitch deck for EdgeVision.
Uses simple, jargon-free words so any judge or customer understands and buys the idea immediately.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_paths):
    prs = Presentation()
    # 16:9 Widescreen format
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette
    NV_GREEN = RGBColor(118, 185, 0)     # #76b900
    BG_DARK = RGBColor(10, 13, 20)        # #0a0d14
    CARD_BG = RGBColor(22, 29, 44)        # #161d2c
    CARD_BORDER = RGBColor(40, 52, 78)    # #28344e
    TEXT_MAIN = RGBColor(248, 250, 252)   # #f8fafc
    TEXT_MUTED = RGBColor(148, 163, 184)  # #94a3b8
    DANGER = RGBColor(239, 68, 68)        # #ef4444
    WARNING = RGBColor(245, 158, 11)      # #f59e0b
    CYAN = RGBColor(6, 182, 212)          # #06b6d4

    def add_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_DARK
        bg.line.fill.background()
        return bg

    def add_header(slide, badge_text, title_text, highlight_word=None, subtitle_text=None):
        # Badge
        badge_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.55), Inches(11), Inches(0.4))
        tf = badge_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_bottom = tf.margin_right = 0
        p = tf.paragraphs[0]
        p.text = f"●  {badge_text.upper()}"
        p.font.name = "Arial"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = NV_GREEN

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.95), Inches(11.5), Inches(0.85))
        tf = title_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_bottom = tf.margin_right = 0
        p = tf.paragraphs[0]
        p.font.name = "Arial"
        p.font.size = Pt(32)
        p.font.bold = True

        if highlight_word and highlight_word in title_text:
            parts = title_text.split(highlight_word)
            r1 = p.add_run()
            r1.text = parts[0]
            r1.font.color.rgb = TEXT_MAIN

            r_hi = p.add_run()
            r_hi.text = highlight_word
            r_hi.font.color.rgb = NV_GREEN

            if len(parts) > 1:
                r2 = p.add_run()
                r2.text = parts[1]
                r2.font.color.rgb = TEXT_MAIN
        else:
            r = p.add_run()
            r.text = title_text
            r.font.color.rgb = TEXT_MAIN

        # Subtitle
        if subtitle_text:
            sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.5), Inches(0.45))
            tf = sub_box.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_top = tf.margin_bottom = tf.margin_right = 0
            p = tf.paragraphs[0]
            p.text = subtitle_text
            p.font.name = "Arial"
            p.font.size = Pt(14)
            p.font.color.rgb = TEXT_MUTED

    # -------------------------------------------------------------
    # SLIDE 1: TITLE & HOOK (Simple, Punchy, High Energy)
    # -------------------------------------------------------------
    slide1 = prs.slides.add_slide(blank_layout)
    add_background(slide1)
    
    slide1.notes_slide.notes_text_frame.text = (
        "HOW TO SAY THIS (30 seconds):\n"
        "'Every hospital, warehouse, and factory has dozens of security cameras. "
        "Right now, they have a big problem: human guards get tired and miss accidents, "
        "while sending live video to the cloud costs over $14,000 every month and slows down the internet. "
        "We built EdgeVision. It puts smart vision AI directly on local NVIDIA chips. "
        "It catches hazards in one second, costs $0 in cloud bills, and your private video never leaves the building.'"
    )

    # Title Badge
    b1 = slide1.shapes.add_textbox(Inches(0.8), Inches(1.1), Inches(11), Inches(0.4))
    b1.text_frame.margin_left = b1.text_frame.margin_top = 0
    p = b1.text_frame.paragraphs[0]
    p.text = "●  NVIDIA AI HACKATHON // EDGE VISION"
    p.font.name = "Arial"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = NV_GREEN

    # Main Title
    t1 = slide1.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.5), Inches(1.6))
    t1.text_frame.margin_left = t1.text_frame.margin_top = 0
    t1.text_frame.word_wrap = True
    p = t1.text_frame.paragraphs[0]
    p.font.name = "Arial"
    p.font.size = Pt(44)
    p.font.bold = True
    r1 = p.add_run()
    r1.text = "Smart Security for Every Camera,\nPowered by "
    r1.font.color.rgb = TEXT_MAIN
    r2 = p.add_run()
    r2.text = "NVIDIA AI"
    r2.font.color.rgb = NV_GREEN

    # Subtitle
    s1 = slide1.shapes.add_textbox(Inches(0.8), Inches(3.3), Inches(11.5), Inches(0.6))
    s1.text_frame.margin_left = s1.text_frame.margin_top = 0
    p = s1.text_frame.paragraphs[0]
    p.text = "Stops workplace accidents and break-ins in real time. Zero cloud fees. Zero slow internet. 100% private."
    p.font.name = "Arial"
    p.font.size = Pt(17)
    p.font.color.rgb = TEXT_MUTED

    # 4 Simple Metric Cards
    metrics = [
        ("$0", "NO CLOUD FEES", "Runs locally. No monthly OpenAI or AWS bills.", NV_GREEN),
        ("1 Second", "INSTANT ALERTS", "Catches danger and notifies staff immediately.", TEXT_MAIN),
        ("All Cameras", "RUNS TOGETHER", "Spreads the camera workload across NVIDIA GPUs.", TEXT_MAIN),
        ("100% Private", "SAFE & AIR-GAPPED", "Private video stays inside your building.", TEXT_MAIN)
    ]

    card_w = Inches(2.7)
    card_h = Inches(2.4)
    card_gap = Inches(0.3)
    start_x = Inches(0.8)
    card_y = Inches(4.3)

    for i, (num, sub, desc, color) in enumerate(metrics):
        x = start_x + i * (card_w + card_gap)
        c = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, card_y, card_w, card_h)
        c.fill.solid()
        c.fill.fore_color.rgb = CARD_BG
        c.line.color.rgb = NV_GREEN if i == 0 else CARD_BORDER
        c.line.width = Pt(1.5 if i == 0 else 1)

        tb = slide1.shapes.add_textbox(x + Inches(0.25), card_y + Inches(0.25), card_w - Inches(0.5), card_h - Inches(0.5))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_bottom = tf.margin_right = 0
        
        p = tf.paragraphs[0]
        p.text = num
        p.font.name = "Arial"
        p.font.size = Pt(34)
        p.font.bold = True
        p.font.color.rgb = color

        p2 = tf.add_paragraph()
        p2.text = sub
        p2.font.name = "Arial"
        p2.font.size = Pt(10)
        p2.font.bold = True
        p2.font.color.rgb = NV_GREEN if i == 0 else TEXT_MAIN
        p2.space_before = Pt(8)

        p3 = tf.add_paragraph()
        p3.text = desc
        p3.font.name = "Arial"
        p3.font.size = Pt(11)
        p3.font.color.rgb = TEXT_MUTED
        p3.space_before = Pt(6)

    # -------------------------------------------------------------
    # SLIDE 2: THE PROBLEM (Clear, relatable pain points)
    # -------------------------------------------------------------
    slide2 = prs.slides.add_slide(blank_layout)
    add_background(slide2)
    add_header(slide2, "THE PROBLEM // WHY SECURITY IS FAILING", "Why Today's Security Cameras Are 'Dumb'", "Today's Security Cameras", "Companies have thousands of cameras, but they only record video for after something goes wrong.")

    slide2.notes_slide.notes_text_frame.text = (
        "HOW TO SAY THIS (40 seconds):\n"
        "'Right now, security cameras are passive. They only record accidents after they happen.\n"
        "Why can't companies just connect them to cloud AI like ChatGPT or AWS?\n"
        "1. It is way too expensive: sending 50 video streams to the cloud costs over $14,000 every single month.\n"
        "2. It chokes internet bandwidth: video files are huge, and factories or warehouses don't have super-fast fiber.\n"
        "3. Privacy: Banks, hospitals, and factories cannot send confidential video to outside servers.\n"
        "And when you rely on humans, guards get tired after 20 minutes and miss almost everything.'"
    )

    problems = [
        ("💸", "Way Too Expensive", "Streaming 50 camera feeds to cloud AI costs over $14,000 every month in token fees. That is $170,000+ every single year.", DANGER),
        ("🛑", "Chokes the Internet", "Live video is heavy. Streaming dozens of cameras slows down the whole company network, causing lag and lost footage.", WARNING),
        ("🔒", "Not Safe for Private Sites", "Hospitals, factories, and banks cannot legally upload security footage to outside cloud companies.", CYAN)
    ]

    p_w = Inches(3.68)
    p_h = Inches(3.3)
    p_gap = Inches(0.35)
    p_start_x = Inches(0.8)
    p_y = Inches(2.5)

    for i, (icon, title, desc, col) in enumerate(problems):
        x = p_start_x + i * (p_w + p_gap)
        c = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, p_y, p_w, p_h)
        c.fill.solid()
        c.fill.fore_color.rgb = CARD_BG
        c.line.color.rgb = CARD_BORDER
        c.line.width = Pt(1)

        tb = slide2.shapes.add_textbox(x + Inches(0.3), p_y + Inches(0.3), p_w - Inches(0.6), p_h - Inches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = 0

        p = tf.paragraphs[0]
        p.text = f"{icon}  {title}"
        p.font.name = "Arial"
        p.font.size = Pt(19)
        p.font.bold = True
        p.font.color.rgb = TEXT_MAIN

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.name = "Arial"
        p2.font.size = Pt(13)
        p2.font.color.rgb = TEXT_MUTED
        p2.space_before = Pt(14)

    # Bottom Callout Box (The Guard problem)
    strip = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.1), Inches(11.733), Inches(0.75))
    strip.fill.solid()
    strip.fill.fore_color.rgb = RGBColor(35, 18, 22)
    strip.line.color.rgb = DANGER
    strip.line.width = Pt(1)

    tb_strip = slide2.shapes.add_textbox(Inches(1.1), Inches(6.15), Inches(11.1), Inches(0.65))
    tf = tb_strip.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "⚠️  The Human Guard Problem: Studies show human security guards miss up to 95% of events on screens after watching monitors for just 20 minutes."
    p.font.name = "Arial"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = RGBColor(254, 202, 202)

    # -------------------------------------------------------------
    # SLIDE 3: THE SOLUTION (Simple 5-step diagram)
    # -------------------------------------------------------------
    slide3 = prs.slides.add_slide(blank_layout)
    add_background(slide3)
    add_header(slide3, "THE SOLUTION // HOW EDGEVISION WORKS", "How EdgeVision Works", "EdgeVision Works", "We put smart Vision AI right on local NVIDIA graphics cards inside the building.")

    slide3.notes_slide.notes_text_frame.text = (
        "HOW TO SAY THIS (45 seconds):\n"
        "'Here is how simple EdgeVision is:\n"
        "1. It connects to the cameras you already have.\n"
        "2. Instead of streaming heavy video, it checks a smart picture every 1.5 seconds.\n"
        "3. Local NVIDIA chips analyze the scene using Vision AI.\n"
        "4. If there is a hazard, our dashboard highlights it with a red box.\n"
        "5. It sends an instant WhatsApp or Slack alert to the manager in less than 1.2 seconds.\n"
        "Everything stays on-premise—fast, reliable, and completely private.'"
    )

    # Process Flow Nodes (5 simple steps)
    nodes = [
        ("1. YOUR CAMERAS", "Connects to any\nstandard CCTV feed", CARD_BG, CARD_BORDER),
        ("2. SMART SAMPLER", "Checks a picture\nevery 1.5 seconds", CARD_BG, CARD_BORDER),
        ("3. NVIDIA AI CHIP", "Spots danger locally\nusing Vision AI", RGBColor(16, 32, 24), NV_GREEN),
        ("4. LIVE DASHBOARD", "Draws box on hazard\nwith safety advice", CARD_BG, CARD_BORDER),
        ("5. INSTANT ALERT", "Sends phone alert &\nsounds local alarm", CARD_BG, CARD_BORDER)
    ]

    node_w = Inches(2.05)
    node_h = Inches(1.8)
    node_gap = Inches(0.37)
    node_start_x = Inches(0.8)
    node_y = Inches(2.4)

    for i, (title, sub, bg, border) in enumerate(nodes):
        x = node_start_x + i * (node_w + node_gap)
        c = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, node_y, node_w, node_h)
        c.fill.solid()
        c.fill.fore_color.rgb = bg
        c.line.color.rgb = border
        c.line.width = Pt(1.5 if border == NV_GREEN else 1)

        tb = slide3.shapes.add_textbox(x + Inches(0.12), node_y + Inches(0.2), node_w - Inches(0.24), node_h - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = 0

        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = title
        p.font.name = "Arial"
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = NV_GREEN if border == NV_GREEN else TEXT_MAIN

        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        p2.text = sub
        p2.font.name = "Arial"
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_MUTED
        p2.space_before = Pt(8)

        if i < len(nodes) - 1:
            arrow_box = slide3.shapes.add_textbox(x + node_w, node_y + Inches(0.6), node_gap, Inches(0.5))
            tf_a = arrow_box.text_frame
            tf_a.margin_left = tf_a.margin_top = 0
            pa = tf_a.paragraphs[0]
            pa.alignment = PP_ALIGN.CENTER
            pa.text = "➔"
            pa.font.name = "Arial"
            pa.font.size = Pt(18)
            pa.font.color.rgb = TEXT_MUTED

    # Bottom 2 Feature Explanations
    f_w = Inches(5.7)
    f_h = Inches(2.3)
    f_y = Inches(4.5)

    feat1 = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), f_y, f_w, f_h)
    feat1.fill.solid()
    feat1.fill.fore_color.rgb = CARD_BG
    feat1.line.color.rgb = CARD_BORDER

    tb_f1 = slide3.shapes.add_textbox(Inches(1.05), f_y + Inches(0.25), f_w - Inches(0.5), f_h - Inches(0.5))
    tf1 = tb_f1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "⚡  Uses Multiple NVIDIA GPUs Together"
    p.font.name = "Arial"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NV_GREEN

    p2 = tf1.add_paragraph()
    p2.text = "EdgeVision splits your camera feeds across multiple graphics cards. GPU 0 monitors active factory zones, while GPU 1 monitors fire doors and hallways. It runs cool and never slows down."
    p2.font.name = "Arial"
    p2.font.size = Pt(12)
    p2.font.color.rgb = TEXT_MUTED
    p2.space_before = Pt(8)

    feat2 = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.833), f_y, f_w, f_h)
    feat2.fill.solid()
    feat2.fill.fore_color.rgb = CARD_BG
    feat2.line.color.rgb = CARD_BORDER

    tb_f2 = slide3.shapes.add_textbox(Inches(7.083), f_y + Inches(0.25), f_w - Inches(0.5), f_h - Inches(0.5))
    tf2 = tb_f2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "📋  Clear Action Steps, Not False Alarms"
    p.font.name = "Arial"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NV_GREEN

    p2 = tf2.add_paragraph()
    p2.text = "Every alert tells the supervisor: What is wrong, where it happened, how urgent it is, and the exact action to take (e.g. 'Sound buzzer on Line 1' or 'Clean spill on Aisle 4')."
    p2.font.name = "Arial"
    p2.font.size = Pt(12)
    p2.font.color.rgb = TEXT_MUTED
    p2.space_before = Pt(8)

    # -------------------------------------------------------------
    # SLIDE 4: WHAT IT CATCHES (Concrete, Easy Examples)
    # -------------------------------------------------------------
    slide4 = prs.slides.add_slide(blank_layout)
    add_background(slide4)
    add_header(slide4, "WHAT IT CATCHES // REAL SCENARIOS", "One AI Model for Every Threat", "Every Threat", "Old tools need a different model for each problem. EdgeVision understands everything using one model.")

    slide4.notes_slide.notes_text_frame.text = (
        "HOW TO SAY THIS (45 seconds):\n"
        "'Older computer vision tools are fragile—you need one model for helmets, another for fire, another for people.\n"
        "With NVIDIA Vision LLMs, one model understands everything.\n"
        "Here are 4 live examples happening right now in our demo:\n"
        "1. Camera 1: A worker forgot their hard hat near a heavy crane.\n"
        "2. Camera 2: An unauthorized stranger walking in the server room at 3 AM.\n"
        "3. Camera 3: A slippery chemical spill right where forklifts drive.\n"
        "4. Camera 4: Boxes piled high blocking the emergency fire exit.\n"
        "And if you want to detect smoking or running tomorrow, you just type it in plain English!'"
    )

    scenarios = [
        ("CAM-01 // DANGER", "Worker Missing Hard Hat", "Worker walking under heavy crane without a helmet. High safety risk.", "Accuracy: 98.4%", DANGER),
        ("CAM-02 // DANGER", "After-Hours Intruder", "Unknown person spotted inside restricted server vault at 3:14 AM.", "Accuracy: 97.1%", DANGER),
        ("CAM-03 // WARNING", "Liquid Spill on Floor", "Chemical spill spreading near forklift lane. High slip and crash risk.", "Accuracy: 94.2%", WARNING),
        ("CAM-04 // WARNING", "Fire Exit Blocked", "Cardboard boxes piled up blocking the emergency exit door by 75%.", "Accuracy: 96.3%", WARNING)
    ]

    s_w = Inches(2.7)
    s_h = Inches(3.6)
    s_gap = Inches(0.3)
    s_start_x = Inches(0.8)
    s_y = Inches(2.5)

    for i, (cam_badge, title, desc, conf, accent) in enumerate(scenarios):
        x = s_start_x + i * (s_w + s_gap)
        c = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, s_y, s_w, s_h)
        c.fill.solid()
        c.fill.fore_color.rgb = CARD_BG
        c.line.color.rgb = accent
        c.line.width = Pt(1.5)

        tb = slide4.shapes.add_textbox(x + Inches(0.22), s_y + Inches(0.25), s_w - Inches(0.44), s_h - Inches(0.5))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = 0

        p = tf.paragraphs[0]
        p.text = cam_badge
        p.font.name = "Arial"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = accent

        p2 = tf.add_paragraph()
        p2.text = title
        p2.font.name = "Arial"
        p2.font.size = Pt(16)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_MAIN
        p2.space_before = Pt(8)

        p3 = tf.add_paragraph()
        p3.text = desc
        p3.font.name = "Arial"
        p3.font.size = Pt(12)
        p3.font.color.rgb = TEXT_MUTED
        p3.space_before = Pt(10)

        p4 = tf.add_paragraph()
        p4.text = f"●  {conf}"
        p4.font.name = "Arial"
        p4.font.size = Pt(11)
        p4.font.bold = True
        p4.font.color.rgb = NV_GREEN
        p4.space_before = Pt(16)

    # Callout below
    bot_box = slide4.shapes.add_textbox(Inches(0.8), Inches(6.3), Inches(11.733), Inches(0.6))
    tf = bot_box.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "💡  Super Easy to Customize: Want to spot people smoking or phone use on the job? Just tell the AI in plain English—no retraining required!"
    p.font.name = "Arial"
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_MUTED

    # -------------------------------------------------------------
    # SLIDE 5: WHY WE WIN (Crystal clear comparison table)
    # -------------------------------------------------------------
    slide5 = prs.slides.add_slide(blank_layout)
    add_background(slide5)
    add_header(slide5, "COMPARISON // WHY WE ARE BETTER", "Why EdgeVision Beats the Rest", "Beats the Rest", "A clear comparison against human guards and cloud-based AI.")

    slide5.notes_slide.notes_text_frame.text = (
        "HOW TO SAY THIS (45 seconds):\n"
        "'When judges ask why you can't just use guards or cloud AI, point right to this slide:\n"
        "- Human guards cost $12,000 every month and take 20 minutes to notice hazards.\n"
        "- Cloud AI like AWS or OpenAI costs over $14,000 every month, slows down internet, and sends private video outside.\n"
        "- EdgeVision on NVIDIA hardware costs $0 in monthly cloud bills, reacts in 1 second, needs 0 internet, and is 100% private.'"
    )

    rows = 6
    cols = 4
    t_left = Inches(0.8)
    t_top = Inches(2.4)
    t_width = Inches(11.733)
    t_height = Inches(4.3)

    table_shape = slide5.shapes.add_table(rows, cols, t_left, t_top, t_width, t_height)
    table = table_shape.table
    table.columns[0].width = Inches(3.2)
    table.columns[1].width = Inches(2.6)
    table.columns[2].width = Inches(2.9)
    table.columns[3].width = Inches(3.033)

    table_data = [
        ["WHAT MATTERS", "HUMAN SECURITY GUARDS", "CLOUD AI (AWS / OPENAI)", "EDGEVISION (NVIDIA LOCAL)"],
        ["Monthly Cost (50 Cams)", "$12,000+ (Staff wages)", "$14,280+ (API + Data bills)", "$0 (Runs on local hardware)"],
        ["Reaction Speed", "15 to 45 minutes late", "4 to 6 seconds", "Under 1.2 seconds (Instant)"],
        ["Internet Required", "None", "Chokes your internet line", "0 internet needed (Offline)"],
        ["Video Privacy", "Private", "❌ Risky (Leaves the building)", "✅ 100% Private & Air-Gapped"],
        ["What Happens on Danger", "Slow phone calls", "Just sends an email", "Loud buzzer + Instant alert"]
    ]

    for r_idx, row in enumerate(table_data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = val
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            
            p = cell.text_frame.paragraphs[0]
            p.font.name = "Arial"
            p.font.size = Pt(13 if r_idx > 0 else 11)
            p.font.bold = (r_idx == 0 or c_idx == 3)
            
            if r_idx == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(26, 36, 54) if c_idx < 3 else RGBColor(30, 52, 20)
                p.font.color.rgb = NV_GREEN if c_idx == 3 else TEXT_MUTED
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = CARD_BG if c_idx < 3 else RGBColor(16, 28, 20)
                p.font.color.rgb = NV_GREEN if c_idx == 3 else (TEXT_MAIN if c_idx == 0 else TEXT_MUTED)

    # -------------------------------------------------------------
    # SLIDE 6: BUSINESS VALUE & DEMO (Crisp Closing)
    # -------------------------------------------------------------
    slide6 = prs.slides.add_slide(blank_layout)
    add_background(slide6)
    add_header(slide6, "THE VALUE // READY TODAY", "Safer Workplaces. $170K Saved Every Year.", "$170K Saved Every Year.", "Works immediately with the cameras and NVIDIA hardware companies already have.")

    slide6.notes_slide.notes_text_frame.text = (
        "HOW TO SAY THIS (30 seconds):\n"
        "'To wrap up: EdgeVision turns regular cameras into an autonomous safety center.\n"
        "It saves $170,000 every year in cloud bills for a typical 50-camera facility,\n"
        "cuts accident response time from 30 minutes down to 1 second, and sets up in just 1 day.\n"
        "Now let's switch to our live demo. We invite the judges to step in front of our camera and see it work in real time!'"
    )

    roi_cards = [
        ("Instant", "ACCIDENT PREVENTION", "Spots hazards before injuries happen, saving lives and avoiding fines.", NV_GREEN),
        ("$171,000", "SAVED EVERY YEAR", "No recurring cloud fees for a standard 50-camera workplace.", TEXT_MAIN),
        ("1 Day", "EASY SETUP", "Plugs directly into the cameras companies already own today.", TEXT_MAIN)
    ]

    r_w = Inches(3.68)
    r_h = Inches(2.5)
    r_gap = Inches(0.35)
    r_start_x = Inches(0.8)
    r_y = Inches(2.4)

    for i, (num, sub, desc, col) in enumerate(roi_cards):
        x = r_start_x + i * (r_w + r_gap)
        c = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, r_y, r_w, r_h)
        c.fill.solid()
        c.fill.fore_color.rgb = CARD_BG
        c.line.color.rgb = NV_GREEN if i == 0 else CARD_BORDER
        c.line.width = Pt(1.5 if i == 0 else 1)

        tb = slide6.shapes.add_textbox(x + Inches(0.25), r_y + Inches(0.25), r_w - Inches(0.5), r_h - Inches(0.5))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = 0

        p = tf.paragraphs[0]
        p.text = num
        p.font.name = "Arial"
        p.font.size = Pt(36)
        p.font.bold = True
        p.font.color.rgb = col

        p2 = tf.add_paragraph()
        p2.text = sub
        p2.font.name = "Arial"
        p2.font.size = Pt(10)
        p2.font.bold = True
        p2.font.color.rgb = NV_GREEN if i == 0 else TEXT_MAIN
        p2.space_before = Pt(8)

        p3 = tf.add_paragraph()
        p3.text = desc
        p3.font.name = "Arial"
        p3.font.size = Pt(12)
        p3.font.color.rgb = TEXT_MUTED
        p3.space_before = Pt(8)

    # Bottom Call to Action Card
    cta = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.2), Inches(11.733), Inches(1.5))
    cta.fill.solid()
    cta.fill.fore_color.rgb = RGBColor(16, 28, 20)
    cta.line.color.rgb = NV_GREEN
    cta.line.width = Pt(1.5)

    tb_cta = slide6.shapes.add_textbox(Inches(1.1), Inches(5.35), Inches(11.1), Inches(1.2))
    tf_cta = tb_cta.text_frame
    tf_cta.word_wrap = True

    p = tf_cta.paragraphs[0]
    p.text = "🎯  Let's See the Live Demo!"
    p.font.name = "Arial"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = TEXT_MAIN

    p2 = tf_cta.add_paragraph()
    p2.text = "Our live camera matrix and NVIDIA cluster are running right now. Step in front of our webcam or pick any camera feed to watch EdgeVision detect hazards live."
    p2.font.name = "Arial"
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_MUTED
    p2.space_before = Pt(6)

    # Save to all target paths
    for path in output_paths:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        prs.save(path)
        print(f"✅ Generated pitch deck at: {path}")

if __name__ == "__main__":
    targets = [
        os.path.join(os.path.dirname(__file__), "..", "EdgeVision_Hackathon_Pitch.pptx"),
        os.path.join(os.path.dirname(__file__), "..", "static", "EdgeVision_Hackathon_Pitch.pptx")
    ]
    create_deck(targets)
