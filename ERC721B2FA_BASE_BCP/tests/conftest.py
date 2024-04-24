import pytest
from brownie import (
    accounts,
    config,
    network,
)


@pytest.fixture(scope="module", autouse=True)
def ac(module_isolation):
    acc = {
        "deployer": accounts[0],
        "owner": accounts[1],
        "alex": accounts[2],
        "bob": accounts[9],
    }
    return acc
