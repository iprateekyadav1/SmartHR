"""
seed.py — SmartHR database seeder
===================================
Idempotent: safe to re-run. Drops and recreates all data.
Generates 200 realistic employees with full supporting records.

Run: python seed.py
"""

import os
import random
from datetime import date, datetime, timedelta

from faker import Faker
from app import create_app
from models import db
from models.employee import Employee
from models.user import User
from models.leave import Leave
from models.feedback import Feedback
from models.attendance import Attendance
from models.performance import Performance
from models.leave_balance import LeaveBalance
from nlp.sentiment import sentiment_analyzer

fake = Faker("en_IN")
random.seed(42)

# ── Department + Designation structure ───────────────────────────────────────
DEPARTMENTS = {
    "Engineering":  ["Junior Engineer", "Software Engineer", "Senior Engineer", "Tech Lead", "Engineering Manager", "Director of Engineering"],
    "HR":           ["HR Executive", "HR Specialist", "Senior HR Executive", "HR Business Partner", "HR Manager", "Director of HR"],
    "Finance":      ["Finance Executive", "Financial Analyst", "Senior Analyst", "Finance Manager", "Controller", "Director of Finance"],
    "Marketing":    ["Marketing Executive", "Content Strategist", "Growth Analyst", "Marketing Lead", "Marketing Manager", "Director of Marketing"],
    "Operations":   ["Operations Analyst", "Process Coordinator", "Senior Coordinator", "Operations Lead", "Operations Manager", "Director of Operations"],
    "Sales":        ["Sales Executive", "Account Executive", "Senior Account Executive", "Sales Lead", "Sales Manager", "Director of Sales"],
    "Legal":        ["Legal Intern", "Legal Executive", "Associate Counsel", "Senior Associate", "Legal Manager", "General Counsel"],
    "Design":       ["UI Designer", "UX Designer", "Product Designer", "Senior Designer", "Design Lead", "Director of Design"],
}

# ── Pay grade by designation tier (0=junior → 5=director) ────────────────────
PAY_BANDS = {
    0: (25_000,  40_000),   # Junior
    1: (40_000,  65_000),   # Mid
    2: (65_000,  95_000),   # Senior
    3: (95_000,  130_000),  # Lead
    4: (130_000, 200_000),  # Manager
    5: (200_000, 300_000),  # Director
}

# ── Skills pool (60+ skills, role-weighted) ───────────────────────────────────
SKILL_POOL = {
    "Engineering": [
        "Python", "Java", "Go", "TypeScript", "Rust", "C++",
        "React", "Node.js", "FastAPI", "Django", "Spring Boot",
        "Docker", "Kubernetes", "AWS", "GCP", "Terraform", "CI/CD",
        "PostgreSQL", "MongoDB", "Redis", "Kafka", "GraphQL",
        "Machine Learning", "Data Structures", "System Design",
    ],
    "HR": [
        "Talent Acquisition", "Onboarding", "HRIS", "Compliance",
        "Performance Management", "Employee Relations", "Payroll",
        "Learning & Development", "Workforce Planning", "Labor Law",
        "Conflict Resolution", "Diversity & Inclusion", "ATS Systems",
    ],
    "Finance": [
        "SAP", "Excel", "Financial Modelling", "GST", "Tally",
        "Cost Analysis", "Budgeting", "Forecasting", "Auditing",
        "IFRS", "Risk Management", "Treasury", "P&L Management",
    ],
    "Marketing": [
        "SEO", "SEM", "Content Strategy", "Brand Management",
        "Google Analytics", "HubSpot", "Email Marketing",
        "Social Media", "Copywriting", "A/B Testing", "CRM",
        "Market Research", "Campaign Management", "Figma",
    ],
    "Operations": [
        "Supply Chain", "Process Improvement", "Six Sigma", "Lean",
        "Project Management", "ERP", "Logistics", "Vendor Management",
        "Quality Assurance", "Operations Research", "Jira", "Tableau",
    ],
    "Sales": [
        "B2B Sales", "CRM", "Salesforce", "Negotiation", "Cold Outreach",
        "Account Management", "Pipeline Management", "Lead Generation",
        "Presentation Skills", "Customer Success", "SaaS Sales",
    ],
    "Legal": [
        "Contract Drafting", "Corporate Law", "IP Law", "Compliance",
        "Due Diligence", "Litigation Support", "Employment Law",
        "GDPR", "Legal Research", "Document Review",
    ],
    "Design": [
        "Figma", "Adobe XD", "Sketch", "Illustrator", "Photoshop",
        "Prototyping", "User Research", "Design Systems",
        "Motion Design", "Typography", "Accessibility", "Usability Testing",
    ],
}
# Cross-department skills (anyone can have these)
CROSS_SKILLS = ["Communication", "Leadership", "Problem Solving", "Data Analysis",
                "Stakeholder Management", "Agile", "Scrum", "Presentation"]

