import brownie, pytest, pathlib, json, random, logging

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="module", autouse=True)
def contractzz(module_isolation, TheTimeIsDAO, ac, accounts):
    ctr = ac["dep"].deploy(TheTimeIsDAO)
    assert ctr.owner() == ac["dep"]
    print(f"TTDAO contract = {ctr}")
    print(f"\tContract deployed by {ctr.owner()} == {ac['dep']} at {ctr.address}")

    ctr.transferOwnership(ac["owner"], {"from": ac["dep"]})
    print(f"Contract transfered to {ctr.owner()} == {ac['owner']}")

    assert ctr.owner() == ac["owner"]
    assert ctr.isDelegate(ac["dep"], {"from": ac["owner"]})
    with brownie.reverts("Ownable: caller is not the owner"):
        ctr.transferOwnership(
            ac["dep"], {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True}
        )

    return ctr


@pytest.fixture(scope="module", autouse=True)
def get_merkle_stuff(module_isolation, ac):
    base_path = pathlib.Path(__file__).parent.resolve()
    mt_json_file_loc = (
        str(base_path)
        + "/../scripts/merkleTreeJS_TTDAO/out/1_MerkleTree_1674408123647.json"
    )
    mt_json_file = open(mt_json_file_loc, "r")
    print("path = " + str(base_path))
    mt_json = json.loads(mt_json_file.read())

    merkle_root = mt_json["root"]
    print("- ROOT = " + merkle_root)
    merkle_addys = mt_json["addys"]
    print("- Merkle Addys: " + str(merkle_addys))
    merkle_proofs = mt_json["proofs"]
    print("- Markle Proofs: " + str(merkle_proofs))

    return merkle_root, merkle_addys, merkle_proofs


@pytest.fixture(scope="module")
def setup_merkleTree(module_isolation, get_merkle_stuff, accounts, ac, contractzz):
    ct = contractzz
    merkle_root, merkle_addys, merkle_proofs = get_merkle_stuff

    with brownie.reverts("Invalid delegate"):
        ct.setMerkleRoot(merkle_root, {"from": ac["bob"]})
    ct.setMerkleRoot(merkle_root, {"from": ac["dep"]})

    m_proof_list = merkle_proofs[0].split(",")
    assert ct.isvalidMerkleProof(m_proof_list, {"from": accounts[0]})
    m_proof_list = merkle_proofs[1].split(",")
    assert ct.isvalidMerkleProof(m_proof_list, {"from": accounts[1]})
    m_proof_list = merkle_proofs[2].split(",")
    assert ct.isvalidMerkleProof(m_proof_list, {"from": accounts[2]})
    assert not ct.isvalidMerkleProof([], {"from": accounts[5]})

    return merkle_root, merkle_addys, merkle_proofs


def test_misc(contractzz, ac, accounts):
    print(f"ct == {contractzz}")
    ctr = contractzz
    # Making sure we get the proper errors
    with brownie.reverts("ERC721Metadata: URI query for nonexistent token"):
        assert (
            ctr.tokenURI(
                1, {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True}
            )
            == ""
        )
    with brownie.reverts("ERC721: approved query for nonexistent token"):
        ctr.getApproved(
            1, {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True}
        )

    with brownie.reverts("Ownable: caller is not the owner"):
        ctr.setPaymentRecipient(accounts[9], {"from": ac["dep"]})
    ctr.setPaymentRecipient(accounts[9], {"from": ac["owner"]})
    assert ctr.paymentRecipient() == accounts[9]


