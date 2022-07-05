import Test1
import pytest


@pytest.mark.add
def test_add():
    assert Test1.add(2, 3) == 5
    assert Test1.add(2) == 4


@pytest.mark.productss
def test_multiply():
    assert Test1.product(2, 2) == 4
    assert Test1.product(3) == 6
