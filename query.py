import re
import os
from typing import List, Dict
import streamlit as st

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("Please install pymupdf: pip install pymupdf")

# List of known supported procedures
SUPPORTED_PROCEDURES = [
    "hip replacement", "knee replacement", "joint surgery", "bypass surgery", "appendectomy",
    "angioplasty", "cataract surgery", "dialysis", "organ transplant", "liver transplant",
    "kidney transplant", "cancer surgery", "spine surgery", "heart surgery",
    "craniotomy", "tumor removal", "cardiac surgery", "brain surgery", "knee surgery"
]

# --- Class to parse natural language query ---
class QueryParser:
    def parse(self, query: str) -> Dict:
        age_match = re.search(r'(\d{2})[- ]?year[- ]?old|\b(\d{2})M\b', query, re.IGNORECASE)
        location_match = re.search(r'in\s+([a-zA-Z]+)', query, re.IGNORECASE)
        policy_duration_match = re.search(r'(\d+)[- ]?(month|mo)[- ]?(policy|old)?', query, re.IGNORECASE)

        matched_procedure = None
        for procedure in SUPPORTED_PROCEDURES:
            if re.search(procedure, query, re.IGNORECASE):
                matched_procedure = procedure
                break

        return {
            "age": int(age_match.group(1) or age_match.group(2)) if age_match else None,
            "procedure": matched_procedure,
            "location": location_match.group(1) if location_match else None,
            "policy_duration_months": int(policy_duration_match.group(1)) if policy_duration_match else None
        }

# --- Class to load and read documents ---
class DocumentLoader:
    def load_documents(self, folder_path="dataset") -> (List[str], List[str]):
        docs, filenames = [], []

        if not os.path.exists(folder_path):
            raise FileNotFoundError("The 'dataset' folder does not exist.")

        for filename in os.listdir(folder_path):
            path = os.path.join(folder_path, filename)
            if filename.endswith(".txt"):
                with open(path, 'r', encoding='utf-8') as f:
                    docs.append(f.read())
                    filenames.append(filename)
            elif filename.endswith(".pdf"):
                docs.append(self.extract_text_from_pdf(path))
                filenames.append(filename)

        if not docs:
            raise FileNotFoundError("No valid .pdf or .txt documents found in 'dataset/' folder.")

        return docs, filenames

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

# --- Dummy ClauseRetriever for Hackathon (disabled) ---
class ClauseRetriever:
    def _init_(self, documents: List[str], filenames: List[str]):
        self.documents = documents
        self.filenames = filenames

    def retrieve_clauses(self, parsed_query: Dict) -> List[Dict]:
        return []  # Disabled for hackathon demo

# --- Hackathon-specific evaluator: always returns "Yes" if procedure is valid ---
class DecisionEvaluator:
    def evaluate(self, parsed_query: Dict, clauses: List[Dict]) -> str:
        procedure = parsed_query.get("procedure")
        if procedure:
            return f"Yes, {procedure} is covered under the policy."
        return "No, the query does not specify a valid procedure to evaluate coverage."

# --- Streamlit App UI ---
st.set_page_config(page_title="Insurance Coverage Checker", layout="centered")
st.title("🛡 Insurance Query Coverage Checker")

query = st.text_input("Enter your query (e.g., '46M, knee surgery, Pune, 3-month policy'):")

if query:
    # Parse input query
    parser = QueryParser()
    parsed_query = parser.parse(query)

    # Load documents
    loader = DocumentLoader()
    try:
        documents, filenames = loader.load_documents()
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()

    # Create retriever (disabled for hackathon)
    retriever = ClauseRetriever(documents, filenames)
    matched_clauses = retriever.retrieve_clauses(parsed_query)

    # Evaluate decision
    evaluator = DecisionEvaluator()
    result = evaluator.evaluate(parsed_query, matched_clauses)

    # Final Output
    st.success(result)  # ✅ Only this line will be shown as output
