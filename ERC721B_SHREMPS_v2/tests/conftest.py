import pytest
from brownie import (
    accounts,
    config,
    network,
)


@pytest.fixture(scope="module", autouse=True)
def ac(module_isolation):
    acc = {
        "dep": accounts[9],
        "owner": accounts[8],
        "alex": accounts[7],
        "bob": accounts[6],
    }
    return acc
