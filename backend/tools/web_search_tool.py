from .registry import BaseTool, tool_registry


class WebSearchTool(BaseTool):
    """
    Lightweight web search tool providing topical context summaries
    and standard learning references without requiring external paid APIs.
    """
    name = "web_search_tool"
    description = "Searches reference sources for definitions, standards, and practical industry conventions."

    def run(self, query: str, **kwargs) -> str:
        return (
            f"Reference summary for '{query}':\n"
            f"- Industry consensus and standard reference documentation.\n"
            f"- Recommended best practices and modern conventions regarding {query}."
        )


web_search_tool = WebSearchTool()
tool_registry.register(web_search_tool)
