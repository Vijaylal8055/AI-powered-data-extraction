# 🌿 AI-Powered ESG Data Extraction Engine

An end-to-end **AI-driven ESG & Sustainability data extraction system** designed for **CSRD-aligned reporting**.  
The platform extracts structured ESG indicators from unstructured PDF sustainability reports and stores them in a **traceable, auditable PostgreSQL database**.

---

## 📌 Key Features

- 📄 Upload sustainability reports (PDF)
- 🧠 AI-powered extraction using **Retrieval-Augmented Generation (RAG)**
- 🔍 Semantic search with **FAISS vector database**
- 📊 Extraction of **20 CSRD-relevant ESG indicators**
- 🗄️ Persistent storage in **PostgreSQL** with confidence scoring
- 🔎 Full audit trail: source page, section, and quoted evidence
- ♻️ Idempotent updates (safe reprocessing of reports)

---

## 🏗️ System Architecture

### High-Level Architecture Diagram

User
│
▼
Streamlit Web UI
│
▼
PDF Processing Layer (PyMuPDF)
│
▼
Text Chunking & Embeddings
(OpenAI Embeddings)
│
▼
Vector Store (FAISS)
│
▼
LLM Extraction Engine (GPT-4o)
│
▼
PostgreSQL Database
(sustainability_data)


### Architecture Principles

- **Modular design** – each layer is independently replaceable
- **Traceability-first** – every extracted value links back to its source
- **Accuracy over completeness** – no estimation or hallucination
- **Production-ready** – designed for scaling and audit use cases

---

## ⚙️ Technology Stack

| Layer | Technology |
|------|-----------|
| Frontend | Streamlit |
| PDF Parsing | PyMuPDF |
| AI / NLP | LangChain, GPT-4o |
| Embeddings | OpenAI Embeddings |
| Vector Search | FAISS |
| Backend | Python |
| Database | PostgreSQL |
| DB Driver | psycopg2 |
| Config | python-dotenv |

---

## 📂 Project Structure

.
├── app.py # Streamlit UI
├── extractor.py # Core AI extraction logic
├── requirements.txt # Dependencies
├── .env # Environment variables
└── README.md # Documentation


---

## 🧠 Methodology

### 1️⃣ Extraction Approach (RAG-Based)

The platform uses **Retrieval-Augmented Generation (RAG)** instead of full-document prompting.

**Why RAG?**
- Reduces hallucination
- Improves precision
- Scales to large reports (300+ pages)

**Processing Steps:**
1. Extract text from PDFs using PyMuPDF
2. Split text into overlapping chunks
3. Generate vector embeddings
4. Index chunks using FAISS
5. Retrieve top-K relevant chunks per indicator
6. Prompt GPT-4o with structured output schema
7. Persist extracted data with metadata

---

### 2️⃣ Validation Strategy

Strict rules are enforced to ensure regulatory-grade output:

- ✅ Only **explicitly stated values** are accepted
- ❌ No inference, estimation, or calculation
- ❓ Missing indicators → stored as `NULL`
- 📈 Confidence scores:
  - `1.0` → exact value found
  - `0.5` → partial / ambiguous
  - `0.0` → extraction error

---

## 📊 ESG Indicators Extracted

The system extracts **20 standardized ESG indicators**, including:

- Scope 1, 2, and 3 GHG emissions
- Energy consumption & renewables
- Workforce diversity & gender metrics
- Governance indicators
- Supplier ESG screening metrics

(Indicators are configurable and extensible.)

---

## 🗄️ Database Design

### PostgreSQL Table: `sustainability_data`

```sql
CREATE TABLE IF NOT EXISTS sustainability_data (
    id SERIAL PRIMARY KEY,
    company VARCHAR(100) NOT NULL,
    report_year INTEGER NOT NULL,
    indicator_name VARCHAR(200) NOT NULL,
    value VARCHAR(50),
    unit VARCHAR(50),
    confidence FLOAT DEFAULT 0.0,
    source_page VARCHAR(100),
    source_section VARCHAR(200),
    notes TEXT,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company, report_year, indicator_name)
);

Design Rationale

Composite UNIQUE key → prevents duplicate indicators

Text-based value storage → supports heterogeneous ESG units

Source traceability → audit & regulator ready

Confidence scoring → downstream quality control

🚀 Getting Started
1️⃣ Clone the Repository
git clone <repository-url>
cd esg-ai-extractor

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Configure Environment Variables

Create a .env file:

OPENAI_API_KEY=your_openai_key
PG_DATABASE=huly
PG_USER=postgres
PG_PASSWORD=your_password
PG_HOST=localhost
PG_PORT=5432

4️⃣ Run the Application
streamlit run app.py

Access the app at:
👉 http://localhost:8501

🧪 Usage Workflow

Upload a sustainability report (PDF)

Enter company name and report year

Click Start Extraction

Review extracted indicators

Download CSV (optional)

Data is automatically saved to PostgreSQL

⚠️ Challenges & Limitations

ESG disclosures vary widely across institutions

Inconsistent terminology across reports

Scanned PDFs may reduce text extraction quality

LLM accuracy depends on document clarity

Human review recommended for regulatory submissions

📈 Scalability & Production Readiness

Designed for enterprise-scale deployment:

🐳 Docker-ready architecture

🔄 Async batch processing (Celery / queues)

☁️ Cloud PostgreSQL (AWS RDS / GCP SQL)

🧠 Managed vector databases (Pinecone / OpenSearch)

🔐 Role-based access & audit logging

📅 Multi-year & multi-sector extensibility

🔒 Security Considerations

Secrets managed via environment variables

No long-term storage of raw PDF documents

Database access isolated via credentials

Ready for IAM, VPC, and enterprise security controls

📜 License & Usage

This project is intended for:

ESG analytics

AI agent development

Sustainability consulting

Academic & professional case studies

👤 Author

Vijaylal
AI / ESG Systems Developer
Focus: Responsible AI, Sustainability, Enterprise-Grade AI Pipelines

