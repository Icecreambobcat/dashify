import pytest

def test_true():
    assert True

@pytest.mark.xfail
def test_false():
    assert False
