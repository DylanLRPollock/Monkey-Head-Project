# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Cloud Pyramid module (tests)

from monkey_head.cloud_pyramid import CloudPyramid


def test_decision_process():
    pyramid = CloudPyramid()
    result = pyramid.decide("test proposal")
    assert isinstance(result, bool)
