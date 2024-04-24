import brownie, pytest, pathlib, json, random, logging

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="module", autouse=True)
def contractzz(module_isolation, BlazingWomen, test_pp, ac, accounts):
    ctr = ac["dep"].deploy(BlazingWomen)
    assert ctr.owner() == ac["dep"]
    print(f"BW contract = {ctr}")
    print(f"\tContract deployed by {ctr.owner()} == {ac['dep']} at {ctr.address}")

    assert not ctr.paused()

    ctr.transferOwnership(ac["owner"], {"from": ac["dep"]})
    print(f"Contract transfered to {ctr.owner()} == {ac['owner']}")

    assert ctr.owner() == ac["owner"]
    assert ctr.isDelegate(ac["dep"], {"from": ac["owner"]})
    with brownie.reverts("Ownable: caller is not the owner"):
        ctr.transferOwnership(
            ac["dep"], {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True}
        )

    pp_ctr = ac["pp_dep"].deploy(test_pp)
    print(f"power pass contract = {pp_ctr}")

    ctr.updatePowerPassContractAddress(pp_ctr.address, {"from": ac["dep"]})
    assert ctr.POWERPASS_CONTRACT() == pp_ctr.address
    for i in range(5, 10):
        for ii in range(1, i):
            pp_ctr.mint(accounts[i], {"from": ac["pp_dep"]})
        print(f"balance for addy {accounts[i]} = {pp_ctr.balanceOf(accounts[i])}")
        ctr_pp_bal = ctr.getPowerPassBalance(accounts[i], {"from": accounts[i]})
        print(f"ctr_pp_bal == {ctr_pp_bal}")
        print(f"balanceOf PP = {pp_ctr.balanceOf(accounts[i])} / {ctr_pp_bal}")
        assert pp_ctr.balanceOf(accounts[i]) == ctr_pp_bal
    ctr_pp_bal = ctr.getPowerPassBalance(accounts[0], {"from": accounts[0]})
    print(f"balanceOf PP = {pp_ctr.balanceOf(accounts[0])} / {ctr_pp_bal}")
    print(f"totalSupply() = {pp_ctr.totalSupply()}")

    return ctr, pp_ctr


