import brownie, pytest, pathlib, json, random, logging

LOGGER = logging.getLogger(__name__)


@pytest.fixture()
def isolation(fn_isolation):
    pass


@pytest.fixture(scope="module", autouse=True)
def ct(module_isolation, ERC721B2FA_REMNANTS, ac):
    ct = ac["dep"].deploy(ERC721B2FA_REMNANTS)
    LOGGER.info(f"\tContract deployed by {ct.owner()} at {ct.address}")

    ct.transferOwnership(ac["owner"], {"from": ac["dep"]})
    LOGGER.info(f"Contract transfered to {ct.owner()}")

    assert ct.owner() == ac["owner"]
    assert ct.isDelegate(ac["dep"], {"from": ac["owner"]})
    with brownie.reverts("Ownable: caller is not the owner"):
        ct.transferOwnership(ac["dep"], {"from": ac["dep"]})

    return ct


def test_premint_misc(ct, ac):
    # Making sure we get the proper errors
    with brownie.reverts("ERC721Metadata: URI query for nonexistent token"):
        assert ct.tokenURI(1) == ""
    with brownie.reverts("ERC721: approved query for nonexistent token"):
        ct.getApproved(1)

    # test withdrawal address setting
    ct.setWithdrawalAddy(
        "0x4A234b2Cbbe4053360397db002190732AB149A9a", {"from": ac["dep"]}
    )
    assert ct.getWithdrawalAddy() == "0x4A234b2Cbbe4053360397db002190732AB149A9a"


def test_mint(ct, ac):
    assert ct.totalSupply() == 0
    with brownie.reverts():
        ct.ghostyMint(3, [ac["owner"]], {"from": ac["bob"]})
    ct.ghostyMint(3, [ac["owner"]], {"from": ac["dep"]})

    assert ct.totalSupply() == 3
    assert ct.tokenURI(1) == ""
    ct.setBaseSuffixURI("blabla/", ".bllll")
    assert ct.tokenURI(1) == "blabla/1.bllll"


def test_post_mint(ct, ac):
    owner_wallet = ct.walletOfOwner(ac["owner"])
    assert len(owner_wallet) == 3

    assert len(ct.walletOfOwner(ac["alex"])) == 0
    ct.safeTransferFrom(ac["owner"], ac["alex"], 1, {"from": ac["owner"]})
    ct.safeTransferFrom(ac["owner"], ac["alex"], 2, "", {"from": ac["owner"]})
    ct.safeTransferFrom(ac["owner"], ac["alex"], 3, "", {"from": ac["owner"]})
    assert len(ct.walletOfOwner(ac["alex"])) == 3
    assert len(ct.walletOfOwner(ac["owner"])) == 0

    ct.setGuardian(ac["bob"], {"from": ac["alex"]})

    with brownie.reverts():
        ct.lockMany([1, 2], {"from": ac["bob"]})

    ct.updateApprovedContracts([ct.address], [True], {"from": ac["dep"]})
    with brownie.reverts():
        ct.lockMany([1, 2], {"from": ac["alex"]})

    ct.lockMany([1, 2, 3], {"from": ac["bob"]})

    with brownie.reverts("Token is locked"):
        ct.safeTransferFrom(ac["alex"], ac["owner"], 1, {"from": ac["alex"]})
        ct.safeTransferFrom(ac["alex"], ac["owner"], 2, "", {"from": ac["bob"]})

    ct.unlockMany([1], {"from": ac["bob"]})

    with brownie.reverts():
        ct.safeTransferFrom(ac["alex"], ac["owner"], 1, {"from": ac["bob"]})

    ct.safeTransferFrom(ac["alex"], ac["owner"], 1, {"from": ac["alex"]})
    assert len(ct.walletOfOwner(ac["owner"])) == 1

    with brownie.reverts():
        ct.unlockManyAndTransfer([2], ac["dep"], {"from": ac["alex"]})
        ct.unlockManyAndTransfer([2], ac["dep"], {"from": ac["dep"]})

    ct.unlockManyAndTransfer([2], ac["dep"], {"from": ac["bob"]})
    assert len(ct.walletOfOwner(ac["dep"])) == 1

    with brownie.reverts():
        ct.safeTransferFrom(ac["dep"], ac["owner"], 2, {"from": ac["bob"]})
    ct.renounce(ac["alex"], {"from": ac["bob"]})
    with brownie.reverts("!guardian"):
        ct.lockMany([3], {"from": ac["bob"]})

    ct.safeTransferFrom(ac["dep"], ac["owner"], 2, {"from": ac["dep"]})

    assert not ct.isUnlocked(3)
    ct.updateApprovedContracts([ct.address], [False], {"from": ac["dep"]})
    with brownie.reverts():
        ct.freeId(3, ct.address, {"from": ac["alex"]})
        ct.freeId(3, ct.address, {"from": ac["bob"]})
    ct.freeId(3, ct.address, {"from": ac["dep"]})
    assert ct.isUnlocked(3)


def test_withdrawal(ct, ac):
    assert ct.balance() == 0
    ac["alex"].transfer(ct.address, "10 ether")
    print(ct.balance())
    assert ct.balance() == "10 ether"

    with brownie.reverts():
        ct.setWithdrawalAddy(ac["bob"], {"from": ac["alex"]})

    ct.setWithdrawalAddy(ac["bob"], {"from": ac["dep"]})

    assert ac["bob"].balance() == "100 ether"
    ct.withdraw()
    assert ac["bob"].balance() == "110 ether"
    assert ct.balance() == 0
