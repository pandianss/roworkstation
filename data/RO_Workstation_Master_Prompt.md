# RO Workstation — Master Build Prompt
> Paste this entire prompt into any code-generation AI (Claude, GPT-4, Gemini, etc.)
> to scaffold the complete Regional Office Workstation application.

---

## ROLE & OBJECTIVE

You are an expert Python/Streamlit developer specialising in enterprise applications
for Indian public sector banking. Build a production-grade, multi-department
**Regional Office (RO) Workstation** — a single internal web application that serves
as the one-stop workstation for all departments of a PSB (Public Sector Bank)
Regional Office in India.

---

## DEPLOYMENT CONSTRAINT — CLOSED NETWORK (READ FIRST)

This application will be deployed on an **air-gapped internal bank network**
with NO internet access at runtime. Every architectural and code decision must
treat this as the primary constraint.

Rules that follow from this:
- **No CDN imports** anywhere — no cdnjs.cloudflare.com, esm.sh, unpkg.com, or
  any external URL in HTML components or Python code.
- **No cloud LLM APIs** — no OpenAI, Gemini, Anthropic, or any external AI API.
  Use Ollama running on the local server instead.
- **No external embedding APIs** — use sentence-transformers with a locally stored
  model file (`assets/models/all-MiniLM-L6-v2`).
- **No SMS or WhatsApp notifications** — these require internet. Use in-app alerts
  and internal bank SMTP email only.
- **No cloud storage** — all files on local disk or NFS mount.
- **No external data lookups at runtime** (CIBIL, MCA, CERSAI) — mark as stubs
  with `OFFLINE_MODE=true` flag.
- Plotly (bundled with Streamlit), pandas, openpyxl, python-docx, reportlab,
  ChromaDB, FAISS, SQLite, PostgreSQL — all fully offline once installed. Use these.
- Build an **offline wheel cache** (`./wheels/`) for pip installation on the server.
- The Docker image must be built on an internet machine, exported as a `.tar.gz`,
  and loaded on the internal server — no `docker pull` at the bank.

---

## BANKING CONTEXT — INDIAN PSB REGIONAL OFFICE

A PSB Regional Office (RO) sits between Head Office (HO) and branches.
It supervises 30–80 branches in a geographic territory and is responsible for:

- Monitoring PSL (Priority Sector Lending) targets mandated by RBI
  (40% of ANBC: 18% Agriculture, 7.5% Micro, 10% Weaker Sections)
- Reporting periodic returns to HO / RBI / NABARD / IBA
- Monitoring NPA (Non-Performing Assets), SMA-0/1/2 accounts
- Ensuring KYC/AML compliance and RBI circular implementation
- Coordinating government schemes: PMJDY, PM-SVANidhi, PMEGP, MUDRA, KCC
- Managing HR transfers, postings, and training of branch staff
- Conducting inspections, risk audits, and legal follow-ups

---

## TECH STACK

| Layer | Technology | Notes |
|---|---|---|
| Framework | Streamlit >= 1.35 | Serves own JS/CSS — no CDN needed |
| Language | Python 3.11+ | |
| Data | pandas, numpy | |
| Charts | Plotly (primary), Altair (secondary) | Both offline via Streamlit |
| Local LLM | Ollama + Mistral 7B / Phi-3 Mini / Llama 3.1 8B | REST API at localhost:11434 |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Stored in assets/models/ |
| Vector store | ChromaDB (local persistent) or FAISS | Fully offline |
| RAG | LangChain (local chains, no cloud) | |
| Database | SQLAlchemy + SQLite (dev) / PostgreSQL (prod) | |
| Export | reportlab, openpyxl, python-docx | |
| Auth | streamlit-authenticator + YAML user store | |
| Notifications | st.toast + internal SMTP (bank mail server) | No SMS/WhatsApp |
| Deployment | Docker Compose (offline image transfer) | |
| Config | python-dotenv, pyyaml | |

### Recommended server hardware
- **Minimum** (Phi-3 Mini 4-bit): 4-core CPU, 16 GB RAM, 50 GB disk
- **Recommended** (Mistral 7B): 8-core CPU, 32 GB RAM, 100 GB disk
- **Optional GPU**: Any NVIDIA RTX 30/40 series with 8 GB+ VRAM
  (Ollama auto-detects; responses 3–5× faster)

---

## PROJECT STRUCTURE

