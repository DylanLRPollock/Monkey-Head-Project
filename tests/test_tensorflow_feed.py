import pytest

tf = pytest.importorskip("tensorflow")
from monkey_head.tensorflow_feed import train_from_project_sources


def test_train_from_project_sources():
    model = train_from_project_sources("logs", "prompts", "memory", epochs=1)
    assert isinstance(model, tf.keras.Model)
