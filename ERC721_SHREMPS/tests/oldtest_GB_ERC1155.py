import brownie, pytest, pathlib, json, random, logging, sha3, time
from brownie import exceptions
from brownie.network.gas.strategies import GasNowStrategy
from eip712_structs import make_domain
from coincurve import PrivateKey, PublicKey
from eip712_structs import EIP712Struct, Address, String, Uint, Boolean
from eth_utils import big_endian_to_int

LOGGER = logging.getLogger(__name__)


class Master_Approval(EIP712Struct):
    addy = Address()
    qty = Uint(256)
    price = Uint(256)
    id = Uint(256)
    tstamp = Uint(256)
    validity = Uint(256)
    unique_sig = Boolean()


def test_premint_misc(fn_isolation, GHOSTYBOTZ, ac, accounts):
    ct = ac["dep"].deploy(GHOSTYBOTZ)
    assert ct.owner() == ac["dep"]
    print(f"Onwer == {ct.owner()}")

    ct.transferOwnership(ac["owner"], {"from": ac["dep"]})
    assert ct.owner() == ac["owner"]
    ct.transferOwnership(ac["dep"], {"from": ac["owner"]})

    print(f"Onwer == {ct.owner()}")
    print(ct)
    print(f"\tContract deployed by {ac['dep']} at {ct.address}")

    assert ct.hasRole(
        0x0000000000000000000000000000000000000000000000000000000000000000, ac["dep"]
    )  # ADMIN ROLE
    assert ct.hasRole(
        0x9F2DF0FED2C77648DE5860A4CC508CD0818C85B8B8A1AB4CEEEF8D981C8956A6, ac["dep"]
    )  # MINTER ROLE
    assert ct.hasRole(
        0x65D7A28E3265B37A6474929F336521B332C1681B933F6CB9F3376673440D862A, ac["dep"]
    )  # PAUSER ROLE

    print(ct)

    ct.setBaseSuffixURI("/test/", ".bla", "test2", {"from": ac["dep"]})

    assert ct.uri(1) == "/test/1.bla"

    tok1 = ct.tokensLockedMinting(5, {"from": ac["bob"]})
    tok3 = ct.tokensLockedMinting(4, {"from": ac["bob"]})

    print(f" token locked = {tok1} / {tok3}")
    ct.lockTokenMinting(4, {"from": ac["dep"]})
    tok4 = ct.tokensLockedMinting(5, {"from": ac["bob"]})
    tok2 = ct.tokensLockedMinting(4, {"from": ac["bob"]})

    print(f" token locked = {tok2} / {tok4}")
    # Testing blacklisting stuff

    assert not ct.blacklisted_approvals(ac["owner"])
    ct.updateBlackListedApprovals([ac["owner"]], [True], {"from": ac["dep"]})
    assert ct.blacklisted_approvals(ac["owner"])

    # Testing non reselable tokens
    assert not ct.non_resalable_tokens(1)
    ct.updateNonReselableTokens([1], [True], {"from": ac["dep"]})
    assert ct.non_resalable_tokens(1)

    assert not ct.paused()
    ct.pause({"from": ac["dep"]})
    assert ct.paused()
    ct.unpause({"from": ac["dep"]})

    ct.ghostyMint(ac["owner"], 1, 5, 0x0, {"from": ac["dep"]})
    ct.ghostyMint(ac["owner"], 2, 5, 0x0, {"from": ac["dep"]})
    ct.ghostyMint(ac["owner"], 3, 5, 0x0, {"from": ac["dep"]})
    with brownie.reverts("This token is locked for minting."):
        ct.ghostyMint(
            ac["owner"],
            4,
            5,
            0x0,
            {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True},
        )

    ct.lockTokenMinting(2, {"from": ac["dep"]})
    with pytest.raises(exceptions.VirtualMachineError):
        ct.ghostyMint(
            ac["owner"],
            2,
            5,
            0x0,
            {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True},
        )

    assert ct.balance() == 0
    print(f"contract balance = {ct.balance()} / {ac['owner'].balance()}")
    ac["owner"].transfer(ct.address, 10000000000000000000)
    print(ct.balance())
    assert ct.balance() == 10000000000000000000

    with brownie.reverts():
        ct.setPaymentRecipient(
            ac["owner"],
            {"from": ac["owner"], "gas_limit": 1000000, "allow_revert": True},
        )

    ct.setPaymentRecipient(ac["bob"], {"from": ac["dep"]})

    bal = ac["bob"].balance()
    print(f"contract balance = {ct.balance()} / bob ==== {ac['bob'].balance()}")

    ct.withdraw({"from": ac["owner"]})
    print(f"contract balance = {ct.balance()} / bob == {ac['bob'].balance()}")

    # assert ac["bob"].balance() == bal + 10000000000000000000
    assert ct.balance() == 0

    with brownie.reverts("This opperator is blacklisted."):
        ct.setApprovalForAll(
            ac["owner"],
            True,
            {"from": ac["dep"], "gas_limit": 1000000, "allow_revert": True},
        )

    ct.setApprovalForAll(ac["bob"], True, {"from": ac["owner"]})

    assert not ct.isApprovedForAll(ac["dep"], ac["owner"], {"from": ac["dep"]})
    assert ct.isApprovedForAll(ac["owner"], ac["bob"], {"from": ac["dep"]})

    with brownie.reverts():
        ct.safeTransferFrom(
            ac["dep"],
            ac["owner"],
            1,
            1,
            0x0,
            {"from": ac["bob"], "gas_limit": 1000000, "allow_revert": True},
        )
    ct.safeTransferFrom(ac["owner"], ac["dep"], 2, 1, 0x0, {"from": ac["bob"]})

    md = make_domain(
        name="GHOSTYBOTZ",
        version="1",
        chainId=1,
        verifyingContract=ct.address,
    )

    keccak_hash = lambda x: sha3.keccak_256(x).digest()
    pk_master_signer = PrivateKey.from_hex(ac["owner"].private_key[2:])
    mast_tstamp = int(time.time())
    m_apobj = Master_Approval(
        addy=accounts[0].address,
        qty=1,
        price=4200000000000000,
        id=1,
        tstamp=mast_tstamp,
        validity=10,
        unique_sig=False,
    )
    m_ap = (accounts[0].address, 1, 4200000000000000, 1, mast_tstamp, 10, False)
    master_signature = pk_master_signer.sign_recoverable(
        m_apobj.signable_bytes(md), hasher=keccak_hash
    )
    mr = big_endian_to_int(master_signature[0:32])
    ms = big_endian_to_int(master_signature[32:64])
    mv = master_signature[64] + 27
    master_final_sig = (
        mr.to_bytes(32, "big") + ms.to_bytes(32, "big") + mv.to_bytes(1, "big")
    )
    ct.setMasterSigConf(ac["dep"].address, {"from": ac["dep"]})
    with brownie.reverts("Invalid master sig!"):
        ct.signedMint(
            m_ap,
            master_final_sig,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 0,
            },
        )
    ct.setMasterSigConf(ac["owner"].address, {"from": ac["dep"]})
    with brownie.reverts("Not approved minter!"):
        ct.signedMint(
            m_ap,
            master_final_sig,
            {
                "from": accounts[2],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 0,
            },
        )

    with brownie.reverts("Invalid amount of ETH sent!"):
        ct.signedMint(
            m_ap,
            master_final_sig,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 0,
            },
        )
    time.sleep(10)
    with brownie.reverts("Master sig has expired!"):
        ct.signedMint(
            m_ap,
            master_final_sig,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 4200000000000000,
            },
        )
    mast_tstamp = int(time.time())
    m_apobj = Master_Approval(
        addy=accounts[0].address,
        qty=1,
        price=4200000000000000,
        id=1,
        tstamp=mast_tstamp,
        validity=4242,
        unique_sig=True,
    )
    m_ap = (accounts[0].address, 1, 4200000000000000, 1, mast_tstamp, 4242, True)
    master_signature = pk_master_signer.sign_recoverable(
        m_apobj.signable_bytes(md), hasher=keccak_hash
    )
    mr = big_endian_to_int(master_signature[0:32])
    ms = big_endian_to_int(master_signature[32:64])
    mv = master_signature[64] + 27
    master_final_sig = (
        mr.to_bytes(32, "big") + ms.to_bytes(32, "big") + mv.to_bytes(1, "big")
    )

    ct.signedMint(
        m_ap,
        master_final_sig,
        {
            "from": accounts[0],
            "gas_limit": 1000000,
            "allow_revert": True,
            "value": 4200000000000000,
        },
    )

    ct.lockTokenMinting(
        1,
        {
            "from": ac["dep"],
            "gas_limit": 1000000,
            "allow_revert": True,
            "value": 0,
        },
    )
    with brownie.reverts("This token is locked for minting."):
        ct.signedMint(
            m_ap,
            master_final_sig,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 4200000000000000,
            },
        )

    with brownie.reverts("Public mint not open"):
        ct.publicMint(
            3,
            5,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 4200000000000000 * 3,
            },
        )

    ct.configurePublicMint(4200000000000000, True, {"from": ac["dep"]})
    with brownie.reverts("Wront amount of ETH sent"):
        ct.publicMint(
            3,
            5,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 4200000000000000 * 3 - 1,
            },
        )
    balof = ct.balanceOf(accounts[0], 5)
    ct.publicMint(
        3,
        5,
        {
            "from": accounts[0],
            "gas_limit": 1000000,
            "allow_revert": True,
            "value": 4200000000000000 * 3,
        },
    )
    assert ct.balanceOf(accounts[0], 5) == balof + 3
    print(f"{ct.balanceOf(accounts[0], 6)=}")
    ct.ghostyMint(accounts[0].address, 6, 30, 0x0, {"from": ac["dep"]})
    ct.ghostyMint(accounts[0].address, 7, 30, 0x0, {"from": ac["dep"]})
    print(f"{(acc1_bal := ct.balanceOf(accounts[1], 6))=}")

    assert ct.balanceOf(accounts[0].address, 6) == 30
    assert ct.balanceOf(accounts[0].address, 7) == 30
    ct.safeTransferFrom(
        accounts[0].address, accounts[1].address, 6, 1, 0x0, {"from": accounts[0]}
    )
    assert acc1_bal + 1 == ct.balanceOf(accounts[1], 6)
    ct.setSoulBoundToken(6, True, {"from": ac["dep"]})
    with brownie.reverts("Soul Bound token!"):
        ct.safeTransferFrom(
            accounts[0].address, accounts[1].address, 6, 1, 0x0, {"from": accounts[0]}
        )
    ct.ghostyMint(accounts[1].address, 6, 2, 0x0, {"from": ac["dep"]})
    assert acc1_bal + 3 == ct.balanceOf(accounts[1], 6)
    acc1_bal = ct.balanceOf(accounts[1], 6)
    with brownie.reverts("Soul Bound token!"):
        ct.safeBatchTransferFrom(
            accounts[0].address,
            accounts[1].address,
            [6],
            [5],
            0x0,
            {"from": accounts[0]},
        )
    assert acc1_bal == ct.balanceOf(accounts[1], 6)
    acc1_bal2 = ct.balanceOf(accounts[1], 7)
    ct.safeBatchTransferFrom(
        accounts[0].address, accounts[1].address, [7], [5], 0x0, {"from": accounts[0]}
    )
    assert acc1_bal2 + 5 == ct.balanceOf(accounts[1], 7)
    ct.setSoulBoundToken(6, False, {"from": ac["dep"]})
    acc1_bal = ct.balanceOf(accounts[1], 6)
    ct.safeBatchTransferFrom(
        accounts[0].address, accounts[1].address, [6], [5], 0x0, {"from": accounts[0]}
    )
    assert acc1_bal + 5 == ct.balanceOf(accounts[1], 6)
