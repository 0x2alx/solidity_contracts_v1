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
    accounts[8].transfer(acc_10, "5 ether")
    accounts[8].transfer(acc_11, "5 ether")
    accounts[8].transfer(acc_12, "5 ether")
    accounts[8].transfer(acc_13, "5 ether")
    return acc
