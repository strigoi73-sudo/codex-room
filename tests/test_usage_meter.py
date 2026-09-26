from codex_room.usage_meter import normalize_usage_meter, usage_meter_delta


def test_usage_meter_delta_suppresses_percentage_delta_across_window_reset():
    before = normalize_usage_meter(
        {
            "rate_limits": {
                "status": "available",
                "data": {
                    "rateLimits": {
                        "limitId": "codex",
                        "primary": {
                            "usedPercent": 90,
                            "windowDurationMins": 300,
                            "resetsAt": 100,
                        },
                    }
                },
            },
            "account_usage": {
                "status": "available",
                "data": {"summary": {"lifetimeTokens": 100}},
            },
        },
        captured_at="before",
    )
    after = normalize_usage_meter(
        {
            "rate_limits": {
                "status": "available",
                "data": {
                    "rateLimits": {
                        "limitId": "codex",
                        "primary": {
                            "usedPercent": 5,
                            "windowDurationMins": 300,
                            "resetsAt": 200,
                        },
                    }
                },
            },
            "account_usage": {
                "status": "available",
                "data": {"summary": {"lifetimeTokens": 150}},
            },
        },
        captured_at="after",
    )

    delta = usage_meter_delta(before, after)
    assert delta["lifetime_tokens_delta"] == 50
    window = delta["rate_limit_window_deltas"][0]
    assert window["reset_changed"] is True
    assert window["delta_percentage_points"] is None