# ── Feedback sentence templates (sentiment-varied) ────────────────────────────
FEEDBACK_POSITIVE = [
    "{name} consistently delivers exceptional work and is a true asset to the team.",
    "Outstanding quarter for {name}. Targets exceeded, zero escalations.",
    "{name} brings tremendous energy and initiative to every project.",
    "Highly reliable. {name} handles pressure extremely well and mentors juniors effectively.",
    "Brilliant communicator. {name}'s stakeholder management is exemplary.",
]
FEEDBACK_NEUTRAL = [
    "{name} meets expectations but there is room to take more ownership.",
    "Steady performance this quarter. {name} should focus on upskilling in core areas.",
    "{name} completes assigned tasks but rarely volunteers beyond scope.",
    "Acceptable output. {name} would benefit from more cross-team collaboration.",
]
FEEDBACK_NEGATIVE = [
    "{name} has missed several deadlines this quarter and requires close supervision.",
    "Communication gaps from {name} have caused downstream delays.",
    "{name} is underperforming against targets and a PIP may be warranted.",
    "Recurring attendance issues with {name}. A formal review meeting is recommended.",
]


def _generate_skills(dept: str, tier: int) -> str:
    """Return 4-8 role-appropriate skills as comma-separated string."""
    role_pool = SKILL_POOL.get(dept, [])
    # Senior people get more skills
    count = random.randint(4, 6) if tier <= 1 else random.randint(6, 8)
    picked = random.sample(role_pool, min(count - 1, len(role_pool)))
    cross  = random.sample(CROSS_SKILLS, k=random.randint(1, 3))
    return ", ".join(dict.fromkeys(picked + cross))  # deduplicate, preserve order


def _salary_structure(tier: int):
    lo, hi    = PAY_BANDS[tier]
    salary    = random.randint(lo, hi)
    basic     = round(salary * 0.50)
    hra       = round(basic   * 0.40)
    da        = round(basic   * 0.12)
    pf        = round(basic   * 0.12)
    bonus     = round(basic   * random.uniform(0, 0.20))
    net       = basic + hra + da + bonus - pf
    grades    = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"]
    pay_grade = grades[min(tier, 4)]
    return dict(salary=salary, basic_pay=basic, hra=hra, da=da,
                pf_deduction=pf, net_salary=net, pay_grade=pay_grade)


def _generate_employees(count: int = 200) -> list[Employee]:
    dept_names  = list(DEPARTMENTS.keys())
    # Distribute evenly-ish across departments
    dept_quota  = {d: 0 for d in dept_names}
    per_dept    = count // len(dept_names)
    extra       = count % len(dept_names)
    for d in dept_names:
        dept_quota[d] = per_dept
    for d in dept_names[:extra]:
        dept_quota[d] += 1

    employees = []
    for dept, quota in dept_quota.items():
        desigs = DEPARTMENTS[dept]
        for i in range(quota):
            # Spread seniority: more juniors than directors
            tier_weights = [30, 30, 20, 10, 7, 3]
            tier = random.choices(range(6), weights=tier_weights, k=1)[0]
            tier = min(tier, len(desigs) - 1)

            first = fake.first_name()
            last  = fake.last_name()
            name  = f"{first} {last}"
            local = first.lower().replace(" ", "") + "." + last.lower().replace(" ", "")
            email = f"{local}@smarthr.com"

            sal = _salary_structure(tier)
            join_date = fake.date_between(
                start_date=date.today() - timedelta(days=8 * 365),
                end_date=date.today() - timedelta(days=30),
            )

            emp = Employee(
                name        = name,
                age         = random.randint(22, 58),
                email       = email,
                phone       = fake.phone_number()[:20],
                address     = fake.address().replace("\n", ", ")[:120],
                department  = dept,
                designation = desigs[tier],
                skills      = _generate_skills(dept, tier),
                join_date   = join_date,
                is_active   = True,
                photo       = f"https://api.dicebear.com/7.x/initials/svg?seed={first}{last}",
                **sal,
            )
            employees.append(emp)
            db.session.add(emp)

    db.session.commit()
    return employees


