from monkey_head.scripts.preload_data import preload_all


def test_preload_all():
    data = preload_all()
    assert data["prompts"], "Prompts should not be empty"
    assert (
        "PDF" in data["memory"] and data["memory"]["PDF"]
    ), "PDF memory should not be empty"