```
ro_workstation/
│
├── app.py                          ← Entry point, sidebar nav, login, task badges
│
├── pages/
│   ├── home.py                     ← "My Day" dashboard (first page after login)
│   ├── fi.py                       ← Financial Inclusion
│   ├── plan.py                     ← Planning
│   ├── arid.py                     ← Agriculture & Rural Infra Dev
│   ├── hrdd.py                     ← Human Resources
│   ├── gad.py                      ← General Administration
│   ├── crmd.py                     ← Credit Monitoring
│   ├── com.py                      ← Compliance
│   ├── mkt.py                      ← Marketing
│   ├── law.py                      ← Law Department
│   ├── ins.py                      ← Inspection
│   ├── rsk.py                      ← Risk Management
│   ├── sme.py                      ← MSME Division
│   ├── ret.py                      ← Retail Department
│   ├── rcc.py                      ← Regional Computer Centre
│   ├── visits.py                   ← Branch Visit Manager
│   ├── comms.py                    ← Staff Communications Hub
│   ├── meetings.py                 ← Meeting Manager
│   ├── research.py                 ← AI Research Assistant (local RAG)
│   ├── scorecard.py                ← Branch Scorecard & Rankings
│   ├── grievances.py               ← Grievance & Ombudsman Tracker
│   ├── calculators.py              ← Banking Calculator Suite
│   ├── vendors.py                  ← Vendor & Empanelment Register
│   ├── vault.py                    ← Document Vault
│   └── profile.py                  ← Profile & Settings
│
├── modules/
│   ├── notes/
│   │   ├── generator.py            ← AI note drafting engine (calls Ollama)
│   │   ├── templates.py            ← 50+ dept-wise note templates
│   │   └── prompts.py              ← System prompts per department
│   │
│   ├── returns/
│   │   ├── builder.py              ← Return form renderer + validation
│   │   ├── scheduler.py            ← Due-date calendar, auto-task creation
│   │   └── formats/                ← YAML schemas per return type
│   │
│   ├── analytics/
│   │   ├── kpi.py                  ← KPI tile builder
│   │   ├── charts.py               ← Plotly wrappers (branch-wise, trend)
│   │   └── mis.py                  ← MIS report generator
│   │
│   ├── tasks/
│   │   ├── engine.py               ← CRUD, priority scoring, NLP parser
│   │   ├── scheduler.py            ← Auto-task generators (SMA, returns, circulars)
│   │   ├── reminders.py            ← In-app + internal SMTP notifications
│   │   ├── models.py               ← SQLAlchemy Task and Reminder models
│   │   └── hooks.py                ← Dept-specific auto-task triggers
│   │
│   ├── knowledge/
│   │   ├── indexer.py              ← PDF ingestion, chunking, local embeddings
│   │   ├── search.py               ← Hybrid semantic + keyword search
│   │   └── qa.py                   ← Local RAG Q&A chain with source citation
│   │
│   ├── llm/
│   │   ├── client.py               ← Ollama wrapper (localhost:11434)
│   │   ├── embeddings.py           ← Local sentence-transformers loader
│   │   ├── rag.py                  ← RAG chain over local ChromaDB
│   │   └── chain.py                ← LangChain chains per department
│   │
│   ├── integrations/
│   │   ├── cbs.py                  ← CBS API connector (stub if offline)
│   │   ├── hrms.py                 ← HRMS connector (stub if offline)
│   │   └── external_stub.py        ← CIBIL/MCA/CERSAI stubs with OFFLINE flag
│   │
│   └── utils/
│       ├── auth.py                 ← RBAC (RO_Admin, Dept_Head, Officer, Branch)
│       ├── export.py               ← PDF/Excel/Word export with letterhead
│       ├── audit.py                ← Immutable activity log
│       ├── validators.py           ← Data validation helpers
│       └── notifications.py        ← In-app toast + internal SMTP dispatch
│
├── config/
│   ├── dept_config.yaml            ← Dept metadata, KPIs, returns schedule
│   ├── prompts.yaml                ← Ollama system prompts per department
│   ├── roles.yaml                  ← RBAC role definitions
│   └── scorecard.yaml              ← Branch KPI weights
│
├── assets/
│   ├── logo.png                    ← Bank logo
│   ├── custom.css                  ← Bank brand colours, sidebar styling
│   ├── models/
│   │   └── all-MiniLM-L6-v2/      ← Local sentence-transformers model
│   ├── js/                         ← Any bundled JS (downloaded offline)
│   └── circular_templates/         ← PDF templates for standard formats
│
├── data/
│   ├── db.py                       ← SQLAlchemy models and engine
│   ├── chroma_db/                  ← ChromaDB persistent vector store
│   ├── uploads/                    ← Uploaded CSVs, PDFs
│   └── exports/                    ← Generated reports
│
├── mock_data/
│   └── *.py                        ← Realistic mock data for all 14 departments
│
├── tests/
│   ├── test_tasks.py
│   ├── test_returns.py
│   └── test_notes.py
│
├── wheels/                         ← Offline pip wheel cache
├── ollama_models/                  ← Pre-downloaded Ollama model files (.gguf)
├── requirements.txt                ← All deps with pinned versions
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## EACH DEPARTMENT PAGE — STANDARD ANATOMY

Every `pages/dept.py` follows this layout:

```
Tabs: [Dashboard] [Note Generator] [Returns] [Analytics] [Circulars] [Drafts]
```

**Dashboard tab**: KPI tiles (target vs achievement), branch-wise data table,
trend chart, alerts for the department.

**Note Generator tab**: AI-powered note drafting via Ollama. Input: note type
selector, subject, key data points, tone. Output: structured office note in
standard PSB format (Ref No / Date / To / Subject / Background / Analysis /
Recommendations / Approval sought). 50+ pre-loaded templates per department.
RAG-grounded on uploaded HO/RBI documents.

**Returns tab**: All periodic returns for this department. Auto-filled from CBS
data upload (CSV/Excel). Validation rules. Status: Draft / Under Review /
Submitted / Acknowledged. Export to Excel/PDF with letterhead.

**Analytics tab**: Plotly charts — branch-wise bar/line/scatter, YOY/MOM trends,
target vs achievement gauges, district heatmap.

**Circulars tab**: RBI/HO circulars tagged to this department. Compliance status
per circular per branch. AI summary of each circular (local Ollama).

**Drafts tab**: Saved but not submitted notes and returns. Linked to task engine.

---

## DEPARTMENTS — FULL SPECIFICATIONS

### 1. FI — Financial Inclusion

**Dashboard KPIs**:
- PMJDY accounts opened (branch-wise), zero-balance %, active %
- BC (Business Correspondent) outlet count vs target
- Aadhaar seeding %, RuPay card activation %
- PM-SVANidhi, PM Vishwakarma disbursements

**Returns**:
- Weekly FI return to HO (branch-wise BC performance)
- Monthly PMJDY return (DFS template format)
- Quarterly DBT credit summary

**Note Generator prompts**:
- "Generate an office note for low BC utilisation at [branch]"
- "Draft a circular to branches on PMJDY account activation drive"
- "Prepare FI performance review note for RO monthly meeting"

---

### 2. PLAN — Planning

**Dashboard KPIs**:
- Business plan target vs achievement (deposits, advances, CASA)
- CD ratio, YOY growth, budget utilisation %
- Branch-wise ranking table

**Returns**:
- Monthly business plan MIS to HO
- Quarterly Performance Review (QPR)
- Annual Business Plan (ABP) input template

**Note Generator prompts**:
- "Draft a note analysing underperformance of [branch] against ABP"
- "Generate talking points for the Regional Manager's quarterly review"

---

### 3. ARID — Agriculture & Rural Infrastructure Development

**Dashboard KPIs**:
- Agri credit outstanding vs RBI sub-target (18% of ANBC)
- KCC (Kisan Credit Card) sanctions, renewals, overdues
- NABARD refinance utilisation, RIDF portfolio
- SHG credit linkage, JLG counts

**Returns**:
- Monthly agri return to HO (KCC, crop loans, allied activities)
- NABARD quarterly return
- SHG progress report

**Note Generator prompts**:
- "Draft office note for shortfall in KCC renewal at [branch]"
- "Generate a note on NABARD inspection compliance for agri portfolio"

---

### 4. HRDD — Human Resources Development

**Dashboard KPIs**:
- Staff strength vs sanctioned posts (officers / clerks / sub-staff)
- Pending transfer requests, vacancy positions
- Training nominations pending and completed (JAIIB/CAIIB tracking)
- Disciplinary cases pending (NDA count)

**Returns**:
- Monthly HR return to HO (vacancies, transfers, retirements)
- Training MIS

**Note Generator prompts**:
- "Draft transfer/posting order for [employee name/ID]"
- "Generate a note recommending promotion for eligible officers"
- "Draft memo on JAIIB/CAIIB compliance for branch staff"
- "Generate charge handover report for [officer] transferring from [branch]"

---

### 5. GAD — General Administration

**Dashboard KPIs**:
- Premises lease renewals due, pending approvals
- Security staff positions, cash van schedule
- Stationery / consumable budget utilisation
- Vehicle maintenance log, insurance renewals

**Returns**:
- Monthly premises return
- Quarterly admin expense report

**Note Generator prompts**:
- "Draft lease renewal recommendation for [branch] premises"
- "Generate a note for purchase of new equipment under capex budget"

---

### 6. CRMD — Credit Monitoring *(reference implementation — build this first)*

**Dashboard KPIs**:
- NPA (Gross / Net) %, branch-wise NPA table
- SMA-0 / SMA-1 / SMA-2 live tracker (30/60/90 day buckets)
- Recovery vs target, written-off accounts with suit status
- SARFAESI / DRT / Lok Adalat action tracker

**Returns**:
- Weekly NPA/SMA flash report to HO
- Monthly Credit Monitoring Return (CMR)
- Quarterly IRAC review note

**Note Generator prompts**:
- "Draft a structured office note on NPA accounts in [branch] with SARFAESI action recommended"
- "Generate CMR narrative for this month's data [paste table]"
- "Draft a review note for top 10 NPA borrowers"

**AI Analytics**:
- SMA-to-NPA slippage probability (rule-based: days overdue + sector + collateral type)
- Vintage analysis of overdue accounts
- Recovery projection chart

---

### 7. COM — Compliance

**Dashboard KPIs**:
- RBI circular compliance status (open / closed / in-progress)
- Audit observation pending closures (IS audit, concurrent, statutory)
- KYC/AML exceptions branch-wise
- PMLA / CTR / STR submissions tracker

**Returns**:
- Monthly compliance return to HO
- Quarterly KYC compliance certificate

**Note Generator prompts**:
- "Generate compliance note for RBI circular [paste circular number/text]"
- "Draft IS audit compliance response for observation [paste observation]"
- "Write a note summarising open compliance items for RM's review"

---

### 8. MKT — Marketing

**Dashboard KPIs**:
- CASA mobilisation vs target (SA, CA, TD new accounts)
- Cross-sell counts (insurance, mutual funds, credit cards)
- Lead conversion rate, campaign performance
- Customer complaint count trend

**Returns**:
- Monthly marketing MIS
- Campaign performance report

**Note Generator prompts**:
- "Draft a branch motivation circular for CASA drive"
- "Generate a product note on [scheme name] for branch staff awareness"

---

### 9. LAW — Law Department

**Dashboard KPIs**:
- Active suit-filed cases (count, amount involved)
- DRT / DRAT / High Court matters pending
- Recovery in suit-filed accounts (YTD)
- Legal notice issued vs replies received
- Court hearing calendar (next 30 days)

**Returns**:
- Monthly legal MIS to HO
- Court-date tracker (calendar view)

**Note Generator prompts**:
- "Draft a reference note to panel advocate for [borrower account]"
- "Generate a note summarising status of top 10 legal cases"
- "Draft legal opinion request for [specific scenario]"

---

### 10. INS — Inspection Department

**Dashboard KPIs**:
- Annual inspection completion % (branches due vs done)
- Concurrent audit observations: critical / major / minor counts
- Inspection rating distribution (branch-wise)
- Fraud/irregularity cases detected

**Returns**:
- Monthly inspection progress report
- Quarterly fraud monitoring return

**Note Generator prompts**:
- "Draft inspection findings note for [branch] based on these observations: [paste]"
- "Generate a note for RO review of recurring audit exceptions"

---

### 11. RSK — Risk Management

**Dashboard KPIs**:
- Credit Risk: NPA ratio, PCR (Provision Coverage Ratio), CAR
- Operational Risk: fraud count, cyber incidents, near misses
- KRI (Key Risk Indicator) dashboard (Red / Amber / Green)

**Returns**:
- Monthly risk report to HO
- ICAAP contribution data

**Note Generator prompts**:
- "Draft a risk note on [specific risk event] for RM approval"
- "Generate monthly risk dashboard commentary from this data [paste]"

---

### 12. SME — MSME Division

**Dashboard KPIs**:
- MSME credit outstanding (Micro / Small / Medium split)
- MUDRA (Shishu / Kishore / Tarun) disbursements vs target
- PMEGP, CGTMSE-covered portfolio, ECLGS exposure
- MSME NPA % vs overall NPA

**Returns**:
- Monthly MSME return to HO
- MUDRA progress report
- CGTMSE claim status tracker

**Note Generator prompts**:
- "Draft a note for expanding MSME credit in [sector/district]"
- "Generate MUDRA campaign circular for branches"
- "Write a note on MSME cluster approach for [industrial cluster]"

---

### 13. RET — Retail Department

**Dashboard KPIs**:
- Home loan / vehicle loan / personal loan: sanctions vs target
- Education loan portfolio, NPA in retail
- Pre-approved offers utilisation (PAPL)
- PMAY subsidy disbursements

**Returns**:
- Monthly retail MIS
- Home loan subsidy (PMAY) report

**Note Generator prompts**:
- "Draft a note on home loan drive targeting [segment]"
- "Generate retail product awareness circular for branches"

---

### 14. RCC — Regional Computer Centre

**Dashboard KPIs**:
- CBS uptime %, ATM uptime % (branch-wise)
- Open IT tickets (P1/P2/P3 counts, ageing)
- Cyber security incidents, patch compliance %
- Internet Banking / Mobile Banking onboarding counts

**Returns**:
- Weekly IT/CBS incident report
- Monthly ATM reconciliation return

**Note Generator prompts**:
- "Draft a note on CBS downtime incident at [branch] on [date]"
- "Generate an advisory circular on password policy compliance"
- "Write a note recommending ATM upgrade at [location]"

---

## MODULE 15 — TASKS & DAILY REMINDERS

### Database models (`modules/tasks/models.py`)

```python
class Task(Base):
    id              : UUID (PK)
    title           : str
    description     : str
    dept            : str           # "FI", "CRMD", "ALL" etc.
    task_type       : Enum          # RETURN_DUE | CIRCULAR_ACTION |
                                    # SMA_ALERT | INSPECTION_DUE |
                                    # PERSONAL | ASSIGNED | MEETING_PREP
    priority        : Enum(P1–P4)
    due_date        : date
    due_time        : time | None
    assigned_to     : str           # user_id
    assigned_by     : str | None    # user_id or "SYSTEM"
    status          : Enum          # OPEN | IN_PROGRESS | DONE | SNOOZED
    source          : str           # "returns_scheduler" | "user" | "crmd_sma_monitor"
    linked_id       : str | None    # FK to return_id / circular_id
    created_at      : datetime
    snoozed_until   : date | None
    recurrence      : str | None    # "monthly" | "weekly" | cron expr

