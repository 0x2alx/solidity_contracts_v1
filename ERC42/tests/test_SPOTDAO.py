import brownie, pytest, pathlib, json, random, logging, sha3, time
from brownie import exceptions
from brownie.network.gas.strategies import GasNowStrategy
from eip712_structs import make_domain
from coincurve import PrivateKey, PublicKey
from eip712_structs import EIP712Struct, Address, String, Uint, Boolean, Bytes
from eth_utils import big_endian_to_int

LOGGER = logging.getLogger(__name__)


class Master_Approval(EIP712Struct):
    addy = Address()
    price = Uint(256)
    valid_until_timestamp = Uint(256)
    id = Uint(256)
    max_per_wallet = Uint(256)
    qty = Uint(256)
    sig_nonce = Uint(256)


class Master_Approval_Burn(EIP712Struct):
    addy = Address()
    valid_until_timestamp = Uint(256)
    token_id_to_mint = Uint(256)
    token_id_to_burn = Uint(256)
    nb_tokens_to_burn = Uint(256)
    nb_tokens_to_mint = Uint(256)
    is_locked_for_mint = Uint(256)
    sig_nonce = Uint(256)


def test_premint_misc(fn_isolation, SPOTLIGHTDAO, ac, accounts):
    ct = ac["dep"].deploy(SPOTLIGHTDAO)
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

    assert not ct.tokensOpenToPublic(1)
    assert ct.tokensOpenToPublic(2)
    assert ct.isSoulBoundToken(1)
    # Testing blacklisting stuff

    assert not ct.blacklisted_approvals(ac["owner"])
    ct.updateBlackListedApprovals([ac["owner"]], [True], {"from": ac["dep"]})
    assert ct.blacklisted_approvals(ac["owner"])

    assert not ct.paused()
    ct.pause({"from": ac["dep"]})
    assert ct.paused()
    ct.unpause({"from": ac["dep"]})

    ct.adminMint(ac["owner"], 1, 5, 0x0, {"from": ac["dep"]})
    ct.adminMint(ac["owner"], 2, 5, 0x0, {"from": ac["dep"]})
    ct.adminMint(ac["owner"], 3, 5, 0x0, {"from": ac["dep"]})

    assert ct.balance() == 0
    print(f"contract balance = {ct.balance()} / {ac['owner'].balance()}")
    ac["owner"].transfer(ct.address, 100000000000000000)
    print(ct.balance())
    assert ct.balance() == 100000000000000000

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

    # TEST PUBLIC MINT

    with brownie.reverts("Public mint not open"):
        ct.publicMint(
            3,
            2,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 10000000000000000 * 3,
            },
        )

    ct.configurePublicMint(10000000000000000, True, {"from": ac["dep"]})
    with brownie.reverts("Wront amount of ETH sent"):
        ct.publicMint(
            3,
            2,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 10000000000000000 * 3 - 1,
            },
        )
    with brownie.reverts("Token not open to public mint."):
        ct.publicMint(
            3,
            1,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 10000000000000000 * 3,
            },
        )
    with brownie.reverts("Token not open to public mint."):
        ct.publicMint(
            3,
            3,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 10000000000000000 * 3,
            },
        )
    balof = ct.balanceOf(accounts[0], 2)
    ct.publicMint(
        3,
        2,
        {
            "from": accounts[0],
            "gas_limit": 1000000,
            "allow_revert": True,
            "value": 10000000000000000 * 3,
        },
    )
    assert balof + 3 == ct.balanceOf(accounts[0], 2)

    # TEST SIGNED MINT

    md = make_domain(
        name="SPOTLIGHTDAO",
        version="1",
        chainId=1,
        verifyingContract=ct.address,
    )

    keccak_hash = lambda x: sha3.keccak_256(x).digest()
    pk_master_signer = PrivateKey.from_hex(ac["owner"].private_key[2:])
    mast_tstamp = int(time.time())
    sig_n = random.randint(42, 42200)
    """
    m_apobj = Master_Approval(
        addy=accounts[0].address,
        qty=1,
        price=10000000000000000,
        id=1,
        tstamp=mast_tstamp,
        validity=10,
        unique_sig=False,
    )
    m_ap = (accounts[0].address, 1, 10000000000000000, 1, mast_tstamp, 10, False)
    """

    m_apobj = Master_Approval(
        addy=accounts[0].address,
        price=10000000000000000,
        valid_until_timestamp=mast_tstamp + 10,
        id=1,
        max_per_wallet=0,
        qty=1,
        sig_nonce=sig_n,
    )
    m_ap = (
        accounts[0].address,
        10000000000000000,
        mast_tstamp + 10,
        1,
        0,
        1,
        sig_n,
    )
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
        ct.masterSigMint(
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
        ct.masterSigMint(
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
        ct.masterSigMint(
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
    with brownie.reverts("Signature Expired!"):
        ct.masterSigMint(
            m_ap,
            master_final_sig,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 10000000000000000,
            },
        )
    mast_tstamp = int(time.time())
    """
    m_apobj = Master_Approval(
        addy=accounts[0].address,
        qty=1,
        price=10000000000000000,
        id=1,
        tstamp=mast_tstamp,
        validity=4242,
        unique_sig=True,
    )
    m_ap = (accounts[0].address, 1, 10000000000000000, 1, mast_tstamp, 4242, True)
    """
    m_apobj = Master_Approval(
        addy=accounts[0].address,
        price=10000000000000000,
        valid_until_timestamp=mast_tstamp + 100000,
        id=1,
        max_per_wallet=0,
        qty=1,
        sig_nonce=sig_n,
    )
    m_ap = (
        accounts[0].address,
        10000000000000000,
        mast_tstamp + 100000,
        1,
        0,
        1,
        sig_n,
    )
    master_signature = pk_master_signer.sign_recoverable(
        m_apobj.signable_bytes(md), hasher=keccak_hash
    )
    mr = big_endian_to_int(master_signature[0:32])
    ms = big_endian_to_int(master_signature[32:64])
    mv = master_signature[64] + 27
    master_final_sig = (
        mr.to_bytes(32, "big") + ms.to_bytes(32, "big") + mv.to_bytes(1, "big")
    )

    ct.masterSigMint(
        m_ap,
        master_final_sig,
        {
            "from": accounts[0],
            "gas_limit": 1000000,
            "allow_revert": True,
            "value": 10000000000000000,
        },
    )
    with brownie.reverts("Sig already used!"):
        ct.masterSigMint(
            m_ap,
            master_final_sig,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 10000000000000000,
            },
        )

    acc1_bal = ct.balanceOf(accounts[1], 2)
    ct.safeTransferFrom(
        accounts[0].address, accounts[1].address, 2, 1, 0x0, {"from": accounts[0]}
    )
    assert acc1_bal + 1 == ct.balanceOf(accounts[1], 2)
    with brownie.reverts("Soul Bound token!"):
        ct.safeTransferFrom(
            accounts[0].address, accounts[1].address, 1, 1, 0x0, {"from": accounts[0]}
        )

    ct.adminMint(accounts[0], 7, 10, 0x0, {"from": ac["dep"]})
    ct.adminMint(accounts[0], 6, 10, 0x0, {"from": ac["dep"]})
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

    # TEST MASTER BURN

    sb_bal = ct.balanceOf(accounts[0], 1)

    with brownie.reverts():
        ct.masterBurn(accounts[0].address, 1, 1, {"from": accounts[0]})
    with brownie.reverts("Only soul bound tokens can be master burned"):
        ct.masterBurn(accounts[0].address, 2, 1, {"from": ac["dep"]})
    ct.masterBurn(accounts[0].address, 1, 1, {"from": ac["dep"]})
    assert sb_bal - 1 == ct.balanceOf(accounts[0], 1)

    # TEST BURN TO MINT
    sig_nonce = random.randint(42, 4222)
    m_abobj = Master_Approval_Burn(
        addy=accounts[0].address,
        valid_until_timestamp=mast_tstamp - 1,
        token_id_to_mint=21,
        token_id_to_burn=2,
        nb_tokens_to_burn=3,
        nb_tokens_to_mint=1,
        is_locked_for_mint=42,
        sig_nonce=sig_nonce,
    )
    m_ab = (accounts[0].address, mast_tstamp - 1, 21, 2, 3, 1, 42, sig_nonce)
    master_signature_b = pk_master_signer.sign_recoverable(
        m_abobj.signable_bytes(md), hasher=keccak_hash
    )
    mrb = big_endian_to_int(master_signature_b[0:32])
    msb = big_endian_to_int(master_signature_b[32:64])
    mvb = master_signature_b[64] + 27
    master_final_sig_b = (
        mrb.to_bytes(32, "big") + msb.to_bytes(32, "big") + mvb.to_bytes(1, "big")
    )
    ct.setMasterSigConf(ac["dep"].address, {"from": ac["dep"]})
    with brownie.reverts("Invalid master sig!"):
        ct.masterSigBurnToClaim(
            m_ab,
            master_final_sig_b,
            {
                "from": accounts[1],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 0,
            },
        )
    ct.setMasterSigConf(ac["owner"].address, {"from": ac["dep"]})
    print(f"{ac['owner'].address=}")
    print(f"{ct.get_signer_b(m_ab,master_final_sig_b)=}")
    print(f"{ct.get_signer(m_ap,master_final_sig)=}")
    print(f"{ct.get_master_signer({'from':ac['dep']})=}")
    with brownie.reverts("Not approved minter!"):
        ct.masterSigBurnToClaim(
            m_ab,
            master_final_sig_b,
            {
                "from": accounts[1],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 0,
            },
        )
    with brownie.reverts("Signature Expired!"):
        ct.masterSigBurnToClaim(
            m_ab,
            master_final_sig_b,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 0,
            },
        )
    m_abobj = Master_Approval_Burn(
        addy=accounts[0].address,
        valid_until_timestamp=mast_tstamp + 100000,
        token_id_to_mint=21,
        token_id_to_burn=2,
        nb_tokens_to_burn=3333,
        nb_tokens_to_mint=1,
        is_locked_for_mint=42,
        sig_nonce=sig_nonce,
    )
    m_ab = (
        accounts[0].address,
        mast_tstamp + 100000,
        21,
        2,
        3333,
        1,
        42,
        sig_nonce,
    )

    master_signature_b = pk_master_signer.sign_recoverable(
        m_abobj.signable_bytes(md), hasher=keccak_hash
    )
    mrb = big_endian_to_int(master_signature_b[0:32])
    msb = big_endian_to_int(master_signature_b[32:64])
    mvb = master_signature_b[64] + 27
    master_final_sig_b = (
        mrb.to_bytes(32, "big") + msb.to_bytes(32, "big") + mvb.to_bytes(1, "big")
    )
    with brownie.reverts("Not enough tokens to burn!"):
        ct.masterSigBurnToClaim(
            m_ab,
            master_final_sig_b,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 0,
            },
        )
    m_abobj = Master_Approval_Burn(
        addy=accounts[0].address,
        valid_until_timestamp=mast_tstamp + 100000,
        token_id_to_mint=21,
        token_id_to_burn=2,
        nb_tokens_to_burn=1,
        nb_tokens_to_mint=1,
        is_locked_for_mint=42,
        sig_nonce=sig_nonce,
    )
    m_ab = (
        accounts[0].address,
        mast_tstamp + 100000,
        21,
        2,
        1,
        1,
        42,
        sig_nonce,
    )
    master_signature_b = pk_master_signer.sign_recoverable(
        m_abobj.signable_bytes(md), hasher=keccak_hash
    )
    mrb = big_endian_to_int(master_signature_b[0:32])
    msb = big_endian_to_int(master_signature_b[32:64])
    mvb = master_signature_b[64] + 27
    master_final_sig_b = (
        mrb.to_bytes(32, "big") + msb.to_bytes(32, "big") + mvb.to_bytes(1, "big")
    )
    pre_bal_2 = ct.balanceOf(accounts[0].address, 2)
    pre_bal_21 = ct.balanceOf(accounts[0].address, 21)
    assert pre_bal_21 == 0
    ct.masterSigBurnToClaim(
        m_ab,
        master_final_sig_b,
        {
            "from": accounts[0],
            "gas_limit": 1000000,
            "allow_revert": True,
            "value": 0,
        },
    )
    assert ct.balanceOf(accounts[0].address, 21) == 1
    assert ct.balanceOf(accounts[0].address, 2) == pre_bal_2 - 1
    with brownie.reverts("Sig already used!"):
        ct.masterSigBurnToClaim(
            m_ab,
            master_final_sig_b,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 0,
            },
        )
    sig_nonce = random.randint(42, 42222)
    m_abobj = Master_Approval_Burn(
        addy=accounts[0].address,
        valid_until_timestamp=mast_tstamp + 100000,
        token_id_to_mint=21,
        token_id_to_burn=2,
        nb_tokens_to_burn=1,
        nb_tokens_to_mint=1,
        is_locked_for_mint=42,
        sig_nonce=sig_nonce,
    )
    m_ab = (
        accounts[0].address,
        mast_tstamp + 100000,
        21,
        2,
        1,
        1,
        42,
        sig_nonce,
    )
    master_signature_b = pk_master_signer.sign_recoverable(
        m_abobj.signable_bytes(md), hasher=keccak_hash
    )
    mrb = big_endian_to_int(master_signature_b[0:32])
    msb = big_endian_to_int(master_signature_b[32:64])
    mvb = master_signature_b[64] + 27
    master_final_sig_b = (
        mrb.to_bytes(32, "big") + msb.to_bytes(32, "big") + mvb.to_bytes(1, "big")
    )
    with brownie.reverts("This token is not open for mint!"):
        ct.masterSigBurnToClaim(
            m_ab,
            master_final_sig_b,
            {
                "from": accounts[0],
                "gas_limit": 1000000,
                "allow_revert": True,
                "value": 0,
            },
        )
