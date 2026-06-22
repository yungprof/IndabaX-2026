"""
The four verified Ghanaian financial documents used by the RAG assistant.
Small and inspectable by design — participants can read the entire corpus.
"""

KNOWLEDGE_BASE: list[dict] = [
    {
        "id": "doc_001",
        "title": "Susu and Mobile Money Lending Eligibility",
        "content": """
        Several Ghanaian microfinance institutions accept Mobile Money transaction
        history as evidence of income for informal sector workers. Providers including
        Fido, Jumo, and MTN Qwikloan assess eligibility based on MoMo transaction
        frequency, average balance, and account age. A minimum of six months of
        consistent MoMo activity is typically required. No payslip is needed for
        these products. Maximum loan amounts for first-time borrowers typically
        range from GHS 500 to GHS 2,000 depending on the provider and transaction history.
        """,
        "source": "Ghana Microfinance Industry Overview, 2024",
        "verified": True,
    },
    {
        "id": "doc_002",
        "title": "Borrowers and Lenders Act 2020",
        "content": """
        The Borrowers and Lenders Act 2020 (Act 1052) governs lending in Ghana.
        Under this Act, all lenders must disclose the total cost of credit, including
        interest rates, fees, and charges, before a loan agreement is signed. Borrowers
        have the right to receive an information document before the contract is signed.
        Lenders are prohibited from using deceptive practices in advertising loan products.
        Collateral requirements must be proportionate to the loan amount. The Act
        established a Collateral Registry for movable assets.
        """,
        "source": "Borrowers and Lenders Act 2020, Parliament of Ghana",
        "verified": True,
    },
    {
        "id": "doc_003",
        "title": "Bank of Ghana Savings and Loans Licensing",
        "content": """
        Savings and Loans companies in Ghana are licensed and regulated by the Bank
        of Ghana under the Banks and Specialised Deposit Taking Institutions Act 2016
        (Act 930). Licensed savings and loans companies may accept deposits and extend
        credit. Customers can verify whether a financial institution holds a valid
        licence by checking the Bank of Ghana public register, available at the
        Bank of Ghana official website. Dealing with unlicensed lenders carries
        significant risk and limited legal recourse.
        """,
        "source": "Bank of Ghana Regulatory Framework, 2024",
        "verified": True,
    },
    {
        "id": "doc_004",
        "title": "Interest Rate Disclosure Requirements",
        "content": """
        Under regulations issued by the Bank of Ghana, all licensed financial
        institutions must quote interest rates on an annual percentage rate (APR)
        basis to allow meaningful comparison between products. Monthly interest
        rates, which are commonly advertised, must be accompanied by the equivalent
        APR. As of 2024, microfinance loan interest rates in Ghana range widely,
        from approximately 35% to over 100% APR depending on the product type,
        loan size, and borrower risk profile.
        """,
        "source": "Bank of Ghana Consumer Protection Guidelines, 2023",
        "verified": True,
    },
]


import re
import string

# Common words that inflate overlap scores but carry no retrieval signal.
_STOP_WORDS = {
    "i", "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "my", "your", "is", "it", "can",
    "get", "be", "do", "if", "me", "am", "are", "was", "not", "no", "so",
}


def _tokenize(text: str) -> set[str]:
    """Lowercase, strip punctuation, remove stop words."""
    tokens = re.sub(r"[^\w\s]", "", text.lower()).split()
    return {t for t in tokens if t and t not in _STOP_WORDS}


def retrieve_relevant_documents(
    query: str,
    knowledge_base: list[dict] | None = None,
    top_k: int = 2,
) -> list[dict]:
    """
    Keyword-overlap retrieval. Intentionally simple so participants can
    inspect exactly what the retrieval step is doing and why.
    In production, use vector embeddings and cosine similarity instead.

    Note: Exercise — try editing the query to use different words for
    "interest" or "fees" and watch how overlap changes.
    """
    kb = knowledge_base if knowledge_base is not None else KNOWLEDGE_BASE
    query_terms = _tokenize(query)
    scored = []
    for doc in kb:
        blob = doc["title"] + " " + doc["content"]
        doc_terms = _tokenize(blob)
        score = len(query_terms & doc_terms)
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in scored[:top_k] if score > 0]


def format_retrieved_context(documents: list[dict]) -> str:
    if not documents:
        return "No relevant documents were retrieved for this query."
    parts = []
    for doc in documents:
        parts.append(
            f"SOURCE: {doc['source']}\n"
            f"TITLE: {doc['title']}\n"
            f"CONTENT: {doc['content'].strip()}\n"
        )
    return "\n\n".join(parts)