class Reminder(Base):
    id              : UUID (PK)
    task_id         : UUID (FK)
    remind_at       : datetime
    channel         : Enum          # APP | EMAIL
    sent            : bool
    acknowledged    : bool
```

### Priority scoring rules (`modules/tasks/engine.py`)

**P1 — Critical (red)**:
Return overdue · SMA-2 account slipped to NPA · RBI circular compliance
deadline = today · Task manually escalated by RM.

**P2 — High (orange)**:
Return due in 1–2 days · Circular compliance due within 3 days ·
Inspection of branch due this week · Court hearing tomorrow (LAW).

**P3 — Normal (blue)**:
Return due in 3–7 days · Branch visit scheduled this week ·
Meeting prep task · HRDD transfer order due within 7 days.

**P4 — Low (grey)**:
Return due > 7 days · Personal to-dos · Saved drafts · Training nominations.

### Auto-task generators (`modules/tasks/scheduler.py`)

```python
def generate_return_tasks():
    """
    Read config/dept_config.yaml for all returns and their due dates.
    Create a Task for each return due within 14 days.
    Deduplicate by linked_id — never create duplicate tasks.
    Score priority automatically from days remaining.
    """

def generate_sma_tasks():
    """
    For each account that moved from SMA-1 to SMA-2 since last check,
    create a P1 Task assigned to CRMD dept head:
    "SMA-2 alert: [Borrower] A/c [number] — [Branch] — ₹[amount] cr"
    """

