# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Chat Learning module (tests)

import pytest

tf = pytest.importorskip("tensorflow")
from monkey_head.chat_learning import train_from_chat_and_pdfs


def test_train_from_chat_and_pdfs(tmp_path):
    chat = ["hello world", "goodbye world"]
    pdf_file = "memory/PDF/Linux_on_PlayStation_3.pdf"
    model = train_from_chat_and_pdfs(chat, [pdf_file], epochs=1)
    assert isinstance(model, tf.keras.Model)
