"""Offline teaching example using the standard library and synthetic CNY cents.

Calls are normalized application objects, NOT provider responses or MCP wire
messages. No model, protocol client/server, skill loader, network, or credentials.
"""
from copy import deepcopy
from dataclasses import dataclass
import json
import re


INPUT_SCHEMA = {
    "type": "object",
    "properties": {"month": {"type": "string", "description": "Explicit YYYY-MM"}},
    "required": ["month"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class Identity:
    tenant: str


def model_tool_definition(catalog_entry):
    """Adapt catalog fields to one model API's function-definition shape only."""
    return {
        "type": "function",
        "name": catalog_entry["name"],
        "description": catalog_entry["description"],
        "parameters": deepcopy(catalog_entry["inputSchema"]),
    }


def dispatch(call, identity):
    """Validate normalized input; real applications need a full schema validator."""
    if call["name"] != "query_net_revenue":
        raise ValueError("Unknown tool")
    args = call["arguments"]
    if not isinstance(args, dict) or set(args) != {"month"}:
        raise ValueError("Exactly one model-generated field is accepted: month")
    month = args["month"]
    if not isinstance(month, str) or not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", month):
        raise ValueError("Invalid YYYY-MM")
    if month != "2026-09":
        raise LookupError("Valid shape, but no teaching data exists for this month")
    fixtures = {"A": 27000, "B": 25000}
    if identity.tenant not in fixtures:
        raise PermissionError("No access to this teaching tenant")
    return {"tenant": identity.tenant, "month": month,
            "net_cents": fixtures[identity.tenant], "unit": "CNY_cent",
            "definition_version": "teaching-v1"}


def main():
    # This local dictionary resembles an MCP catalog entry; no discovery occurs.
    catalog_entry = {"name": "query_net_revenue",
                     "description": "Query net revenue for an explicit month.",
                     "inputSchema": INPUT_SCHEMA}
    model_definition = model_tool_definition(catalog_entry)
    assert set(model_definition["parameters"]["properties"]) == {"month"}
    call = {"name": "query_net_revenue", "arguments": {"month": "2026-09"}}
    direct = dispatch(call, Identity("A"))
    # Demonstrates reusing the same backend after catalog adaptation, not MCP I/O.
    adapted = dispatch({"name": model_definition["name"], "arguments": call["arguments"]}, Identity("A"))
    assert direct == adapted and direct["net_cents"] == 27000
    other = dispatch(call, Identity("B"))
    assert other["net_cents"] == 25000
    cases = [
        ("tenant_spoofing", {"name": "query_net_revenue", "arguments": {"month": "2026-09", "tenant": "B"}}, Identity("A"), ValueError),
        ("unknown_tool", {"name": "execute_sql", "arguments": {"month": "2026-09"}}, Identity("A"), ValueError),
        ("invalid_month", {"name": "query_net_revenue", "arguments": {"month": "2026-99"}}, Identity("A"), ValueError),
        ("no_data", {"name": "query_net_revenue", "arguments": {"month": "2026-10"}}, Identity("A"), LookupError),
        ("unauthorized_identity", call, Identity("unknown"), PermissionError),
    ]
    rejected = []
    for label, request, identity, error in cases:
        try:
            dispatch(request, identity)
        except error:
            rejected.append(label)
        else:
            raise AssertionError(f"Expected rejection: {label}")
    print(json.dumps({"scope": "normalized local calls; no model or MCP transport",
                      "model_visible_parameters": list(model_definition["parameters"]["properties"]),
                      "backend_reuse_equal": direct == adapted, "tenant_A": direct,
                      "tenant_B": other, "rejected_cases": rejected}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
