from typing import Dict, Any, Union
from pydantic import BaseModel
from mcp import ClientSession
import ast
from models import WebPageInput, WebPageOutput, SearchInput, SearchOutput, HighlightInput, HighlightOutput, IndexedPagesOutput
from perception import Perception
from memory import MemoryManager
from decision import Decision

# Optional: import log from agent if shared, else define locally
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")


class ToolCallResult(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Union[str, list, dict]
    raw_response: Any


def parse_function_call(response: str) -> tuple[str, Dict[str, Any]]:
    """Parses FUNCTION_CALL string into tool name and arguments."""
    try:
        if not response.startswith("FUNCTION_CALL:"):
            raise ValueError("Not a valid FUNCTION_CALL")

        _, function_info = response.split(":", 1)
        parts = [p.strip() for p in function_info.split("|")]
        func_name, param_parts = parts[0], parts[1:]

        result = {}
        for part in param_parts:
            if "=" not in part:
                raise ValueError(f"Invalid param: {part}")
            key, value = part.split("=", 1)

            try:
                parsed_value = ast.literal_eval(value)
            except Exception:
                parsed_value = value.strip()

            # Handle nested keys
            keys = key.split(".")
            current = result
            for k in keys[:-1]:
                current = current.setdefault(k, {})
            current[keys[-1]] = parsed_value

        log("parser", f"Parsed: {func_name} → {result}")
        return func_name, result

    except Exception as e:
        log("parser", f"❌ Failed to parse FUNCTION_CALL: {e}")
        raise


async def execute_tool(session: ClientSession, tools: list[Any], response: str) -> ToolCallResult:
    """Executes a FUNCTION_CALL via MCP tool session."""
    try:
        tool_name, arguments = parse_function_call(response)

        tool = next((t for t in tools if t.name == tool_name), None)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registered tools")

        log("tool", f"⚙️ Calling '{tool_name}' with: {arguments}")
        result = await session.call_tool(tool_name, arguments=arguments)

        if hasattr(result, 'content'):
            if isinstance(result.content, list):
                out = [getattr(item, 'text', str(item)) for item in result.content]
            else:
                out = getattr(result.content, 'text', str(result.content))
        else:
            out = str(result)

        log("tool", f"✅ {tool_name} result: {out}")
        return ToolCallResult(
            tool_name=tool_name,
            arguments=arguments,
            result=out,
            raw_response=result
        )

    except Exception as e:
        log("tool", f"⚠️ Execution failed for '{response}': {e}")
        raise


class Action:
    def __init__(self):
        self.perception = Perception()
        self.memory = MemoryManager()
        self.decision = Decision(self.memory)

    def index_page(self, input_data: WebPageInput) -> WebPageOutput:
        """Index a web page"""
        try:
            # Extract and process content
            perception_result = self.perception.extract_perception(input_data)
            if not perception_result.success:
                return perception_result

            # Add to memory
            success = self.memory.add(input_data.url, input_data.content)
            if not success:
                return WebPageOutput(success=False, error="Failed to add page to index")
            return WebPageOutput(success=True)
        except Exception as e:
            return WebPageOutput(success=False, error=str(e))

    def search_pages(self, input_data: SearchInput) -> SearchOutput:
        """Search indexed pages"""
        try:
            # Generate search plan and execute
            results = self.decision.generate_plan(input_data.query)
            return results
        except Exception as e:
            return SearchOutput(results=[])

    def highlight_text(self, input_data: HighlightInput) -> HighlightOutput:
        """Highlight text in search results"""
        try:
            # Generate highlighted text
            result = self.decision.highlight_text(input_data)
            return result
        except Exception as e:
            return HighlightOutput(highlighted_text=input_data.text)

    def list_indexed_pages(self) -> IndexedPagesOutput:
        """List all indexed pages"""
        try:
            pages = self.memory.list_pages()
            return IndexedPagesOutput(pages=pages)
        except Exception as e:
            return IndexedPagesOutput(pages=[], error=str(e))
