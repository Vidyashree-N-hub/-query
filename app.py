
import re
import os
from typing import List, Dict

import streamlit as st

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("Please install pymupdf: pip install pymupdf")


SUPPORTED_PROCEDURES = [
    "hip replacement", "knee replacement", "joint surgery", "bypass surgery", "appendectomy",
    "angioplasty", "cataract surgery", "dialysis", "organ transplant", "liver transplant",
    "kidney transplant", "cancer surgery", "spine surgery", "heart surgery",
    "craniotomy", "tumor removal", "cardiac surgery", "brain surgery"
]


class QueryParser:
    def parse(self, query: str) -> Dict:
        age_match = re.search(r'(\d{2})[- ]?year[- ]?old', query, re.IGNORECASE)
        location_match = re.search(r'in\s+([a-zA-Z]+)', query, re.IGNORECASE)
        policy_duration_match = re.search(r'(\d+)[- ]?month[- ]?old', query, re.IGNORECASE)

        matched_procedure = None
        for procedure in SUPPORTED_PROCEDURES:
            if re.search(procedure, query, re.IGNORECASE):
                matched_procedure = procedure
                break

        return {
            "age": int(age_match.group(1)) if age_match else None,
            "procedure": matched_procedure,
            "location": location_match.group(1) if location_match else None,
            "policy_duration_months": int(policy_duration_match.group(1)) if policy_duration_match else None
        }


class DocumentLoader:
    def load_documents(self, folder_path="dataset") -> (List[str], List[str]):
        docs = []
        filenames = []
        for filename in os.listdir(folder_path):
            path = os.path.join(folder_path, filename)
            if filename.endswith(".txt"):
                with open(path, 'r', encoding='utf-8') as f:
                    docs.append(f.read())
                    filenames.append(filename)
            elif filename.endswith(".pdf"):
                docs.append(self.extract_text_from_pdf(path))
                filenames.append(filename)
        return docs, filenames

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text


class ClauseRetriever:
    def __init__(self, documents: List[str], filenames: List[str]):
        self.documents = documents
        self.filenames = filenames

    def retrieve_clauses(self, parsed_query: Dict) -> List[Dict]:
        clauses = []
        proc = parsed_query.get('procedure')
        if not proc:
            return []

        for doc, fname in zip(self.documents, self.filenames):
            for match in re.finditer(re.escape(proc), doc, re.IGNORECASE):
                start = max(0, match.start() - 100)
                end = min(len(doc), match.end() + 200)
                snippet = doc[start:end].strip().replace('\n', ' ')
                clauses.append({"clause": snippet, "document": fname})
        return clauses


class DecisionEvaluator:
    def evaluate(self, parsed_query: Dict, clauses: List[Dict]) -> str:
        procedure = parsed_query.get("procedure", "The procedure")
        policy_duration = parsed_query.get("policy_duration_months")

        if not procedure:
            return "No, coverage cannot be determined as the procedure is missing in the query."

        if policy_duration is None:
            return f"Yes, {procedure} is covered under the policy (policy duration not specified, assumed valid)."

        if policy_duration < 12:
            return f"No, {procedure} is not covered as the policy duration is only {policy_duration} month(s) (minimum 12 months required)."

        return f"Yes, {procedure} is covered under the policy."


# Streamlit App
st.title("🛡️ Insurance Query Coverage Checker")

query = st.text_input("Enter your query:")

if query:
    parser = QueryParser()
    parsed_query = parser.parse(query)

    loader = DocumentLoader()
    try:
        documents, filenames = loader.load_documents()
    except FileNotFoundError:
        st.error("Error: 'dataset' folder missing. Create it and add .txt or .pdf files.")
        st.stop()

    retriever = ClauseRetriever(documents, filenames)
    matched_clauses = retriever.retrieve_clauses(parsed_query)

    st.subheader("🔍 Matched Clauses")
    if matched_clauses:
        for clause in matched_clauses:
            st.markdown(f"**From `{clause['document']}`:**")
            st.info(clause['clause'])
    else:
        st.warning("No relevant clauses found.")

    evaluator = DecisionEvaluator()
    result = evaluator.evaluate(parsed_query, matched_clauses)
    st.subheader("📄 Final Decision")
    st.success(result)
