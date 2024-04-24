import pytest
from brownie import (
    accounts,
    config,
    network,
)


@pytest.fixture(scope="module", autouse=True)
def ac(module_isolation):
    acc = {
        "dep": accounts[0],
        "owner": accounts[1],
        "pp_dep": accounts[2],
        "bob": accounts[3],
    }
    return acc
