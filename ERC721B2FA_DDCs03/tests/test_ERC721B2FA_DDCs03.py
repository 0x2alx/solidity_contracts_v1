import brownie, pytest, pathlib, json, random, logging

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="module", autouse=True)
def ct(module_isolation, DemonicDorks, ac):
    ctr = ac["dep"].deploy(DemonicDorks)
    print(ctr)
    LOGGER.info(f"\tContract deployed by {ctr.owner()} at {ctr.address}")

    assert ctr.paused()

    ctr.transferOwnership(ac["owner"], {"from": ac["dep"]})
    LOGGER.info(f"Contract transfered to {ctr.owner()}")
    print(ctr.owner())

    assert ctr.owner() == ac["owner"]
    assert ctr.isDelegate(ac["dep"], {"from": ac["owner"]})
    with brownie.reverts("Ownable: caller is not the owner"):
        ctr.transferOwnership(ac["dep"], {"from": ac["dep"]})

    return ctr


# TEST COMMON URI


def test_premint_misc(ct, ac):
    # Making sure we get the proper errors
    with brownie.reverts("ERC721Metadata: URI query for nonexistent token"):
        assert ct.tokenURI(1) == ""
    with brownie.reverts("ERC721: approved query for nonexistent token"):
        ct.getApproved(1)
    # test max mints per tx var
    assert ct.maxPublicDDPerWallet() == 3
    print(f"Contract {ct}")

    ct.setMaxPublicDDPerWallet(25, {"from": ac["dep"]})
    assert ct.maxPublicDDPerWallet() == 25
    ct.setMaxPublicDDPerWallet(3, {"from": ac["owner"]})

    # test withdrawal address setting
    ct.setPaymentRecipient(
        "0x4A234b2Cbbe4053360397db002190732AB149A9a", {"from": ac["owner"]}
    )
    assert ct.getPaymentRecipient() == "0x4A234b2Cbbe4053360397db002190732AB149A9a"

    assert ct.paused() == True


def test_minting(ct, ac, accounts):

    with brownie.reverts("Public mint is not open yet!"):
        ct.feelinMinty(1, {"from": ac["bob"]})

    ct.togglePause(0, {"from": ac["dep"]})
    assert ct.paused() == False

    assert ct.maxPublicDDPerWallet() == 3
    with brownie.reverts("You can only mint one DD at a time"):
        ct.feelinMinty(2, {"from": accounts[19]})
    print(f"NFTs in wallet 1 = " + str(ct.balanceOf(accounts[19])))
    ct.feelinMinty(1, {"from": accounts[19]})
    print(f"NFTs in wallet 2 = " + str(ct.balanceOf(accounts[19])))
    ct.setMaxPublicDDPerTx(2, {"from": ac["dep"]})
    print(f"NFTs in wallet 3 = " + str(ct.balanceOf(accounts[19])))
    with brownie.reverts("You can only mint one DD at a time"):
        ct.feelinMinty(3, {"from": accounts[19]})
    ct.feelinMinty(2, {"from": accounts[19]})
    print(f"NFTs in wallet 4 = " + str(ct.balanceOf(accounts[19])))
    print(f"NFTs in wallet 5 = " + str(ct.balanceOf(accounts[19])))
    with brownie.reverts("Max NFTs per wallet reached!"):
        ct.feelinMinty(1, {"from": accounts[19]})
    ct.setMaxPublicDDPerTx(1, {"from": ac["dep"]})
    assert len(ct.walletOfOwner(accounts[19])) == 3

    tot_sup = ct.totalSupply()
    mints = 0
    for i in range(0, 10):
        r_m = 1
        for ii in range(0, 3):
            mints += r_m
            ct.feelinMinty(r_m, {"from": accounts[5 + i]})
            print(f"MINTING {ii} for {i}")

    assert tot_sup + mints == ct.totalSupply()

    assert ct.paused() == False
    ct.togglePause(1, {"from": ac["dep"]})
    assert ct.paused() == True

    with brownie.reverts("Public mint is not open yet!"):
        ct.feelinMinty(1, {"from": ac["alex"]})
    ct.feelinMinty(1, {"from": ac["dep"]})
    assert ct.paused() == True
    ct.togglePause(0, {"from": ac["dep"]})

    with brownie.reverts("Can only set a lower size."):
        ct.setReducedMaxSupply(10001)

    with brownie.reverts("New supply lower current totalSupply"):
        ct.setReducedMaxSupply(ct.totalSupply() - 1)

    ct.setReducedMaxSupply(ct.totalSupply())

    ct.tokenURI(ct.totalSupply())
    with brownie.reverts():
        ct.tokenURI(ct.totalSupply() + 1)

    with brownie.reverts("Max supply reached!"):
        ct.feelinMinty(1, {"from": accounts[18]})


def test_withdrawal(ct, ac):
    assert ct.balance() == 0
    ac["alex"].transfer(ct.address, "10 ether")
    print(ct.balance())
    assert ct.balance() == "10 ether"

    with brownie.reverts("Invalid delegate"):
        ct.setPaymentRecipient(ac["bob"], {"from": ac["alex"]})

    ct.setPaymentRecipient(ac["bob"], {"from": ac["dep"]})

    bal = ac["bob"].balance()
    ct.withdraw()
    assert ac["bob"].balance() == bal + "10 ether"
    assert ct.balance() == 0


