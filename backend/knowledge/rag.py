import re
import math
from typing import List, Dict, Any

# Curated Educational Knowledge Corpus for Backend Development & Python
KNOWLEDGE_DOCUMENTS = [
    {
        "id": "doc_python_fundamentals",
        "topic": "Python Fundamentals & Data Structures",
        "title": "Python Core Types, Lists, Dictionaries, and Memory Primitives",
        "content": """
Python variables are dynamically typed references to objects in heap memory.
Core collection data structures include:
- Lists: Dynamic mutable contiguous arrays with O(1) append/pop and O(n) arbitrary insertion.
- Dictionaries: Hash maps using open addressing, providing O(1) average lookup, insertion, and deletion.
- Sets: Unordered collections of unique elements built over hash tables.
- Tuples: Immutable sequences ideal for fixed records and dictionary keys.
List comprehensions provide concise syntax: [x * 2 for x in items if x > 0].
Memory management relies on reference counting complemented by a generational cyclic garbage collector.
"""
    },
    {
        "id": "doc_functions_oop",
        "topic": "Functions, Scope, and Object-Oriented Programming",
        "title": "Functional Patterns, Decorators, and Object-Oriented Architecture",
        "content": """
Functions in Python are first-class citizens capable of being passed as arguments, returned, and decorated.
Scope follows the LEGB rule: Local, Enclosing, Global, Built-in.
Decorators use closures to wrap and modify function behavior: @decorator_func wraps target callable.
Object-Oriented Programming principles in Python:
- Encapsulation: Grouping state and methods; convention uses single leading underscore for protected attributes.
- Inheritance: Superclass specialization with method resolution order (MRO) via the C3 linearization algorithm.
- Polymorphism & Duck Typing: If an object implements the required interface methods (e.g. __iter__, __len__), it fits the protocol.
- Dunder methods: __init__, __str__, __repr__, and context managers (__enter__, __exit__).
"""
    },
    {
        "id": "doc_web_apis_fastapi",
        "topic": "REST APIs, HTTP Protocols, and FastAPI Framework",
        "title": "REST Architectural Constraints and Modern FastAPI Development",
        "content": """
Representational State Transfer (REST) adheres to key constraints: Stateless client-server communication, uniform interface, and cacheability.
HTTP Verbs:
- GET: Retrieve resources idempotently.
- POST: Create subordinate resources.
- PUT / PATCH: Complete or partial updates.
- DELETE: Remove resources.
FastAPI builds on Starlette and Pydantic:
- Request validation occurs automatically through type annotations and Pydantic BaseModel schemas.
- Dependency Injection (Depends) enables modular database sessions, authentication, and caching.
- Path parameters (/items/{item_id}) and query parameters (/items?skip=0&limit=10) are type-coerced and validated.
"""
    },
    {
        "id": "doc_databases_sqlite",
        "topic": "Relational Databases, SQL, and SQLite Persistence",
        "title": "Database Schema Design, ACID Transactions, and SQLite Indexing",
        "content": """
Relational database management systems organize data into structured tables with foreign keys.
ACID Guarantees:
- Atomicity: Transactions either completely execute or roll back entirely.
- Consistency: State transitions preserve declarative constraints.
- Isolation: Concurrent operations produce states equivalent to serial execution.
- Durability: Committed transactions persist across crashes or power failure.
SQLite is an embedded zero-configuration serverless database storing the entire catalog in a single disk file.
B-Tree indexes speed up lookups from O(n) sequential scans to O(log n) tree traversals.
SQL injection vulnerabilities are prevented through parameterized queries (? placeholders) rather than raw string formatting.
"""
    },
    {
        "id": "doc_async_programming",
        "topic": "Asynchronous Programming, Event Loops, and AsyncIO",
        "title": "Non-Blocking I/O, Async/Await Syntax, and Event Loop Mechanics",
        "content": """
Python async/await leverages cooperative multitasking driven by an underlying event loop.
- Synchronous I/O blocks the thread during network or disk waits.
- Asynchronous I/O yields execution control back to the event loop during wait states using 'await'.
async def declares a coroutine. Coroutines must be awaited or scheduled via asyncio.create_task().
asyncio.gather() enables concurrent execution of multiple coroutines.
Crucial Rule: Do not run CPU-bound blocking calls or time.sleep() inside async functions; use thread executors or asyncio.sleep().
"""
    },
    {
        "id": "doc_testing_debugging",
        "topic": "Automated Testing, Pytest, and Code Quality",
        "title": "Unit Testing, Pytest Fixtures, Mocking, and Regression Protection",
        "content": """
Automated software testing guarantees component correctness and guards against regressions.
Pytest conventions:
- Test files named test_*.py or *_test.py.
- Assertion statements: assert actual == expected.
- Fixtures (@pytest.fixture) provide reusable, modular setup and teardown contexts.
- Mocking (unittest.mock): Replaces slow or external network I/O with deterministic substitutes.
Coverage metrics verify which branches of logic are exercised during test execution.
"""
    },
    {
        "id": "doc_sql_fundamentals",
        "topic": "SQL Fundamentals & Relational Concepts",
        "title": "Relational Tables, Data Types, Constraints, and SELECT Projections",
        "content": """
Structured Query Language (SQL) is the standard declarative language for interacting with relational databases.
Core concepts:
- Tables: Two-dimensional schemas with rows (records/tuples) and columns (attributes).
- Primary Key (PK): Uniquely identifies each record in a table, enforcing entity integrity.
- Foreign Key (FK): Establishes relational integrity linking records between parent and child tables.
- The SELECT statement retrieves column projections: SELECT col1, col2 FROM table_name.
- Aliases: AS keyword renames result columns or table references for readability.
- DISTINCT: Filters out duplicate rows from query results.
"""
    },
    {
        "id": "doc_sql_filtering_aggregates",
        "topic": "Filtering, Sorting, and Aggregate Functions",
        "title": "WHERE Conditions, ORDER BY Sorting, and GROUP BY Aggregations",
        "content": """
Filtering and transforming records in SQL:
- WHERE clause: Applies boolean criteria (AND, OR, NOT, IN, BETWEEN, LIKE) to filter rows before aggregation.
- ORDER BY: Sorts result sets by one or more columns in ASC (default) or DESC order.
- Aggregate Functions: Compute summary statistics over sets of values: COUNT(), SUM(), AVG(), MIN(), MAX().
- GROUP BY: Groups rows sharing identical attribute values into summary rows.
- HAVING clause: Filters groups AFTER aggregation (unlike WHERE which filters before grouping).
"""
    },
    {
        "id": "doc_sql_joins",
        "topic": "Table Joins and Multi-Table Relations",
        "title": "Relational Multi-Table Joins: INNER, LEFT, RIGHT, and FULL OUTER",
        "content": """
Joins combine columns from one or more tables based on common relational keys.
- INNER JOIN: Returns only records having matching keys in both participating tables.
- LEFT JOIN (LEFT OUTER JOIN): Returns all records from the left table, and matching records from the right table. Unmatched right columns evaluate to NULL.
- RIGHT JOIN: Returns all records from right table, and matching rows from left table.
- FULL OUTER JOIN: Returns all records when there is a match in either table.
- CROSS JOIN: Produces the Cartesian product of all rows across both tables.
- Best Practice: Always explicitly index foreign key columns to avoid costly table scans during join operations.
"""
    }
]


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into lowercase alphanumeric tokens."""
    return re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())


def compute_tf_idf(query: str, corpus: List[Dict[str, str]]) -> List[float]:
    """Calculate TF-IDF cosine similarity scores between query and documents."""
    q_tokens = tokenize(query)
    if not q_tokens:
        return [0.0] * len(corpus)

    num_docs = len(corpus)
    doc_tokens_list = [tokenize(doc["title"] + " " + doc["content"]) for doc in corpus]

    # Calculate IDF
    idf: Dict[str, float] = {}
    for token in set(q_tokens):
        containing_docs = sum(1 for d_tokens in doc_tokens_list if token in d_tokens)
        idf[token] = math.log((1 + num_docs) / (1 + containing_docs)) + 1.0

    scores = []
    for d_tokens in doc_tokens_list:
        if not d_tokens:
            scores.append(0.0)
            continue

        score = 0.0
        d_len = len(d_tokens)
        for token in q_tokens:
            tf = d_tokens.count(token) / d_len
            score += tf * idf.get(token, 1.0)
        scores.append(score)

    return scores


class RAGRetriever:
    """
    Lightweight, deterministic local Retrieval-Augmented Knowledge (RAG) layer.
    Retrieves grounded educational source documents to back Tutor and Practice agents.
    """
    def __init__(self, corpus: List[Dict[str, str]] = None):
        self.corpus = corpus or KNOWLEDGE_DOCUMENTS

    def retrieve(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        scores = compute_tf_idf(query, self.corpus)
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in indexed_scores[:top_k]:
            doc = self.corpus[idx]
            results.append({
                "id": doc["id"],
                "topic": doc["topic"],
                "title": doc["title"],
                "content": doc["content"].strip(),
                "score": round(score, 4)
            })
        return results

    def format_context(self, query: str, top_k: int = 2) -> str:
        docs = self.retrieve(query, top_k=top_k)
        formatted_chunks = []
        for d in docs:
            formatted_chunks.append(f"### [Grounded Source: {d['title']}]\n{d['content']}")
        return "\n\n".join(formatted_chunks)


# Global RAG instance
rag_retriever = RAGRetriever()