def generate_circular_tasks():
    """
    When a new circular is uploaded in COM module,
    auto-create tasks for each tagged department with
    due_date = compliance_due_date (extract via local LLM if unstructured).
    """

def generate_inspection_tasks():
    """
    From INS inspection schedule, create tasks at:
    T-30 days: "Prepare pre-inspection checklist for [Branch]"
    T-14 days: "Dispatch inspection team to [Branch]"
    T-0 days:  "Upload inspection report for [Branch]"
    """

def generate_legal_tasks():
    """
    From LAW court date tracker, create P2 tasks 2 days before
    each hearing: "Brief panel advocate for [borrower] at [court]"
    """
```

### "My Day" home page (`pages/home.py`)

Layout (top to bottom):
1. **Greeting strip** — "Good morning, [Name]. You have [N] tasks today, [X] overdue."
2. **P1 alert banner** — red banner listing all critical items (only if P1 tasks exist)
3. **Today's task list** — grouped: Overdue / Due Today / Due This Week.
   Each card: [priority badge] [dept tag] [title] [due] [source]
   Buttons: [✓ Mark Done] [→ Open Dept Page] [⏰ Snooze] [✏ Edit]
4. **Quick-add bar** — "Add a task…" with due date + dept + Add.
   Parse natural language via local Ollama into structured Task JSON.
5. **Return deadline strip** — horizontal 7-day mini-calendar with coloured dots.
6. **Dept task summary** — row of 14 mini-cards; green/amber/red by overdue count.
7. **Recent activity feed** — last 20 actions with timestamps.

### Sidebar integration

Above the navigation menu in `app.py`:
```
[📋 My Tasks  🔴 3]   ← clickable, opens home.py
```
Each dept menu item shows a badge if open/overdue tasks exist:
```
FI    🔴 2
CRMD  🔴 1
COM   🟡 4
```

### Snooze and escalation rules
- Snooze options: 1 day, 3 days, custom date
- **P1 tasks cannot be snoozed more than 1 day**
- If any task is snoozed past its due_date → auto-escalate to P1
- If a return task is overdue by 3+ days → auto-assign copy to RM as P1

### Returns calendar (`config/dept_config.yaml` — `returns:` block)

```yaml
FI:
  returns:
    - name: "Monthly PMJDY return"
      frequency: monthly
      due_day: 7
      recipient: HO
      format: excel
      reminder_days: [7, 3, 1]
    - name: "Weekly BC performance return"
      frequency: weekly
      due_day: monday
      reminder_days: [1]

