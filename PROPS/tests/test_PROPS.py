import brownie, pytest, pathlib, json, time, logging, sha3
from eip712_structs import make_domain
from coincurve import PrivateKey, PublicKey
from eip712_structs import EIP712Struct, Address, String, Uint, Boolean
from eth_utils import big_endian_to_int


class Master_Approval(EIP712Struct):
    approved_address = Address()
    master_sig_timestamp = Uint(256)


LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="module", autouse=True)
def contractzz(module_isolation, PROPS, ac, accounts):
    ctr = ac["dep"].deploy(PROPS)
    assert ctr.owner() == ac["dep"]
    print(f"PROPS contract = {ctr}")
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

    with brownie.reverts("Invalid delegate"):
        ctr.setPaymentRecipient(accounts[9], {"from": ac["bob"]})
    ctr.setPaymentRecipient(accounts[9], {"from": ac["owner"]})
    assert ctr.payment_recipient() == accounts[9]


def test_minting(contractzz, ac, accounts):
    ct = contractzz

    md = make_domain(
        name="PROPS",
        version="1",
        chainId=1,
        verifyingContract=ct.address,
    )

    keccak_hash = lambda x: sha3.keccak_256(x).digest()
    pk_master_signer = PrivateKey.from_hex(ac["owner"].private_key[2:])
    mast_tstamp = int(time.time())
    m_ap = Master_Approval(
        approved_address=accounts[0].address,
        master_sig_timestamp=mast_tstamp,
    )
    master_signature = pk_master_signer.sign_recoverable(
        m_ap.signable_bytes(md), hasher=keccak_hash
    )
    mr = big_endian_to_int(master_signature[0:32])
    ms = big_endian_to_int(master_signature[32:64])
    mv = master_signature[64] + 27
    master_final_sig = (
        mr.to_bytes(32, "big") + ms.to_bytes(32, "big") + mv.to_bytes(1, "big")
    )

    with brownie.reverts("Mint not open yet!"):
        ct.propsMint(
            (
                accounts[0].address,
                mast_tstamp,
            ),
            master_final_sig,
            {"from": accounts[0], "gas_limit": 1000000, "allow_revert": True},
        )
    ct.toggleMint(True, {"from": ac["dep"]})
    ct.setMasterSigConf(ac["owner"].address, 300, {"from": ac["owner"]})
    ct.setMintPrice(4200000000000000, {"from": ac["owner"]})
    ct.propsMint(
        (
            accounts[0].address,
            mast_tstamp,
        ),
        master_final_sig,
        {
            "from": accounts[0],
            "gas_limit": 1000000,
            "allow_revert": True,
            "value": ct.mint_price(),
        },
    )

    with brownie.reverts("Invalid amount of ETH"):
        ct.propsMint(
            (
                accounts[0].address,
                mast_tstamp,
            ),
            master_final_sig,
            {
                "from": accounts[5],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 0,
            },
        )
    assert ct.balanceOf(accounts[0]) == 1

    assert ct.balance() == ct.mint_price()
    assert ct.balanceOf(accounts[0]) == 1

    assert ct.totalSupply() == 1

    for i in range(1, 6):
        mast_tstamp = int(time.time())
        m_ap = Master_Approval(
            approved_address=accounts[i].address, master_sig_timestamp=mast_tstamp
        )
        master_signature = pk_master_signer.sign_recoverable(
            m_ap.signable_bytes(md), hasher=keccak_hash
        )
        mr = big_endian_to_int(master_signature[0:32])
        ms = big_endian_to_int(master_signature[32:64])
        mv = master_signature[64] + 27
        master_final_sig = (
            mr.to_bytes(32, "big") + ms.to_bytes(32, "big") + mv.to_bytes(1, "big")
        )
        print(f"{master_final_sig=}")
        print(f"{master_final_sig.hex()=}")
        print(f"{type(master_final_sig.hex())=}")
        print(f"{type(master_final_sig)=}")
        ct.propsMint(
            (
                accounts[i].address,
                mast_tstamp,
            ),
            master_final_sig.hex(),
            {
                "from": accounts[i],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": ct.mint_price(),
            },
        )


def test_pausing_andwithdraw(contractzz, ac, accounts):
    ct = contractzz

    acc_0_tokens = ct.walletOfOwner(accounts[0])

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

    with brownie.reverts("ERC721: caller is not token owner or approved"):
        ct.burn(
            1,
            {"from": accounts[9], "gas_limit": 1000000, "allow_revert": True},
        )
    assert ct.ownerOf(1) == accounts[6]
    ct.burn(
        1,
        {"from": accounts[6], "gas_limit": 1000000, "allow_revert": True},
    )
    with brownie.reverts("ERC721: owner query for nonexistent token"):
        assert ct.ownerOf(1) == "0x0000000000000000000000000000000000000000"
    assert ct.ownerOf(2) == accounts[1]
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

    ct.ghostyMint(1, [accounts[5]])
    assert ct.balanceOf(accounts[5]) == 2
    ct.ghostyMint(3, [accounts[5], accounts[5], accounts[4]])
    assert ct.balanceOf(accounts[5]) == 4
    assert ct.balanceOf(accounts[4]) == 2

    assert ct.balance() == 0
    assert accounts[9].balance() == acc9_bal + ctr_bal
