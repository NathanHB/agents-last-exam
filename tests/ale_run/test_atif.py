from __future__ import annotations

from ale_run.base_interface.atif import ATIF_VERSION, to_atif
from ale_run.base_interface.trajectory import (
    Observation,
    StepMetrics,
    ToolCall,
    ToolResult,
    TrajectoryBuilder,
)


def _builder() -> TrajectoryBuilder:
    return TrajectoryBuilder(
        episode_id="ep-123",
        agent_name="pi_cli",
        agent_version="0.85.1",
        model="Qwen/Qwen3.5-9B",
        task_path="demo/hello",
        variant_index=0,
        instruction="say hi",
    )


def test_basic_shape():
    builder = _builder()
    builder.add_step("user", message="say hi")
    builder.add_step(
        "agent",
        message="hi!",
        metrics=StepMetrics(input_tokens=10, output_tokens=2, cost_usd=0.001),
    )
    traj = builder.finalize(reward=1.0, status="completed")

    out = to_atif(traj)

    assert out["schema_version"] == ATIF_VERSION
    assert out["session_id"] == "ep-123"
    assert out["trajectory_id"] == "ep-123"
    assert out["agent"] == {
        "name": "pi_cli",
        "version": "0.85.1",
        "model_name": "Qwen/Qwen3.5-9B",
    }
    assert len(out["steps"]) == 2
    assert [s["step_id"] for s in out["steps"]] == [1, 2]
    assert out["steps"][0]["source"] == "user"
    assert out["steps"][1]["source"] == "agent"
    assert out["steps"][1]["metrics"] == {"prompt_tokens": 10, "completion_tokens": 2, "cost_usd": 0.001}


def test_metrics_only_on_agent_steps():
    """ATIF forbids `metrics` on non-agent steps; this must never happen."""
    builder = _builder()
    builder.add_step("system", message="note", metrics=StepMetrics(input_tokens=5))
    traj = builder.finalize(reward=0.0)

    out = to_atif(traj)

    assert "metrics" not in out["steps"][0]


def test_split_observation_is_merged_onto_the_tool_call_step():
    """Some harnesses (e.g. openclaw_cli) log the observation on a separate
    'environment' step right after the agent step with the tool_calls. ATIF
    requires same-step resolution, so the result must be re-attached and the
    now-empty carrier step dropped."""
    builder = _builder()
    builder.add_step(
        "agent",
        tool_calls=[ToolCall(id="call_1", name="read", arguments={"path": "a.txt"})],
    )
    builder.add_step(
        "environment",
        observation=Observation(
            results=[ToolResult(tool_call_id="call_1", content=[], is_error=False)]
        ),
    )
    traj = builder.finalize(reward=1.0)

    out = to_atif(traj)

    assert len(out["steps"]) == 1
    step = out["steps"][0]
    assert step["step_id"] == 1
    assert step["source"] == "agent"
    assert step["tool_calls"][0]["tool_call_id"] == "call_1"
    assert step["tool_calls"][0]["function_name"] == "read"
    assert step["observation"]["results"][0]["source_call_id"] == "call_1"


def test_orphaned_observation_is_folded_into_message_not_dropped():
    """A result whose source_call_id matches no tool_call anywhere (a logging
    gap) can't keep its own step (ATIF forbids tool_calls on non-agent steps
    pointing nowhere) -- it must be preserved as text, not silently lost."""
    builder = _builder()
    builder.add_step(
        "environment",
        observation=Observation(
            results=[ToolResult(tool_call_id="call_ghost", content=[], is_error=True)]
        ),
    )
    traj = builder.finalize(reward=0.0)

    out = to_atif(traj)

    assert len(out["steps"]) == 1
    assert "call_ghost" in out["steps"][0]["message"]
    assert "observation" not in out["steps"][0]


def test_final_metrics_field_names():
    builder = _builder()
    builder.add_step("agent", metrics=StepMetrics(input_tokens=10, output_tokens=5, cache_read_tokens=3))
    traj = builder.finalize(reward=0.75, status="timeout")

    out = to_atif(traj)

    fm = out["final_metrics"]
    assert fm["total_prompt_tokens"] == 10
    assert fm["total_completion_tokens"] == 5
    assert fm["total_cached_tokens"] == 3
    assert fm["extra"]["reward"] == 0.75
    assert fm["extra"]["status"] == "timeout"


def test_accepts_plain_dict_too():
    builder = _builder()
    builder.add_step("user", message="hi")
    traj = builder.finalize(reward=None)

    from_model = to_atif(traj)
    from_dict = to_atif(traj.model_dump(mode="json"))

    assert from_model == from_dict
