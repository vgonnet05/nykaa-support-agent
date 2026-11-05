from crew_agents import (
    DeterministicCrewMockLLM,
    build_crew,
    get_tool_permissions,
)


def test_only_lookup_agent_has_order_lookup_tool():
    _, agents = build_crew(DeterministicCrewMockLLM())
    permissions = get_tool_permissions(agents)

    assert "check_order_status" in permissions["Lookup Agent"]
    assert "check_order_status" not in permissions["Retrieval Agent"]
    assert "check_order_status" not in permissions["Response Composer"]

    assert "rag_policy_search" in permissions["Retrieval Agent"]
    assert "rag_policy_search" not in permissions["Lookup Agent"]

    print("PASS: Only Lookup Agent can call check_order_status")
    print("Tool permissions:", permissions)


if __name__ == "__main__":
    test_only_lookup_agent_has_order_lookup_tool()
