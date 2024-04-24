import pytest
from brownie import (
    accounts,
    config,
    network,
)


@pytest.fixture(scope="module", autouse=True)
def ac(module_isolation):
    acc_10 = accounts.add()
    acc_11 = accounts.add()
    acc_12 = accounts.add()
    acc_13 = accounts.add()
    acc = {
        "dep": acc_10,
        "owner": acc_11,
        "alex": acc_12,
        "bob": acc_13,
    }
    accounts[9].transfer(acc_10, "10 ether")
    accounts[9].transfer(acc_11, "10 ether")
    accounts[9].transfer(acc_12, "10 ether")
    accounts[9].transfer(acc_13, "10 ether")
    return acc
