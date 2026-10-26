"""Offline tool-loop experiment. No model API, network, keys, or business data."""
import json
from dataclasses import dataclass

from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult


@dataclass(frozen=True)
class Identity:
    tenant: str


@tool
def query_net_revenue(month: str, runtime: ToolRuntime[Identity]) -> str:
    """Query net revenue in CNY cents for an explicit YYYY-MM month."""
    if month != "2026-09":
        raise ValueError("The teaching fixture only covers 2026-09")
    fixtures = {"A": 27000, "B": 25000}
    tenant = runtime.context.tenant
    if tenant not in fixtures:
        raise PermissionError("Unknown teaching tenant")
    return json.dumps({"tenant": tenant, "month": month,
                       "net_cents": fixtures[tenant], "definition_version": "teaching-v1"})


class ScriptedModel(BaseChatModel):
    """Emit predetermined tool calls; this does not simulate model intelligence."""

    @property
    def _llm_type(self):
        return "offline-scripted-model"

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        # The fixed script knows exactly one tool; no provider-side binding needed.
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        if isinstance(messages[-1], ToolMessage):
            result = json.loads(messages[-1].content)
            message = AIMessage(content=f"净收入为 {result['net_cents']} 分。")
        else:
            message = AIMessage(content="", tool_calls=[{
                "name": "query_net_revenue", "args": {"month": "2026-09"},
                "id": "teaching-call-1", "type": "tool_call",
            }])
        return ChatResult(generations=[ChatGeneration(message=message)])


def main():
    schema = query_net_revenue.tool_call_schema.model_json_schema()
    assert set(schema["properties"]) == {"month"}, schema
    agent = create_agent(model=ScriptedModel(), tools=[query_net_revenue],
                         context_schema=Identity)
    observations = []
    for tenant, expected in [("A", 27000), ("B", 25000)]:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "查询2026年9月净收入"}]},
            context=Identity(tenant=tenant),
            config={"recursion_limit": 10},
        )
        messages = result["messages"]
        tool_results = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_results) == 1
        value = json.loads(tool_results[0].content)
        assert value["tenant"] == tenant and value["net_cents"] == expected
        assert str(expected) in messages[-1].content
        observations.append({"tenant": tenant, "net_cents": expected,
                             "message_types": [m.type for m in messages]})
    print(json.dumps({"model_visible_parameters": list(schema["properties"]),
                      "runs": observations}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
