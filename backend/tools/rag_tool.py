from .registry import BaseTool, tool_registry
from ..knowledge.rag import rag_retriever


class RAGKnowledgeTool(BaseTool):
    """
    Tool allowing agents to dynamically query the local RAG knowledge repository
    for grounded documentation and technical references.
    """
    name = "rag_knowledge_tool"
    description = "Retrieves authoritative curriculum references and technical specifications for a topic."

    def run(self, query: str, **kwargs) -> str:
        top_k = kwargs.get("top_k", 2)
        return rag_retriever.format_context(query, top_k=top_k)


# Register instance in dynamic registry
rag_knowledge_tool = RAGKnowledgeTool()
tool_registry.register(rag_knowledge_tool)