def test_token_uri(ct, ac, accounts):
    assert ct.tokenURI(1) == ""
    ct.setCommonURI("testtt")
    assert ct.tokenURI(1) == "testtt"
    ct.setBaseSuffixURI("blabla/", ".json")
    assert ct.tokenURI(1) == "testtt"
    ct.setCommonURI("revealed")
    assert ct.tokenURI(1) == "blabla/1.json"
    assert ct.tokenURI(10) == "blabla/10.json"


def test_post_mint(ct, ac, accounts):
    # assert len(ct.walletOfOwner(ac["alex"])) == 300
    print(f"total sup = " + str(ct.totalSupply()))
    ct.safeTransferFrom(ct.ownerOf(1), ac["ow"], 1, {"from": ct.ownerOf(1)})
    ct.safeTransferFrom(ct.ownerOf(12), ac["ow2"], 12, "", {"from": ct.ownerOf(12)})
    ct.safeTransferFrom(ct.ownerOf(13), ac["ow"], 13, {"from": ct.ownerOf(13)})
    ct.safeTransferFrom(ct.ownerOf(14), ac["ow"], 14, {"from": ct.ownerOf(14)})
    ct.safeTransferFrom(ct.ownerOf(15), ac["ow2"], 15, {"from": ct.ownerOf(15)})
    ct.safeTransferFrom(ct.ownerOf(16), ac["ow"], 16, "", {"from": ct.ownerOf(16)})
    assert len(ct.walletOfOwner(ac["ow"])) == 4
    assert len(ct.walletOfOwner(ac["ow2"])) == 2
    print(ct.walletOfOwner(ac["ow"]))
    print(ct.walletOfOwner(ac["ow2"]))

    ct.proposeGuardian(ac["ga"], {"from": ac["ow"]})
    ct.proposeGuardian(ac["ga"], {"from": ac["ow2"]})

    with brownie.reverts("!guardian"):
        ct.lockMany([1, 12], {"from": ac["bob"]})

    with brownie.reverts("!guardian"):
        ct.lockMany([1, 12, 14, 16], {"from": ac["ga"]})
    ct.acceptGuardianship(ac["ow"], {"from": ac["ga"]})
    ct.acceptGuardianship(ac["ow2"], {"from": ac["ga"]})

    with brownie.reverts("Cannot update map"):
        ct.lockMany([1, 12], {"from": ac["ga"]})
    ct.updateApprovedContracts([ct.address], [True], {"from": ac["dep"]})
    with brownie.reverts():
        ct.lockMany([1, 12, 14, 16], {"from": ac["ow"]})
    ct.lockMany([1, 12, 14, 15, 16], {"from": ac["ga"]})

    with brownie.reverts("Token is locked"):
        ct.safeTransferFrom(ac["ow"], ac["alex"], 1, {"from": ac["ow"]})
        ct.safeTransferFrom(ac["ow"], ac["alex"], 12, {"from": ac["ow"]})

    with brownie.reverts("ERC721: transfer caller is not owner nor approved"):
        ct.safeTransferFrom(ac["ow"], ac["alex"], 13, {"from": ac["ga"]})
        ct.safeTransferFrom(ac["ow"], ac["alex"], 13, {"from": ac["dep"]})
    ct.safeTransferFrom(ac["ow"], ac["alex"], 13, {"from": ac["ow"]})

    with brownie.reverts("!guardian"):
        ct.unlockMany([1, 15], {"from": ac["ow"]})
        ct.unlockMany([1, 15], {"from": ac["ow2"]})
        ct.unlockMany([1, 15], {"from": ac["dep"]})
    ct.unlockMany([1, 15], {"from": ac["ga"]})

    with brownie.reverts("ERC721: transfer caller is not owner nor approved"):
        ct.safeTransferFrom(ac["ow"], ac["alex"], 1, {"from": ac["ga"]})
        ct.safeTransferFrom(ac["ow"], ac["alex"], 1, {"from": ac["owner"]})

    ct.safeTransferFrom(ac["ow"], ac["alex"], 1, "", {"from": ac["ow"]})

    assert ct.ownerOf(1) == ac["alex"]
    assert ct.ownerOf(12) != ct.ownerOf(14)
    with brownie.reverts():
        ct.unlockManyAndTransfer([12, 14], ac["alex"], {"from": ac["alex"]})
        ct.unlockManyAndTransfer([12, 14], ac["alex"], {"from": ac["ow"]})
    assert ct.ownerOf(12) != ct.ownerOf(14)
    ct.unlockManyAndTransfer([12, 14], ac["alex"], {"from": ac["ga"]})

    assert ct.ownerOf(12) == ac["alex"]
    assert ct.ownerOf(14) == ac["alex"]

    assert (
        ct.isUnlocked(1)
        and ct.isUnlocked(12)
        and ct.isUnlocked(14)
        and not ct.isUnlocked(16)
    )

    ct.renounce(ac["ow"], {"from": ac["ga"]})
    with brownie.reverts("!guardian"):
        ct.unlockMany([16], {"from": ac["ga"]})

    assert not ct.isUnlocked(16)
    ct.updateApprovedContracts([ct.address], [False], {"from": ac["dep"]})
    with brownie.reverts():
        ct.freeId(16, ct.address, {"from": ac["alex"]})
        ct.freeId(16, ct.address, {"from": ac["bob"]})
    # ct.freeId(16, ct.address, {"from": ac["owner"]})
    assert ct.isUnlocked(16)