CRMD:
  returns:
    - name: "Weekly NPA/SMA flash report"
      frequency: weekly
      due_day: friday
      reminder_days: [1]
    - name: "Monthly credit monitoring return (CMR)"
      frequency: monthly
      due_day: 10
      reminder_days: [7, 3, 1]
    - name: "Quarterly IRAC review note"
      frequency: quarterly
      due_month_day: "Q+10"
      reminder_days: [14, 7, 3]
# ... repeat for all 14 departments
```

---

## MODULE 16 — BRANCH VISIT MANAGER (`pages/visits.py`)

- Visit calendar with branch-wise scheduling
- Pre-visit checklist auto-built from: last inspection rating +
  open NPA accounts + pending compliance items for that branch
- Mobile-friendly on-site observation entry
- AI note generator → formal visit report via Ollama:
  (Background / Observations / Positives / Concerns /
   Instructions issued / Follow-up date)
- Visit history per branch, searchable
- RM approval workflow with digital sign-off

---

## MODULE 17 — STAFF COMMUNICATIONS HUB (`pages/comms.py`)

- Internal notice board: pinned + archived notices
- Branch-wise read-receipt (delivery confirmation)
- Notices linked to Compliance circular tracker
- Searchable archive by date / dept / subject
- AI-assisted notice drafting via Ollama
- No external integration needed — fully local

---

## MODULE 18 — MEETING MANAGER (`pages/meetings.py`)

Meeting types: Weekly HOD · QPR · Monthly RO · Ad hoc

- Agenda builder with per-department input slots
- Attendance tracker
- AI-drafted minutes from bullet points (local Ollama):
  Format: Agenda → Discussion → Decision → Action Points → Next Meeting
- Action points auto-convert to Tasks (Module 15)
- PDF export with bank letterhead (reportlab)

---

## MODULE 19 — KNOWLEDGE BASE (`modules/knowledge/`)

```python
# indexer.py — runs offline, no internet
from sentence_transformers import SentenceTransformer
import chromadb

