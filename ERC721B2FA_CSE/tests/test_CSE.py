import brownie, pytest, pathlib, json, random, logging

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="module", autouse=True)
def ct(module_isolation, CrazySassyExes, ac):
    ctr = ac["dep"].deploy(CrazySassyExes)
    print(ctr)
    LOGGER.info(f"\tContract deployed by {ctr.owner()} at {ctr.address}")

    assert not ctr.paused()

    ctr.transferOwnership(ac["owner"], {"from": ac["dep"]})
    LOGGER.info(f"Contract transfered to {ctr.owner()}")
    print(ctr.owner())

    assert ctr.owner() == ac["owner"]
    assert ctr.isDelegate(ac["dep"], {"from": ac["owner"]})
    with brownie.reverts("Ownable: caller is not the owner"):
        ctr.transferOwnership(ac["dep"], {"from": ac["dep"], 'gas_limit': 1000000, "allow_revert":True})

    return ctr


# TEST COMMON URI


def test_premint_misc(ct, ac):
    # Making sure we get the proper errors
    with brownie.reverts("ERC721Metadata: URI query for nonexistent token"):
        assert ct.tokenURI(1,{"from": ac["dep"], 'gas_limit': 1000000, "allow_revert":True}) == ""
    with brownie.reverts("ERC721: approved query for nonexistent token"):
        ct.getApproved(1,{"from": ac["dep"], 'gas_limit': 1000000, "allow_revert":True})
    # test max mints per tx var
    assert ct.maxPublicCSEMintsPerWallet() == 3
    print(f"Contract {ct}")

    ct.setmaxCSEMintsPerWallet(5, 5, {"from": ac["dep"]})
    assert ct.maxPublicCSEMintsPerWallet() == 5
    assert ct.maxPreSaleCSEMintsPerWallet() == 5
    ct.setmaxCSEMintsPerWallet(3, 3, {"from": ac["owner"]})

    # test withdrawal address setting
    ct.setPaymentRecipient(
        "0x4A234b2Cbbe4053360397db002190732AB149A9a", {"from": ac["owner"]}
    )
    assert ct.paymentRecipient() == "0x4A234b2Cbbe4053360397db002190732AB149A9a"

    assert not ct.paused()


def test_minting(ct, ac, accounts):
    with brownie.reverts("Public mint is not open yet!"):
        ct.publicMint(1, {"from": ac["bob"], 'gas_limit': 1000000, "allow_revert":True})

    ct.setMintPhase(2, {"from":ac['dep']})

    assert ct.maxPublicCSEMintsPerWallet() == 3

    print(f"Price = {ct.publicPriceDiscounted()}")

    ct.publicMint(3, {"from": accounts[7], "value":60000000000000000})
    with brownie.reverts("You have minted max during public phase."):
        ct.publicMint(1, {"from": accounts[7], 'gas_limit': 1000000, "allow_revert":True, "value":25000000000000000})

    with brownie.reverts("Can only set a lower size."):
        ct.setReducedMaxSupply(10001, {"from": ac['dep'],'gas_limit': 1000000, "allow_revert":True})

    with brownie.reverts("New supply lower than current totalSupply"):
        ct.setReducedMaxSupply(ct.totalSupply() - 1, {"from":ac['dep'], 'gas_limit': 1000000, "allow_revert":True})

    ct.setReducedMaxSupply(ct.totalSupply(), {"from":ac['dep'], 'gas_limit': 1000000, "allow_revert":True})

    ct.tokenURI(ct.totalSupply())
    with brownie.reverts():
        ct.tokenURI(ct.totalSupply() + 1, {"from":ac['dep'], 'gas_limit': 1000000, "allow_revert":True})

    with brownie.reverts("Max supply reached!"):
        ct.publicMint(1, {"from": accounts[8], 'gas_limit': 1000000, "allow_revert":True, "value":25000000000000000})

    pre_bal = ct.balance()
    ac["alex"].transfer(ct.address, "10 ether")
    print(ct.balance())
    assert ct.balance() == pre_bal + "10 ether"

    with brownie.reverts("Invalid delegate"):
        ct.setPaymentRecipient(ac["bob"], {"from": ac["alex"], 'gas_limit': 1000000, "allow_revert":True})

    ct.setPaymentRecipient(ac["bob"], {"from": ac["dep"]})

    bal = ac["bob"].balance()
    bal2 = ct.balance()
    print(f"bal = {bal}")
    print(f"ba2l = {ct.balance()}")

    ct.withdraw({"from":ac['dep']})
    assert ac["bob"].balance() == bal + bal2
    assert ct.balance() == 0


def test_token_uri(ct, ac, accounts):
    print(ct.totalSupply())
    assert ct.tokenURI(1) == ""
    ct.setBaseSuffixURI("blabla/", ".json", {"from":ac['dep']})
    assert ct.tokenURI(1) == "blabla/1.json"
    assert ct.tokenURI(2) == "blabla/2.json"

def test_blacklisting(ct, ac, accounts):
    ct.approve(ac['owner'], 1, {"from":accounts[7]})
    approvedd = ct.getApproved(1)
    print(approvedd)
    ct.setApprovalForAll(ac['bob'], True, {"from":accounts[7]})
    assert ct.isApprovedForAll(accounts[7], ac['bob'])

    ct.updateBlackListedApprovals([accounts[9]], [True], {"from":ac['dep']})
    with brownie.reverts("This opperator is blacklisted."):
        ct.approve(accounts[9], 2, {"from":accounts[7], 'gas_limit': 1000000, "allow_revert":True})
        ct.setApprovalForAll([accounts[9]], [True], {"from":accounts[7], 'gas_limit': 1000000, "allow_revert":True})

    ct.approve(accounts[6], 3, {"from":accounts[7]})
    ct.setApprovalForAll(accounts[6], True, {"from":accounts[7]})


"""
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
"""