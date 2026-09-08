from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseTool(ABC):
    """Abstract base class for tools registered in the dynamic registry."""
    name: str
    description: str

    @abstractmethod
    def run(self, query: str, **kwargs: Any) -> str:
        """Execute the tool with a query and optional parameters."""
        pass


class ToolRegistry:
    """
    Dynamic tool registry allowing agents to dynamically look up, inspect,
    and execute tools without hardcoding tool logic inside each agent.
    """
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> BaseTool:
        """Register a tool instance."""
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        """List all available registered tools with descriptions."""
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]

    def execute(self, name: str, query: str, **kwargs: Any) -> str:
        """Execute a tool dynamically by name."""
        tool = self.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found in registry. Available tools: {list(self._tools.keys())}"
        try:
            return tool.run(query, **kwargs)
        except Exception as e:
            return f"Error executing tool '{name}': {str(e)}"


# Global registry instance
tool_registry = ToolRegistry()
