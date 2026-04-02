# SmartHR Full Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform SmartHR from a functional Bootstrap app into a commercial-grade, 3D-immersive HR platform with complete dark design system, Three.js visualizations, payroll engine, and jsPDF payslips.

**Architecture:** Flask/Jinja2 server-rendered templates; all UI delivered via static CSS/JS files loaded from CDN and `static/`; no bundler required. Three.js for 3D backgrounds and department globe; Chart.js for glowing dark-theme charts; jsPDF for client-side payslip PDF generation.

**Tech Stack:** Flask 3.x, SQLAlchemy, Three.js r158 (CDN), Chart.js 4.4 (CDN), jsPDF 2.5 (CDN), Google Fonts (Outfit + Inter), Bootstrap 5.3 (CDN)

---

## Files Modified / Created

| File | Action |
|---|---|
| `routes/nlp_routes.py` | CREATE — stub blueprint fixing blocking bug |
| `static/css/style.css` | REWRITE — complete dark design system |
| `static/js/three-bg.js` | CREATE — Three.js particle field for login |
| `static/js/three-globe.js` | CREATE — Three.js 3D department globe for dashboard |
| `static/js/payslip.js` | CREATE — jsPDF payslip generator |
| `templates/base.html` | REWRITE — new sidebar, header, CDN imports |
| `templates/login.html` | REWRITE — glassmorphism + Three.js background |
| `templates/dashboard.html` | REWRITE — 3D KPI cards, dark charts, 3D globe |
| `templates/employees.html` | REWRITE — new table, row hover lift |
| `templates/leave.html` | REWRITE — circular leave indicators |
| `templates/chatbot.html` | REWRITE — floating panel, typing indicator |
| `templates/feedback.html` | REWRITE — mood trend chart |
| `templates/reports.html` | REWRITE — enhanced with PDF export |
| `templates/payroll.html` | CREATE — payroll engine + jsPDF payslips |
| `app.py` | MODIFY — add payroll page route |

---

### Task 1: Fix Blocking Bug — Create nlp_routes.py stub
### Task 2: Rewrite style.css — Full dark design system
### Task 3: Rewrite base.html — New layout with CDN imports
### Task 4: Rewrite login.html — Three.js particle field
### Task 5: Create three-bg.js — Three.js particle animation
### Task 6: Rewrite dashboard.html — 3D KPI cards + dark charts
### Task 7: Create three-globe.js — 3D department globe
### Task 8: Create payroll.html + payslip.js — Payroll engine
### Task 9: Rewrite employees.html — Immersive table
### Task 10: Rewrite leave.html — Circular leave indicators
### Task 11: Rewrite chatbot.html — Immersive chat panel
### Task 12: Rewrite feedback.html — Mood trend chart
### Task 13: Rewrite reports.html — Enhanced reports
### Task 14: Update app.py — Add payroll route
