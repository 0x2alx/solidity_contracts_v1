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
        "owner": accounts[0],
        "alex": accounts[1],
        "bob": accounts[2],
    }
    return acc
