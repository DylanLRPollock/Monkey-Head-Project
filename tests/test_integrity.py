# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Integrity module (tests)

import hashlib

from monkey_head.utils.integrity import sha256_digest, verify_checksums


def test_sha256_digest(tmp_path):
    file = tmp_path / "data.txt"
    content = b"hello world"
    file.write_bytes(content)
    assert sha256_digest(file) == hashlib.sha256(content).hexdigest()


def test_verify_checksums(tmp_path):
    file = tmp_path / "data.txt"
    file.write_text("data")
    good = {str(file): hashlib.sha256(b"data").hexdigest()}
    assert verify_checksums(good) == []
    bad = {str(file): "deadbeef"}
    assert verify_checksums(bad) == [str(file)]