def test_minting(contractzz, ac, accounts, setup_merkleTree):
    ct = contractzz
    merkle_root, merkle_addys, merkle_proofs = setup_merkleTree

    # TESTING powerPassMint

    with brownie.reverts("Mint not open yet!"):
        ct.daoMint(
            merkle_proofs[0].split(","),
            {"from": accounts[0], "gas_limit": 1000000, "allow_revert": True},
        )
    ct.toggleMint(True, {"from": ac["dep"]})

    with brownie.reverts("You are not authorized to mint!"):
        ct.daoMint(
            merkle_proofs[0].split(","),
            {"from": accounts[5], "gas_limit": 1000000, "allow_revert": True},
        )
    ct.daoMint(
        merkle_proofs[0].split(","),
        {"from": accounts[0], "gas_limit": 1000000, "allow_revert": True},
    )
    assert ct.balanceOf(accounts[0]) == 1
    with brownie.reverts("You already minted!"):
        ct.daoMint(
            merkle_proofs[0].split(","),
            {"from": accounts[0], "gas_limit": 1000000, "allow_revert": True},
        )

    assert ct.balance() == 0
    ct.daoMint(
        merkle_proofs[1].split(","),
        {
            "from": accounts[1],
            "value": 1420000000000000,
            "gas_limit": 1000000,
            "allow_revert": True,
        },
    )
    assert ct.balance() == 1420000000000000
    assert ct.balanceOf(accounts[1]) == 1

    assert ct.totalSupply() == 2


def test_pausing_andwithdraw(contractzz, ac, accounts):
    ct = contractzz

    acc_0_tokens = ct.walletOfOwner(accounts[0])

    with brownie.reverts("Transfers are blocked!"):
        ct.safeTransferFrom(
            accounts[0],
            accounts[6],
            1,
            {"from": accounts[0], "gas_limit": 1000000, "allow_revert": True},
        )
        ct.safeTransferFrom(
            accounts[1],
            accounts[6],
            2,
            {"from": accounts[1], "gas_limit": 1000000, "allow_revert": True},
        )

    with brownie.reverts("ERC721: transfer caller is not owner nor approved"):
        ct.safeTransferFrom(
            accounts[0],
            accounts[6],
            1,
            {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True},
        )
    ct.setApprovalForAll(ac["dep"], True, {"from": accounts[0]})
    ct.safeTransferFrom(
        accounts[0],
        accounts[6],
        1,
        {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True},
    )
    assert ct.ownerOf(1) == accounts[6]

    with brownie.reverts("Ownable: caller is not the owner"):
        ct.burn(
            1,
            {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True},
        )
    assert ct.ownerOf(1) == accounts[6]
    ct.burn(
        1,
        {"from": ac["owner"], "gas_limit": 1000000, "allow_revert": True},
    )
    with brownie.reverts("ERC721: owner query for nonexistent token"):
        assert ct.ownerOf(1) == "0x0000000000000000000000000000000000000000"
    assert ct.ownerOf(2) == accounts[1]
    assert ct.transfers_blocked()
    with brownie.reverts("Ownable: caller is not the owner"):
        ct.toggleTransfersBlocked(
            False,
            {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True},
        )
    print(f"tr blocked == {ct.transfers_blocked()}")

    ct.toggleTransfersBlocked(
        False,
        {"from": ac["owner"], "gas_limit": 1000000, "allow_revert": True},
    )
    print(f"tr blocked == {ct.transfers_blocked()}")
    assert not ct.transfers_blocked()
    ct.safeTransferFrom(
        accounts[1],
        accounts[6],
        2,
        {"from": accounts[1], "gas_limit": 1000000, "allow_revert": True},
    )
    assert ct.ownerOf(2) == accounts[6]

    acc9_bal = accounts[9].balance()
    ctr_bal = ct.balance()
    ct.withdraw(
        {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True},
    )

    ct.freeTeamMints(1, [accounts[5]])
    assert ct.balanceOf(accounts[5]) == 1
    ct.freeTeamMints(3, [accounts[5], accounts[5], accounts[4]])
    assert ct.balanceOf(accounts[5]) == 3
    assert ct.balanceOf(accounts[4]) == 1

    assert ct.balance() == 0
    assert accounts[9].balance() == acc9_bal + ctr_bal
