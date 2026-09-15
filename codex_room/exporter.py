from __future__ import annotations

import json
from typing import Any


def as_json(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, indent=2, ensure_ascii=False)


def as_markdown(snapshot: dict[str, Any]) -> str:
    ordered_agents = snapshot["agents"]
    names = {agent["agent_key"]: agent["name"] for agent in ordered_agents}
    names.update({"observer": "Observer", "room": "Room"})
    lines = [
        f"# {snapshot['title']}",
        "",
        f"- Room ID: `{snapshot['id']}`",
        f"- Created: {snapshot['created_at']}",
        f"- Status: {snapshot['status']}",
    ]
    for agent in ordered_agents:
        label = f"Agent {agent['agent_key'].removeprefix('agent_').upper()}"
        lines.extend(
            [
                f"- {label} thread: `{agent.get('thread_id') or 'not created'}`",
                f"- {label} profile: `{agent.get('profile_id') or 'legacy snapshot'}`",
            ]
        )
    lines.append("")
    rounds = snapshot.get("rounds") or [
        {"id": snapshot.get("discussion_id"), "title": "Legacy discussion", "events": snapshot["events"]}
    ]
    for index, round_item in enumerate(rounds, start=1):
        lines.extend(
            [
                f"## Round {index}: {round_item.get('title') or 'Untitled round'}",
                "",
                f"- Round ID: `{round_item['id']}`",
                f"- Status: {round_item.get('status', 'legacy')}",
                f"- Starting agent: {round_item.get('starting_agent') or 'not recorded'}",
                f"- Turns: {round_item.get('turn_count', 0)}",
                f"- Consecutive conversational PASSes: {round_item.get('consecutive_passes', 0)}",
                f"- Work model version: {round_item.get('work_model_version', 1)}",
                "",
                "### Public prompt",
                "",
                round_item.get("prompt") or snapshot.get("topic", ""),
                "",
            ]
        )
        transaction = round_item.get("transaction_state")
        if transaction is not None:
            lines.extend(["### Transaction work state", ""])
            tasks = transaction.get("tasks", [])
            if not tasks:
                lines.extend(["_(no transaction tasks recorded)_", ""])
            for task in tasks:
                required = task.get("required_contributors") or []
                lines.extend(
                    [
                        f"#### Task `{task['id']}`",
                        "",
                        f"- State: {task['state']}",
                        (
                            "- Required contributors: "
                            + (", ".join(required) if required else "none")
                        ),
                        f"- Settlement reason: {task.get('settlement_reason') or 'not settled'}",
                        "",
                        "Assignments:",
                    ]
                )
                for assignment in task.get("assignments", []):
                    lines.append(
                        f"- `{assignment['id']}` · {assignment['agent_key']} · "
                        f"{assignment['state']} · {assignment['instruction']}"
                    )
                lines.append("")
                lines.append("Joins:")
                for join in task.get("joins", []):
                    lines.append(
                        f"- `{join['id']}` · {join['state']} · "
                        f"parent={join.get('parent_assignment_id') or 'external'} · "
                        f"released={join.get('released_assignment_id') or 'none'}"
                    )
                lines.append("")
        lines.extend(["### Events", ""])
        for event in round_item.get("events", []):
            speaker = names.get(event["source"], event["source"])
            destination = event["destination"]
            private = event.get("metadata", {}).get("private", False)
            label = f"{speaker} → {destination}"
            if private:
                label += " (private observer delivery)"
            flags = [event.get("event_class", "legacy")]
            if event.get("counts_as_turn"):
                flags.append("counts as turn")
            if event.get("counts_toward_pass"):
                flags.append("counts toward PASS termination")
            recovery = event.get("metadata", {}).get("retry_recovery")
            if recovery and recovery.get("status") == "recovered":
                count = recovery.get("attempt_failure_count", 1)
                flags.append(f"recovered after {count} retryable attempt failure(s)")
            elif event.get("event_type") == "agent_error":
                flags.append(
                    "retryable attempt warning"
                    if event.get("metadata", {}).get("will_retry") is True
                    else "terminal recovery failure"
                )
            lines.extend(
                [
                    f"#### {label}",
                    "",
                    f"_{event['created_at']} · {event['event_type']} · {' · '.join(flags)} · `{event['id']}`_",
                    "",
                    event["content"] or "_(no message text)_",
                    "",
                ]
            )
    return "\n".join(lines)