MODEL_PATH = "assets/models/all-MiniLM-L6-v2"

def index_document(pdf_path: str, dept_tags: list[str]):
    """
    Chunk PDF into 512-token segments.
    Generate embeddings using local SentenceTransformer.
    Store in ChromaDB with metadata: dept, circular_number, date, source.
    """

# qa.py — RAG Q&A using local Ollama
def answer_question(query: str, dept_filter: str = None) -> dict:
    """
    1. Embed query with local model
    2. Retrieve top-5 chunks from ChromaDB
    3. Pass chunks + query to Ollama with citation prompt
    4. Return: { answer: str, sources: list[{doc, page, excerpt}] }
    """
```

Features:
- Upload RBI master circulars, HO guidelines, IBA instructions (PDF)
- Tag by dept / topic / effective date / circular number
- Hybrid semantic + keyword search
- Every answer cites exact source document and page number
- Accessible from every department page via sidebar widget

**Setup (run once on any machine with the model files):**
```bash
python -c "
from sentence_transformers import SentenceTransformer
m = SentenceTransformer('all-MiniLM-L6-v2')
m.save('assets/models/all-MiniLM-L6-v2')
"
```
After this, the model loads from disk with no internet call.

---

## MODULE 20 — AI RESEARCH ASSISTANT (`pages/research.py`)

Fully feasible on closed network — uses local Ollama + local ChromaDB.

- Multi-turn conversational interface (banking Q&A)
- Grounded in Knowledge Base (Module 19) via RAG
- Synthesises across multiple circulars in one answer
- "Cite source" button on every answer paragraph
- History of past queries per user
- Pre-loaded starter questions per department
- **Framing for bank management**: "All AI processing happens on our own
  servers. No data leaves the bank's network."

---

## MODULE 21 — BRANCH SCORECARD (`pages/scorecard.py`)

KPI weights (configurable in `config/scorecard.yaml`):
- Business growth (deposits + advances): 20%
- PSL achievement (% of ANBC): 20%
- NPA ratio: 20%
- CASA ratio: 10%
- CD ratio: 10%
- Inspection rating: 10%
- Complaint resolution TAT: 5%
- Staff productivity: 5%

Views:
- Ranked table (overall + per-KPI sortable)
- District heatmap (Plotly choropleth using local GeoJSON)
- Peer group comparison (rural / semi-urban / urban branches)
- Monthly and quarterly trend per branch
- Auto-flag outlier branches (> 1.5 SD from peer group mean)

---

## MODULE 22 — GRIEVANCE TRACKER (`pages/grievances.py`)

Complaint sources: Branch walk-in · Email · CPGRAMS · RBI IOS ·
NCRFS · Internal escalation

- TAT clock per complaint category (per RBI guidelines)
- Auto-escalate to RM if TAT − 3 days unresolved (P1 task created)
- RBI Integrated Ombudsman Scheme (IOS) format MIS report
- Branch-wise complaint count and TAT compliance dashboard
- AI-drafted resolution letters via Ollama

---

## MODULE 23 — CALCULATOR SUITE (`pages/calculators.py`)

Build all calculators as interactive Streamlit forms with instant output:

1. **PSL / ANBC Calculator** — input total credit by category;
   output: sub-target achievement %, shortfall amount, projection to March
2. **EMI Calculator** — with prepayment, part-payment, and amortisation table
3. **NPA Provision Calculator** (per IRAC norms):
   - Substandard: 15%
   - Doubtful D1 (< 1 yr): 25%
   - Doubtful D2 (1–3 yr): 40%
   - Doubtful D3 (> 3 yr): 100%
   - Loss: 100%
4. **Interest Subvention (Agri) Working Sheet**
5. **CRAR Estimator** (simplified Tier I + Tier II vs RWA)
6. **PSL Projector** — "At current pace, will we achieve 40% by 31 March?"
7. **Yield to Maturity** on investments
8. **Forex / cross-currency** working sheet

All outputs exportable to Excel with full workings shown (openpyxl).

---

## MODULE 24 — VENDOR & EMPANELMENT REGISTER (`pages/vendors.py`)

Entity types: Panel advocates · Chartered accountants · Valuers
(property/stock) · Security agencies · Insurance companies ·
IT vendors · Courier agencies

- Empanelment expiry alerts at 60 / 30 / 7 days (auto-task created)
- Performance rating after each engagement (1–5 stars + remarks)
- Blacklist / caution flag (visible RO-wide, all departments)
- Assignment to cases/matters (linked to LAW module)
- Contact directory with jurisdiction / district mapping
- Renewal reminder letter auto-drafted via Ollama

---

## MODULE 25 — AUDIT TRAIL (`modules/utils/audit.py`)

Log every event immutably:
- Note drafted / saved / submitted / approved
- Return submitted / acknowledged
- Task created / modified / completed / snoozed
- Circular marked compliant
- File uploaded / downloaded / deleted
- User login / logout / failed login attempt

```python
# Schema
class AuditLog(Base):
    id          : UUID (PK)
    timestamp   : datetime          # UTC, immutable
    user_id     : str
    action      : str               # "NOTE_SUBMITTED", "TASK_CREATED" etc.
    entity_type : str               # "note", "return", "task", "circular"
    entity_id   : str
    old_value   : JSON | None
    new_value   : JSON | None
    ip_address  : str
    session_id  : str