@pytest.fixture(scope="module", autouse=True)
def get_merkle_stuff(module_isolation, ac):
    base_path = pathlib.Path(__file__).parent.resolve()
    mt_json_file_loc = (
        str(base_path)
        + "/../scripts/merkleTreeJS_POW/out/1_MerkleTree_1669514978377.json"
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
    ct = contractzz[0]
    pp_ctr = contractzz[1]
    merkle_root, merkle_addys, merkle_proofs = get_merkle_stuff

    with brownie.reverts("Invalid delegate"):
        ct.setMerkleRoot(merkle_root, {"from": ac["bob"]})
    ct.setMerkleRoot(merkle_root, {"from": ac["dep"]})

    m_proof_list = merkle_proofs[0].split(",")
    assert ct.isvalidMerkleProof(m_proof_list, {"from": accounts[9]})
    m_proof_list = merkle_proofs[1].split(",")
    assert ct.isvalidMerkleProof(m_proof_list, {"from": accounts[8]})
    m_proof_list = merkle_proofs[2].split(",")
    assert ct.isvalidMerkleProof(m_proof_list, {"from": accounts[7]})
    assert not ct.isvalidMerkleProof([], {"from": accounts[0]})

    return merkle_root, merkle_addys, merkle_proofs


def test_pricing(contractzz, ac, accounts):
    ctr = contractzz[0]
    pp_ctr = contractzz[1]

    phase_one_conf = ctr.powerPassHolderPhaseOneConf()
    print(f"phase_one_conf = {phase_one_conf}")
    phase_two_conf = ctr.powerListPhaseTwoConf()
    print(f"phase_two_conf = {phase_two_conf}")
    phase_three_conf = ctr.publicPhaseThreeConf()
    print(f"phase_three_conf = {phase_three_conf}")

    price_1 = ctr.getTotalMintPrice(1, 1)
    price_6 = ctr.getTotalMintPrice(6, 1)
    price_11 = ctr.getTotalMintPrice(11, 1)
    print(
        f"Power Pass price for 1, 6, 11 == {price_1/1000000000000000000}, {price_6/1000000000000000000}, {price_11/1000000000000000000}"
    )
    assert price_1 == phase_one_conf[1]
    assert price_6 == 6 * phase_one_conf[2]
    assert price_11 == 11 * phase_one_conf[3]

    price_1 = ctr.getTotalMintPrice(1, 2)
    price_6 = ctr.getTotalMintPrice(6, 2)
    price_11 = ctr.getTotalMintPrice(11, 2)
    print(
        f"Power List price for 1, 6, 11 == {price_1/1000000000000000000}, {price_6/1000000000000000000}, {price_11/1000000000000000000}"
    )
    assert price_1 == phase_two_conf[1]
    assert price_6 == 6 * phase_two_conf[2]
    assert price_11 == 11 * phase_two_conf[3]

    price_1 = ctr.getTotalMintPrice(1, 3)
    price_6 = ctr.getTotalMintPrice(6, 3)
    price_11 = ctr.getTotalMintPrice(11, 3)
    print(
        f"Power List price for 1, 6, 11 == {price_1/1000000000000000000}, {price_6/1000000000000000000}, {price_11/1000000000000000000}"
    )
    assert price_1 == phase_three_conf[1]
    assert price_6 == 6 * phase_three_conf[2]
    assert price_11 == 11 * phase_three_conf[3]


def test_misc(contractzz, ac, accounts):
    print(f"ct == {contractzz}")
    ctr = contractzz[0]
    pp_ctr = contractzz[1]
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

    phase_one_conf = ctr.powerPassHolderPhaseOneConf()
    print(f"phase_one_conf = {phase_one_conf}")
    phase_two_conf = ctr.powerListPhaseTwoConf()
    print(f"phase_two_conf = {phase_two_conf}")
    phase_three_conf = ctr.publicPhaseThreeConf()
    print(f"phase_three_conf = {phase_three_conf}")

    assert phase_one_conf[0] == 10
    assert phase_one_conf[1] == 40000000000000000

    assert phase_two_conf[0] == 10
    assert phase_two_conf[1] == 60000000000000000

    assert phase_three_conf[0] == 4242
    assert phase_three_conf[1] == 80000000000000000

    ctr.setPowerPassHolderPhaseOneConf(
        11, 50000000000000000, 50000000000000000, 50000000000000000, {"from": ac["dep"]}
    )
    ctr.setPowerListPhaseTwoConf(
        12, 70000000000000000, 70000000000000000, 70000000000000000, {"from": ac["dep"]}
    )
    ctr.setPublicPhaseThreeConf(
        4242,
        90000000000000000,
        90000000000000000,
        90000000000000000,
        {"from": ac["dep"]},
    )

    phase_one_conf = ctr.powerPassHolderPhaseOneConf()
    print(f"phase_one_conf = {phase_one_conf}")
    phase_two_conf = ctr.powerListPhaseTwoConf()
    print(f"phase_two_conf = {phase_two_conf}")
    phase_three_conf = ctr.publicPhaseThreeConf()
    print(f"phase_three_conf = {phase_three_conf}")

    assert phase_one_conf[0] == 11
    assert phase_one_conf[1] == 50000000000000000

    assert phase_two_conf[0] == 12
    assert phase_two_conf[1] == 70000000000000000

    assert phase_three_conf[0] == 4242
    assert phase_three_conf[1] == 90000000000000000

    ctr.setPowerPassHolderPhaseOneConf(
        10, 40000000000000000, 38000000000000000, 36000000000000000, {"from": ac["dep"]}
    )
    ctr.setPowerListPhaseTwoConf(
        10, 60000000000000000, 57000000000000000, 54000000000000000, {"from": ac["dep"]}
    )
    ctr.setPublicPhaseThreeConf(
        4242,
        80000000000000000,
        76000000000000000,
        72000000000000000,
        {"from": ac["dep"]},
    )

    assert ctr.powerPassHolderMints(accounts[0]) == 0
    assert ctr.powerPassHolderMints(accounts[4]) == 0
    assert ctr.powerPassHolderMints(accounts[6]) == 0

    assert ctr.powerlistMints(accounts[1]) == 0
    assert ctr.powerlistMints(accounts[2]) == 0
    assert ctr.powerlistMints(accounts[5]) == 0

    assert ctr.publicMints(accounts[3]) == 0
    assert ctr.publicMints(accounts[8]) == 0
    assert ctr.publicMints(accounts[9]) == 0

    ctr.setPaymentRecipient(accounts[9], {"from": ac["dep"]})
    assert ctr.paymentRecipient() == accounts[9]


def test_minting(contractzz, ac, accounts, setup_merkleTree):
    ct = contractzz[0]
    pp_ctr = contractzz[1]
    merkle_root, merkle_addys, merkle_proofs = setup_merkleTree

    # TESTING powerPassMint
    ct.setMintPhase(0, {"from": ac["dep"]})

    with brownie.reverts("Power Pass Mint not open yet."):
        ct.powerPassMint(
            1, {"from": ac["bob"], "gas_limit": 1000000, "allow_revert": True}
        )

    with brownie.reverts("Powerlist mint not open yet!"):
        ct.powerListMint(
            1, [], {"from": ac["bob"], "gas_limit": 1000000, "allow_revert": True}
        )

    ct.setMintPhase(1, {"from": ac["dep"]})

    pp_price = ct.powerPassHolderPhaseOneConf()[1]
    pp_amount_per = ct.powerPassHolderPhaseOneConf()[0]

    acc_5_pp_bal = pp_ctr.balanceOf(accounts[5])
    acc_5_max_allowed_mint = acc_5_pp_bal * pp_amount_per

    with brownie.reverts("There are no Power Passes in your wallet!"):
        ct.powerPassMint(
            1, {"from": accounts[4], "gas_limit": 1000000, "allow_revert": True}
        )
    with brownie.reverts("You cannot mint that many!"):
        ct.powerPassMint(
            acc_5_max_allowed_mint + 1,
            {"from": accounts[5], "gas_limit": 1000000, "allow_revert": True},
        )
    with brownie.reverts("Wrong amount of ETH sent!"):
        ct.powerPassMint(
            acc_5_max_allowed_mint,
            {
                "from": accounts[5],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": ct.getTotalMintPrice(acc_5_max_allowed_mint - 1, 1),
            },
        )

    ct.powerPassMint(
        acc_5_max_allowed_mint - 8,
        {
            "from": accounts[5],
            "value": ct.getTotalMintPrice(acc_5_max_allowed_mint - 8, 1),
        },
    )
    with brownie.reverts("You cannot mint that many!"):
        ct.powerPassMint(
            9,
            {
                "from": accounts[5],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": ct.getTotalMintPrice(9, 1),
            },
        )

    ct.powerPassMint(
        8,
        {
            "from": accounts[5],
            "value": ct.getTotalMintPrice(8, 1),
        },
    )

    assert ct.balanceOf(accounts[5]) == acc_5_max_allowed_mint
    assert ct.balance() == 100000000000000000000 - accounts[5].balance()
    assert ct.totalSupply() == acc_5_max_allowed_mint

    acc_7_pp_bal = pp_ctr.balanceOf(accounts[7])
    acc_7_max_allowed_mint = acc_7_pp_bal * pp_amount_per

    print(f"Total supply == {ct.totalSupply()}")
    ct.setMintPhase(2, {"from": ac["dep"]})

    ct.powerPassMint(
        acc_7_max_allowed_mint / 2,
        {
            "from": accounts[7],
            "value": ct.getTotalMintPrice(acc_7_max_allowed_mint / 2, 1),
        },
    )
    ct.powerPassMint(
        2,
        {
            "from": accounts[7],
            "value": ct.getTotalMintPrice(2, 1),
        },
    )

    ### TESTING POWER LIST MINT

    power_list_conf = ct.powerListPhaseTwoConf()

    with brownie.reverts("You cannot mint that many!"):
        ct.powerListMint(
            power_list_conf[0] + 1,
            [],
            {"from": ac["bob"], "gas_limit": 1000000, "allow_revert": True},
        )
    with brownie.reverts("Wrong amount of ETH sent!"):
        ct.powerListMint(
            power_list_conf[0],
            [],
            {
                "from": ac["bob"],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": ct.getTotalMintPrice(power_list_conf[0] - 1, 2),
            },
        )
    with brownie.reverts("You are not authorized for pre-sale."):
        ct.powerListMint(
            power_list_conf[0],
            [],
            {
                "from": accounts[9],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": ct.getTotalMintPrice(power_list_conf[0], 2),
            },
        )
    ct.powerListMint(
        power_list_conf[0],
        merkle_proofs[0].split(","),
        {
            "from": accounts[9],
            "gas_limit": 1000000,
            "allow_revert": True,
            "value": ct.getTotalMintPrice(power_list_conf[0], 2),
        },
    )
    with brownie.reverts("You cannot mint that many!"):
        ct.powerListMint(
            1,
            [],
            {"from": accounts[9], "gas_limit": 1000000, "allow_revert": True},
        )

    ct.powerListMint(
        power_list_conf[0] / 2,
        merkle_proofs[1].split(","),
        {
            "from": accounts[8],
            "gas_limit": 1000000,
            "allow_revert": True,
            "value": ct.getTotalMintPrice(power_list_conf[0] / 2, 2),
        },
    )

    # TEST PUblic mint
    with brownie.reverts("Public mint not open yet!"):
        ct.publicMint(
            1, {"from": ac["bob"], "gas_limit": 1000000, "allow_revert": True}
        )
    ct.setMintPhase(3, {"from": ac["dep"]})
    ct.publicMint(
        22,
        {
            "from": accounts[3],
            "gas_limit": 1000000,
            "allow_revert": True,
            "value": ct.getTotalMintPrice(22, 3),
        },
    )
    ct.publicMint(
        2,
        {
            "from": accounts[3],
            "gas_limit": 1000000,
            "allow_revert": True,
            "value": ct.getTotalMintPrice(2, 3),
        },
    )
    with brownie.reverts("Wrong amount of ETH sent!"):
        ct.publicMint(
            7,
            {
                "from": accounts[2],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": ct.getTotalMintPrice(7, 3) - 1,
            },
        )

    ct.setPublicPhaseThreeConf(
        5,
        80000000000000000,
        76000000000000000,
        72000000000000000,
        {"from": ac["dep"]},
    )
    with brownie.reverts("You cannot mint that many!"):
        ct.publicMint(
            7,
            {
                "from": accounts[3],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": ct.getTotalMintPrice(7, 3),
            },
        )
    ct.publicMint(
        4,
        {
            "from": accounts[3],
            "gas_limit": 1000000,
            "allow_revert": True,
            "value": ct.getTotalMintPrice(4, 3),
        },
    )
    with brownie.reverts("You cannot mint that many!"):
        ct.publicMint(
            2,
            {
                "from": accounts[3],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": ct.getTotalMintPrice(2, 3),
            },
        )
    ct.publicMint(
        1,
        {
            "from": accounts[3],
            "gas_limit": 1000000,
            "allow_revert": True,
            "value": ct.getTotalMintPrice(1, 3),
        },
    )


def test_blacklisting(contractzz, ac, accounts):
    ct = contractzz[0]
    pp_ctr = contractzz[1]
    ct.approve(ac["owner"], ct.walletOfOwner(accounts[7])[0], {"from": accounts[7]})
    approvedd = ct.getApproved(ct.walletOfOwner(accounts[7])[0])
    print(approvedd)
    ct.setApprovalForAll(ac["bob"], True, {"from": accounts[7]})
    assert ct.isApprovedForAll(accounts[7], ac["bob"])

    ct.updateBlackListedApprovals([accounts[9]], [True], {"from": ac["dep"]})
    with brownie.reverts("This opperator is blacklisted."):
        ct.approve(
            accounts[9],
            ct.walletOfOwner(accounts[7])[0],
            {"from": accounts[7], "gas_limit": 1000000, "allow_revert": True},
        )
        ct.setApprovalForAll(
            accounts[9],
            True,
            {"from": accounts[7], "gas_limit": 1000000, "allow_revert": True},
        )

    ct.approve(accounts[6], ct.walletOfOwner(accounts[7])[0], {"from": accounts[7]})
    ct.setApprovalForAll(accounts[6], True, {"from": accounts[7]})


def test_pausing_andwithdraw(contractzz, ac, accounts):
    ct = contractzz[0]
    pp_ctr = contractzz[1]

    assert not ct.paused()

    acc_5_tokens = ct.walletOfOwner(accounts[5])
    token_to_send = acc_5_tokens[0]
    token_2_to_send = acc_5_tokens[1]
    token_3_to_send = acc_5_tokens[2]
    token_4_to_send = acc_5_tokens[3]

    with brownie.reverts():
        ct.safeTransferFrom(
            accounts[5],
            accounts[6],
            token_to_send,
            {"from": accounts[6], "gas_limit": 1000000, "allow_revert": True},
        )
        ct.safeTransferFrom(
            accounts[5],
            accounts[6],
            token_2_to_send,
            {"from": accounts[6], "gas_limit": 1000000, "allow_revert": True},
        )
        ct.safeTransferFrom(
            accounts[5],
            accounts[6],
            token_3_to_send,
            {"from": accounts[6], "gas_limit": 1000000, "allow_revert": True},
        )
    ct.safeTransferFrom(
        accounts[5],
        accounts[6],
        token_to_send,
        {"from": accounts[5], "gas_limit": 1000000, "allow_revert": True},
    )
    ct.approve(
        accounts[6],
        token_2_to_send,
        {"from": accounts[5], "gas_limit": 1000000, "allow_revert": True},
    )
    ct.safeTransferFrom(
        accounts[5],
        accounts[6],
        token_2_to_send,
        {"from": accounts[6], "gas_limit": 1000000, "allow_revert": True},
    )
    ct.setApprovalForAll(
        accounts[6],
        True,
        {"from": accounts[5], "gas_limit": 1000000, "allow_revert": True},
    )
    ct.safeTransferFrom(
        accounts[5],
        accounts[6],
        token_3_to_send,
        {"from": accounts[6], "gas_limit": 1000000, "allow_revert": True},
    )
    assert ct.ownerOf(token_to_send) == accounts[6]
    assert ct.ownerOf(token_2_to_send) == accounts[6]
    assert ct.ownerOf(token_3_to_send) == accounts[6]

    ct.togglePaused(True, {"from": ac["dep"]})

    with brownie.reverts("Pausable: paused"):
        ct.safeTransferFrom(
            accounts[5],
            accounts[6],
            token_3_to_send,
            {"from": accounts[6], "gas_limit": 1000000, "allow_revert": True},
        )
    ct.togglePaused(False, {"from": ac["dep"]})
    assert ct.ownerOf(token_4_to_send) == accounts[5]
    ct.safeTransferFrom(
        accounts[5],
        accounts[6],
        token_4_to_send,
        {"from": accounts[6], "gas_limit": 1000000, "allow_revert": True},
    )
    assert ct.ownerOf(token_4_to_send) == accounts[6]

    with brownie.reverts("Invalid delegate"):
        ct.setPaymentRecipient(
            ac["bob"], {"from": ac["bob"], "gas_limit": 1000000, "allow_revert": True}
        )

    ct.setPaymentRecipient(ac["bob"], {"from": ac["dep"]})

    bal = ac["bob"].balance()
    bal2 = ct.balance()
    print(f"bal = {bal}")
    print(f"ba2l = {ct.balance()}")

    ct.withdraw({"from": ac["dep"]})
    assert ac["bob"].balance() == bal + bal2
    assert ct.balance() == 0
    """
    ct.publicMint(3, {"from": accounts[7], "value": 60000000000000000})
    with brownie.reverts("You have minted max during public phase."):
        ct.publicMint(
            1,
            {
                "from": accounts[7],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 25000000000000000,
            },
        )

    with brownie.reverts("Can only set a lower size."):
        ct.setReducedMaxSupply(
            10001, {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True}
        )

    with brownie.reverts("New supply lower than current totalSupply"):
        ct.setReducedMaxSupply(
            ct.totalSupply() - 1,
            {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True},
        )

    ct.setReducedMaxSupply(
        ct.totalSupply(),
        {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True},
    )

    ct.tokenURI(ct.totalSupply())
    with brownie.reverts():
        ct.tokenURI(
            ct.totalSupply() + 1,
            {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True},
        )

    with brownie.reverts("Max supply reached!"):
        ct.publicMint(
            1,
            {
                "from": accounts[8],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 25000000000000000,
            },
        )

    pre_bal = ct.balance()
    ac["alex"].transfer(ct.address, "10 ether")
    print(ct.balance())
    assert ct.balance() == pre_bal + "10 ether"

    with brownie.reverts("Invalid delegate"):
        ct.setPaymentRecipient(
            ac["bob"], {"from": ac["alex"], "gas_limit": 1000000, "allow_revert": True}
        )

    ct.setPaymentRecipient(ac["bob"], {"from": ac["dep"]})

    bal = ac["bob"].balance()
    bal2 = ct.balance()
    print(f"bal = {bal}")
    print(f"ba2l = {ct.balance()}")

    ct.withdraw({"from": ac["dep"]})
    assert ac["bob"].balance() == bal + bal2
    assert ct.balance() == 0


def test_blacklisting(ct, ac, accounts):

    assert False
    ct.approve(ac["owner"], 1, {"from": accounts[7]})
    approvedd = ct.getApproved(1)
    print(approvedd)
    ct.setApprovalForAll(ac["bob"], True, {"from": accounts[7]})
    assert ct.isApprovedForAll(accounts[7], ac["bob"])

    ct.updateBlackListedApprovals([accounts[9]], [True], {"from": ac["dep"]})
    with brownie.reverts("This opperator is blacklisted."):
        ct.approve(
            accounts[9],
            2,
            {"from": accounts[7], "gas_limit": 1000000, "allow_revert": True},
        )
        ct.setApprovalForAll(
            [accounts[9]],
            [True],
            {"from": accounts[7], "gas_limit": 1000000, "allow_revert": True},
        )

    ct.approve(accounts[6], 3, {"from": accounts[7]})
    ct.setApprovalForAll(accounts[6], True, {"from": accounts[7]})

    assert False
"""
