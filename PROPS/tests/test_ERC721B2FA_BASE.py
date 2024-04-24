import brownie, pytest, pathlib, json, random


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


@pytest.fixture(scope="module", autouse=True)
def ct(module_isolation, ERC721B2FA_BASE, ac):
    ct = ac["deployer"].deploy(ERC721B2FA_BASE)
    print("Contract deployed by " + ct.owner())

    ct.transferOwnership(ac["owner"], {"from": ac["deployer"]})
    print("Contract transfered to " + ct.owner())

    assert ct.owner() == ac["owner"]
    assert ct.isDelegate(ac["deployer"], {"from": ac["owner"]})
    with brownie.reverts("Ownable: caller is not the owner"):
        ct.transferOwnership(ac["deployer"], {"from": ac["deployer"]})

    return ct


def test_premint_misc(ct, ac):

    # Making sure we get the proper errors
    with brownie.reverts("ERC721Metadata: URI query for nonexistent token"):
        assert ct.tokenURI(1) == ""
    with brownie.reverts("ERC721: approved query for nonexistent token"):
        ct.getApproved(1)

    # Make sure contract doesn't accept ETH transfers
    assert ct.balance() == 0
    with brownie.reverts("I love ETH, but don't send it to this contract!"):
        ac["alex"].transfer(ct.address, "2 ether")
    assert ct.balance() == 0

    # test price settings
    assert ct.publicPrice() == 42000000000000000
    ct.setPublicPrice(43000000000000000, {"from": ac["deployer"]})
    assert ct.publicPrice() == 43000000000000000

    # test max mints per tx var
    assert ct.maxMintsPerTx() == 10
    ct.setMaxMintsPerTx(5, {"from": ac["deployer"]})
    assert ct.maxMintsPerTx() == 5

    # test withdrawal address setting
    ct.setWithdrawalAddy(
        "0x4A234b2Cbbe4053360397db002190732AB149A9a", {"from": ac["deployer"]}
    )
    assert ct.withdrawalAddy() == "0x4A234b2Cbbe4053360397db002190732AB149A9a"


def test_post_mint(ct, ac):
    # Testing pausing
    assert not ct.paused()
    with brownie.reverts("Invalid delegate"):
        ct.togglePause({"from": ac["alex"]})
    ct.togglePause({"from": ac["owner"]})
    assert ct.paused()

    ## TODO test trasnfers blocked

    ct.togglePause(0, {"from": ac["deployer"]})
    assert not ct.paused()