```

- Filterable by date / user / dept / action type
- Export to CSV / PDF for IS audit and inspection purposes
- Minimum 3-year retention (configurable)
- Audit log itself is read-only — no update or delete permitted

---

## MODULE 26 — DOCUMENT VAULT (`pages/vault.py`)

- Every return, note, and letter stored with full version history
- Versions marked "submitted/dispatched" become immutable
- Diff view between any two versions
- Submission record: who sent it, when, to whom, acknowledgement reference
- Linked to Tasks: submitting a return auto-closes the corresponding task
- Role-based access: Officer (own dept only), RM (all), Admin (all + audit)
- Search by: document type · dept · date range · status · author

---

## MODULE 27 — PROFILE & SETTINGS (`pages/profile.py`)

- Default department and home page preference
- Notification channels: App (always) · Email (if internal SMTP available)
- Preferred export format: PDF / Excel / Word
- Saved prompt templates for Note Generator (personal library)
- My Drafts tray (notes not yet submitted)
- My Work History (last 30 / 90 days activity log)
- **Charge Handover Report** — auto-generates a structured handover
  summary of all pending tasks, open returns, active drafts, and
  outstanding legal/inspection items for the incoming officer
  (critical for PSBs where staff transfers are frequent)

---

## CROSS-CUTTING FEATURES

### Authentication & RBAC (`modules/utils/auth.py`)

Roles:
- `RO_Admin` — full access, user management, audit trail
- `RM` (Regional Manager) — all departments, escalations, approvals
- `Dept_Head` — own department + common dashboard + read-only others
- `RO_Officer` — own department only
- `Branch_Manager` — read-only dashboard (their branch data only)

Use `streamlit-authenticator` with YAML user store (no LDAP/AD needed,
but add a config stub for future AD integration via internal network).

### LLM Configuration (`modules/llm/client.py`)

```python
import ollama

class LLMClient:
    def __init__(self):
        self.model    = os.getenv("OLLAMA_MODEL", "mistral")
        self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.client   = ollama.Client(host=self.base_url)

    def generate(self, prompt: str, system: str = "") -> str:
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt}
            ]
        )
        return response["message"]["content"]

    def generate_json(self, prompt: str, system: str = "") -> dict:
        """Force JSON output. Strip markdown fences before parsing."""
        raw = self.generate(prompt, system + "\nRespond ONLY with valid JSON.")
        clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean)
```

### Embedding Configuration (`modules/llm/embeddings.py`)

```python
from sentence_transformers import SentenceTransformer

MODEL_PATH = "assets/models/all-MiniLM-L6-v2"

@st.cache_resource
def get_embedder() -> SentenceTransformer:
    return SentenceTransformer(MODEL_PATH)  # loads from disk, no internet
```

### Offline mode flag

```python
# config/settings.py
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "true").lower() == "true"
```

Use this to disable CIBIL / MCA / CERSAI buttons and show:
*"External lookup unavailable on this network. Please use the designated terminal."*

### No CDN rule — enforced pattern

```python
# For any JS needed in st.components.v1.html():
def load_local_js(filename: str) -> str:
    path = Path("assets/js") / filename
    return path.read_text()

# Use Plotly for all charts — it is bundled with Streamlit, fully offline.
# Only use this pattern for custom HTML components that need additional JS.
```

### Export engine (`modules/utils/export.py`)

- **PDF**: ReportLab with bank letterhead (logo + RO stamp + ref number)
- **Excel**: openpyxl with formatted return templates, coloured headers
- **Word**: python-docx for office notes and formal letters
- All exports include: bank name, RO name, date, prepared by, page numbers

### Notifications (`modules/utils/notifications.py`)

```python
# In-app (always available)
st.toast("⚠ CMR return due tomorrow", icon="⚠")

# Internal email (if SMTP available on bank LAN)
def send_email_digest(to: str, subject: str, body: str):
    import smtplib
    SMTP_HOST = os.getenv("INTERNAL_SMTP_HOST", "mailserver.banklan")
    SMTP_PORT = int(os.getenv("INTERNAL_SMTP_PORT", "25"))
    ...
