import pytest
from brownie import (
    accounts,
    config,
    network,
)


@pytest.fixture(scope="module", autouse=True)
def ac(module_isolation):
    acc = {
        "dep": accounts[20],
        "owner": accounts[0],
        "alex": accounts[1],
        "bob": accounts[2],
        "ow": accounts[18],
        "ow2": accounts[16],
        "ga": accounts[17],
    }
    return acc
