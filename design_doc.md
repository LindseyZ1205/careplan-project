# CarePlan Auto-Generation System — Design Document

## 1. Project Overview

### 1.1 Background
A specialty pharmacy needs an automated tool to generate care plans for patients. Currently, pharmacists spend 20–40 minutes per patient manually creating care plans. These care plans are required for compliance and reimbursement from Medicare and pharma companies. The pharmacy is short-staffed and backlogged.

### 1.2 Goal
Build a web-based system that allows CVS medical assistants to input patient information and automatically generate professional care plans using an LLM (Large Language Model).

### 1.3 Target Users
- **Primary users:** CVS medical assistants / pharmacists
- **NOT end users:** Patients do not interact with the system
- **Workflow:** Medical assistant inputs data → system generates care plan → assistant prints and gives to patient

---

## 2. Core Features

| Feature | Priority | Description |
|---------|----------|-------------|
| Web form input | Must-have | Medical assistant inputs patient info via a web form |
| Input validation | Must-have | All fields validated (NPI = 10 digits, MRN = 6 digits, ICD-10 format, etc.) |
| Duplicate order detection | Must-have | Detect and warn/block duplicate orders |
| Duplicate patient detection | Must-have | Detect and warn/block duplicate patients |
| Provider deduplication | Must-have | Provider (identified by NPI) can only be entered once |
| Care Plan generation (LLM) | Must-have | Call LLM to generate care plan as downloadable text file |
| Care Plan download | Must-have | User can download the generated care plan |
| Export for reporting | Must-have | Quick export for pharma reporting |

---

## 3. Data Model (Input Fields)

| Field | Type | Validation |
|-------|------|------------|
| Patient First Name | string | Required, alphabetic |
| Patient Last Name | string | Required, alphabetic |
| Referring Provider | string | Required |
| Referring Provider NPI | string | Must be exactly 10 digits |
| Patient MRN | string | Must be exactly 6 digits, unique |
| Patient Primary Diagnosis | string | Must be valid ICD-10 code |
| Medication Name | string | Required |
| Additional Diagnosis | list of strings | Each must be valid ICD-10 code |
| Medication History | list of strings | Optional |
| Patient Records | string or PDF | Optional |

---

## 4. Care Plan Output

One care plan corresponds to **one order (one medication)**.

Output must include the following four sections:
1. **Problem List / Drug Therapy Problems (DTPs)**
2. **Goals (SMART format)**
3. **Pharmacist Interventions / Plan**
4. **Monitoring Plan & Lab Schedule**

---

## 5. Duplicate Detection Rules

### 5.1 Order Duplicates

| Scenario | Action | Reason |
|----------|--------|--------|
| Same patient + same medication + **same day** | ❌ ERROR — must block | Definitely a duplicate submission |
| Same patient + same medication + **different day** | ⚠️ WARNING — allow with confirmation | Could be a refill |

### 5.2 Patient Duplicates

| Scenario | Action | Reason |
|----------|--------|--------|
| Same MRN + same name & DOB | ✅ Reuse existing patient | Normal |
| Same MRN + different name or DOB | ⚠️ WARNING — allow with confirmation | Possible data entry error |
| Same name + DOB + different MRN | ⚠️ WARNING — allow with confirmation | Could be the same person |

### 5.3 Provider Duplicates

| Scenario | Action | Reason |
|----------|--------|--------|
| Same NPI + same name | ✅ Reuse existing provider | Normal |
| Same NPI + different name | ❌ ERROR — must correct | NPI is a nationally unique identifier |

---

## 6. Error vs Warning Design

- **ERROR (block):** User cannot proceed. Must fix the issue before submitting.
- **WARNING (confirm):** User is shown a warning message and can choose to confirm and continue, or go back and fix.

---

## 7. Tech Stack (Planned)

| Category | Technology | Purpose |
|----------|-----------|---------|
| Backend | Python, Django, Django REST Framework | Web framework, API |
| Frontend | React, JavaScript | User interface |
| Database | PostgreSQL | Data storage |
| Async Tasks (local) | Celery, Redis | Background task processing |
| Async Tasks (AWS) | SQS, Lambda | Production background tasks |
| AI/LLM | Claude API or OpenAI API | Care plan generation |
| Containerization | Docker, Docker Compose | Local dev + deployment |
| Cloud | AWS (EC2, Lambda, RDS, SQS, S3) | Production environment |
| Infrastructure | Terraform | Infrastructure as Code |
| Monitoring | Prometheus, Grafana | Metrics & visualization |
| Testing | pytest | Unit & integration tests |

---

## 8. Production-Ready Requirements

- Every input is validated
- Integrity rules always enforce consistency
- Errors are safe, clear, and contained (no stack traces or PHI exposed)
- Code is modular and navigable
- Critical logic is covered by automated tests (unit + integration)
- Project runs end-to-end out of the box (Docker)

---

## 9. Open Questions / Future Considerations

- Support for additional data sources with different formats (JSON, XML)?
- Rate limiting for LLM API calls?
- Role-based access control (different permission levels)?
- Audit logging for compliance?
- Care plan versioning (edit/regenerate)?

---

*Document created: Day 1 — Requirements Analysis Phase*