def _generate_attendance(employees: list[Employee]):
    today     = date.today()
    start_day = today - timedelta(days=180)   # 6 months

    batch = []
    for emp in employees:
        day = start_day
        while day <= today:
            if day.weekday() < 5:   # Mon–Fri only
                status = random.choices(
                    ["Present", "Absent", "Half-Day", "Leave"],
                    weights=[85, 5, 5, 5], k=1
                )[0]
                batch.append(Attendance(employee_id=emp.id, date=day, status=status))
            day += timedelta(days=1)

        if len(batch) >= 2000:
            db.session.add_all(batch)
            db.session.flush()
            batch.clear()

    if batch:
        db.session.add_all(batch)
    db.session.commit()


def _generate_performance(employees: list[Employee]):
    quarters = ["Q1-2025", "Q4-2024", "Q3-2024", "Q2-2024"]
    for emp in employees:
        for q in quarters:
            db.session.add(Performance(
                employee_id = emp.id,
                quarter     = q,
                score       = round(random.uniform(2.5, 5.0), 1),
            ))
    db.session.commit()


def _generate_leaves(employees: list[Employee]):
    reasons = [
        "Family function", "Medical appointment", "Personal work",
        "Fever and rest", "Annual vacation", "Child care",
        "Home relocation", "Travel back home", "Bereavement",
    ]
    for emp in employees:
        for _ in range(random.randint(2, 5)):
            offset    = random.randint(10, 170)
            start     = date.today() - timedelta(days=offset)
            duration  = random.randint(1, 3)
            end       = start + timedelta(days=duration - 1)
            db.session.add(Leave(
                employee_id = emp.id,
                leave_type  = random.choice(["CL", "SL", "EL"]),
                start_date  = start,
                end_date    = end,
                reason      = random.choice(reasons),
                status      = random.choices(
                    ["APPROVED", "REJECTED", "PENDING"],
                    weights=[70, 15, 15], k=1
                )[0],
            ))
    db.session.commit()


def _generate_leave_balances(employees: list[Employee]):
    for emp in employees:
        db.session.add(LeaveBalance(
            employee_id  = emp.id,
            casual_leave = random.randint(6, 12),
            sick_leave   = random.randint(4, 8),
            earned_leave = random.randint(8, 15),
        ))
    db.session.commit()


def _generate_feedback(employees: list[Employee]):
    pools = [
        (FEEDBACK_POSITIVE, 0.55),
        (FEEDBACK_NEUTRAL,  0.30),
        (FEEDBACK_NEGATIVE, 0.15),
    ]
    for emp in employees:
        first_name = emp.name.split()[0]
        n = random.randint(1, 3)
        for _ in range(n):
            pool, _ = random.choices(pools, weights=[w for _, w in pools], k=1)[0]
            text    = random.choice(pool).replace("{name}", first_name)
            result  = sentiment_analyzer.analyze(text)
            db.session.add(Feedback(
                employee_id     = emp.id,
                text            = text,
                sentiment_label = result["label"],
                sentiment_score = result["score"],
                submitted_by    = random.choice(["manager", "self"]),
            ))
    db.session.commit()


def _seed_users():
    if User.query.count() > 0:
        return
    admin = User(username="admin",    full_name="System Administrator", email="admin@smarthr.com",    role="admin")
    emp   = User(username="employee", full_name="Demo Employee",        email="employee@smarthr.com", role="employee")
    admin.set_password("Admin@123")
    emp.set_password("Employee@123")
    db.session.add_all([admin, emp])
    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("Dropping existing tables...")
        db.drop_all()
        print("Recreating schema...")
        db.create_all()

        print("Seeding users...")
        _seed_users()

        print("Generating 200 employees...")
        employees = _generate_employees(200)
        print(f"  {len(employees)} employees created")

        print("Generating 6 months of attendance (batched)...")
        _generate_attendance(employees)

        print("Generating quarterly performance scores...")
        _generate_performance(employees)

        print("Generating leave records...")
        _generate_leaves(employees)

        print("Generating leave balances...")
        _generate_leave_balances(employees)

        print("Generating feedback with VADER sentiment scoring...")
        _generate_feedback(employees)

        print()
        print("Database seeded successfully.")
        print(f"  Employees : {Employee.query.count()}")
        print(f"  Attendance: {Attendance.query.count()}")
        print(f"  Leaves    : {Leave.query.count()}")
        print(f"  Feedback  : {Feedback.query.count()}")
