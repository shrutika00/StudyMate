from backend.knowledge.rag import rag_retriever, tokenize, compute_tf_idf
from backend.tools.registry import tool_registry


def test_rag_retrieval_and_tool():
    """Requirement 17: RAG retrieval works and is accessible via tool registry."""
    # Test direct retrieval
    docs = rag_retriever.retrieve("Python lists and dictionaries", top_k=2)
    assert len(docs) == 2
    assert "content" in docs[0]
    assert docs[0]["score"] > 0

    # Test formatting
    context_str = rag_retriever.format_context("FastAPI REST endpoints", top_k=1)
    assert "FastAPI" in context_str

    # Test tool registry integration
    tool_output = tool_registry.execute("rag_knowledge_tool", "Relational Databases SQL")
    assert "Relational" in tool_output or "SQL" in tool_output