```

---

## CODING STANDARDS

- `st.session_state` for all stateful data across tabs and reruns
- All Ollama calls wrapped with `st.spinner("Drafting note…")`
- No hardcoded credentials — all secrets via `st.secrets` or `.env`
- `@st.cache_data(ttl=300)` for CBS data loads
- `@st.cache_resource` for LLM client and embedder (load once)
- Every module has a `if __name__ == "__main__":` block for standalone testing
- Docstrings on all public functions
- `mock_data/` fixtures so app runs without CBS connection from day one
- Target: every page renders within 3 seconds on first load with mock data
- No CDN URLs anywhere in the codebase — enforced by a `grep -r "cdnjs\|unpkg\|esm.sh"` pre-commit check

---

## OFFLINE PACKAGE SETUP

### Python wheels (run on internet machine, copy to server)

```bash
# On internet machine:
pip download -r requirements.txt -d ./wheels/

# On bank server (no internet):
pip install --no-index --find-links ./wheels/ -r requirements.txt
```

### Ollama models (run on internet machine, copy to server)

```bash
# On internet machine:
ollama pull mistral          # or phi3, llama3.1
# Copy ~/.ollama/models/ to server's ollama_models/ folder

# On bank server — Ollama loads from local folder, never calls internet
```

### Sentence-transformers model (run on internet machine, copy to server)

```bash
python -c "
from sentence_transformers import SentenceTransformer
m = SentenceTransformer('all-MiniLM-L6-v2')
m.save('assets/models/all-MiniLM-L6-v2')
"
# Copy assets/models/ folder to server
```

---

## DOCKER DEPLOYMENT

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OLLAMA_MODEL=mistral
      - OLLAMA_HOST=http://ollama:11434
      - OFFLINE_MODE=true
      - INTERNAL_SMTP_HOST=mailserver.banklan
      - INTERNAL_SMTP_PORT=25
    volumes:
      - ./data:/app/data
      - ./assets/models:/app/assets/models
    depends_on:
      - ollama
    restart: unless-stopped

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ./ollama_models:/root/.ollama
    restart: unless-stopped
```

```bash
# Build on internet machine, transfer to bank server:
docker compose build
docker save ro-workstation_app ollama/ollama | gzip > ro-workstation.tar.gz

# On bank server:
docker load < ro-workstation.tar.gz
docker compose up -d
```

---

## IMPLEMENTATION PHASES

**Phase 1 — Core workstation** *(build first)*
`app.py` + auth + 14 department pages + Task engine + Returns builder +
Note generator (Ollama) + Mock data for all departments

**Phase 2 — Intelligence layer**
Knowledge Base (local RAG) + AI Research Assistant + Branch Scorecard +
Calculator Suite

**Phase 3 — Operations layer**
Branch Visit Manager + Meeting Manager + Grievance Tracker +
Staff Communications Hub

**Phase 4 — Governance layer**
Audit Trail + Document Vault + Vendor Register +
Profile & Settings + Charge Handover Report

---

## DELIVERABLES — IN ORDER

Generate these files sequentially, confirming completion before moving on:

1.  Full project scaffold (all folders, `__init__.py` files, `requirements.txt`)
2.  `config/dept_config.yaml` — full config for all 14 departments including `returns:` block
3.  `config/prompts.yaml` — Ollama system prompts for all departments
4.  `modules/utils/auth.py` — RBAC implementation
5.  `modules/llm/client.py` — Ollama wrapper
6.  `modules/llm/embeddings.py` — local sentence-transformers loader
7.  `modules/tasks/models.py` + `engine.py` + `scheduler.py`
8.  `pages/home.py` — "My Day" dashboard
9.  `app.py` — sidebar nav with task badges, login, routing
10. `pages/crmd.py` — **complete CRMD reference implementation**
    (NPA dashboard, SMA tracker, AI note generator, CMR return builder)
11. `pages/fi.py` — **complete FI reference implementation**
12. `modules/notes/generator.py` — AI note engine
13. `modules/returns/builder.py` + `scheduler.py`
14. `modules/analytics/charts.py`
15. `modules/knowledge/indexer.py` + `qa.py`
16. `pages/research.py` — AI Research Assistant
17. `pages/scorecard.py` — Branch Scorecard
18. `pages/calculators.py` — full Calculator Suite
19. `pages/visits.py` — Branch Visit Manager
20. `pages/meetings.py` — Meeting Manager
21. `pages/grievances.py` — Grievance Tracker
22. `pages/vault.py` — Document Vault
23. `modules/utils/audit.py` — Audit Trail
24. `pages/vendors.py` — Vendor Register
25. `pages/comms.py` — Staff Comms Hub
26. `pages/profile.py` + Charge Handover Report
27. `mock_data/` — realistic mock data for all 14 departments
28. `docker-compose.yml` + `Dockerfile`
29. `README.md` — setup guide including offline wheel cache and Ollama model setup

---

*End of prompt. All features are designed for air-gapped deployment.
No internet access is required at runtime. All AI processing
occurs on the bank's own servers.*
