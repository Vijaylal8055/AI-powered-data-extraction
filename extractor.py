# extractor.py - FINAL CASE STUDY VERSION

import os
from typing import List, Dict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import fitz  # PyMuPDF
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY missing")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

INDICATORS = [
    (1, "Total Scope 1 GHG Emissions", "tCO₂e"),
    (2, "Total Scope 2 GHG Emissions", "tCO₂e"),
    (3, "Total Scope 3 GHG Emissions", "tCO₂e"),
    (4, "GHG Emissions Intensity", "tCO₂e per €M revenue"),
    (5, "Total Energy Consumption", "MWh"),
    (6, "Renewable Energy Percentage", "%"),
    (7, "Net Zero Target Year", "year"),
    (8, "Green Financing Volume", "€ millions"),
    (9, "Total Employees", "FTE"),
    (10, "Female Employees", "%"),
    (11, "Gender Pay Gap", "%"),
    (12, "Training Hours per Employee", "hours"),
    (13, "Employee Turnover Rate", "%"),
    (14, "Work-Related Accidents", "count"),
    (15, "Collective Bargaining Coverage", "%"),
    (16, "Board Female Representation", "%"),
    (17, "Board Meetings", "count/year"),
    (18, "Corruption Incidents", "count"),
    (19, "Avg Payment Period to Suppliers", "days"),
    (20, "Suppliers Screened for ESG", "%"),
]

PAGE_RANGES = {
    "AIB Group plc": (48, 117),
    "Groupe BPCE": (100, 350),
    "BBVA": (280, 410),
}

class PyMuPDFLoader:
    def __init__(self, file_path: str, bank_name: str):
        self.file_path = file_path
        self.bank_name = bank_name

    def load(self) -> List[Document]:
        docs = []
        pdf = fitz.open(self.file_path)
        start, end = PAGE_RANGES.get(self.bank_name, (0, pdf.page_count))
        pages = range(start - 1, min(end, pdf.page_count))

        for page_num in pages:
            page = pdf.load_page(page_num)
            text = " ".join(page.get_text("text").split())
            if text.strip():
                docs.append(Document(
                    page_content=text,
                    metadata={"page": page_num + 1}
                ))
        pdf.close()
        return docs

def extract_indicators_from_pdf(pdf_path: str, bank_name: str, report_year: int = 2024) -> List[Dict]:
    print(f"Extracting {bank_name} {report_year}...")

    loader = PyMuPDFLoader(pdf_path, bank_name)
    docs = loader.load()
    if not docs:
        return []

    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", chunk_size=500)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(
        schema={
            "type": "object",
            "properties": {
                "value": {"type": ["string", "null"]},
                "exact_quote": {"type": ["string", "null"]},
                "source_section": {"type": ["string", "null"]}
            },
            "required": ["value"]
        },
        method="json_mode"
    )

    rows = []

    for _, indicator_name, unit in INDICATORS:
        query = f"2024 {indicator_name} exact value"
        relevant_docs = retriever.invoke(query)

        pages = sorted(set(d.metadata["page"] for d in relevant_docs))
        source_page = ", ".join(map(str, pages)) if pages else None

        context = "\n\n".join([doc.page_content[:4000] for doc in relevant_docs[:5]])

        prompt = f"""
Extract exact value from 2024 report.

Indicator: {indicator_name}
Unit: {unit}

Rules:
- Only 2024 data
- No estimation
- Return null if not found
- Quote exact text

JSON:
{{
  "value": "number_or_null",
  "exact_quote": "sentence",
  "source_section": "section name"
}}

Context:
{context}
"""

        try:
            result = structured_llm.invoke(prompt)
            value = result.get("value")
            if value in ["null", None]:
                value = None
            confidence = 1.0 if value is not None else 0.5
            source_section = result.get("source_section") or "Sustainability"
            notes = result.get("exact_quote") or "Not found"
        except:
            value = None
            confidence = 0.0
            source_section = "Unknown"
            notes = "Extraction error"

        rows.append({
            "company": bank_name,
            "report_year": report_year,
            "indicator_name": indicator_name,
            "value": str(value) if value is not None else None,
            "unit": unit,
            "confidence": confidence,
            "source_page": source_page,
            "source_section": source_section,
            "notes": notes
        })

    return rows


def save_rows_to_postgres(rows: List[Dict], conn_params: Dict):
    if not rows:
        return

    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sustainability_data (
            id SERIAL PRIMARY KEY,
            company VARCHAR(100),
            report_year INTEGER,
            indicator_name VARCHAR(200),
            value VARCHAR(50),
            unit VARCHAR(50),
            confidence FLOAT,
            source_page VARCHAR(100),
            source_section VARCHAR(200),
            notes TEXT,
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company, report_year, indicator_name)
        );
    """)

    insert_sql = """
        INSERT INTO sustainability_data 
        (company, report_year, indicator_name, value, unit, confidence, source_page, source_section, notes)
        VALUES %s
        ON CONFLICT (company, report_year, indicator_name) 
        DO UPDATE SET value = EXCLUDED.value, unit = EXCLUDED.unit, confidence = EXCLUDED.confidence,
                      source_page = EXCLUDED.source_page, source_section = EXCLUDED.source_section, notes = EXCLUDED.notes;
    """

    data_tuples = [(r["company"], r["report_year"], r["indicator_name"], r["value"], r["unit"],
                    r["confidence"], r["source_page"], r["source_section"], r["notes"]) for r in rows]

    execute_values(cur, insert_sql, data_tuples)
    conn.commit()
    cur.close()
    conn.close()
    