from monkey_head.function_registry import (
    register_function,
    list_functions,
    get_functions,
)


@register_function
def _dummy():
    return "ok"


def test_registry():
    assert "_dummy" in list_functions()
    assert get_functions()["_dummy"]() == "ok"
