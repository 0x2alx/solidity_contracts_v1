import brownie, pytest, pathlib, json, random, logging, sha3, time
from brownie import exceptions
from brownie.network.gas.strategies import GasNowStrategy
from eip712_structs import make_domain
from coincurve import PrivateKey, PublicKey
from eip712_structs import EIP712Struct, Address, String, Uint, Boolean, Bytes, Array
from eth_utils import big_endian_to_int

LOGGER = logging.getLogger(__name__)


class WhitelistMintParams(EIP712Struct):
    addy = Address()
    valid_until_timestamp = Uint(256)
    ids = Array(Uint(256))
    qtys = Array(Uint(256))
    paid_ids = Array(Uint(256))
    paid_qtys = Array(Uint(256))
    sig_nonce = Uint(256)

class WhitelistMintParams2(EIP712Struct):
    addy = Address()
    valid_until_timestamp = Uint(256)
    ids = Uint(256)
    qtys = Uint(256)
    paid_ids = Uint(256)
    paid_qtys = Uint(256)
    sig_nonce = Uint(256)

def test_premint_misc(fn_isolation, PacksT, ac, accounts):
    ct = ac["dep"].deploy(PacksT)
    assert ct.owner() == ac["dep"]
    print(f"Onwer == {ct.owner()}")
    ct.transferOwnership(ac["owner"], {"from": ac["dep"]})
    assert ct.owner() == ac["owner"]
    ct.transferOwnership(ac["dep"], {"from": ac["owner"]})

    print(f"Onwer == {ct.owner()}")

    md = make_domain(
        name="ShrempPacks",
        version="1",
        chainId=1,
        verifyingContract=ct.address,
    )

    keccak_hash = lambda x: sha3.keccak_256(x).digest()
    pk_master_signer = PrivateKey.from_hex(ac["owner"].private_key[2:])
    mast_tstamp = int(time.time())
    sig_n = random.randint(42, 42200)

    m_apobj = WhitelistMintParams(
        addy=accounts[0].address,
        valid_until_timestamp=mast_tstamp + 1000,
        ids=[1,2,3],
        qtys=[1,1,1],
        paid_ids=[1,2,3],
        paid_qtys=[2,2,2],        
        sig_nonce=sig_n,
    )
    m_ap = (
        accounts[0].address,
        mast_tstamp + 1000,
        [1,2,3],
        [1,1,1],
        [1,2,3],
        [2,2,2],
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
    ct.setSignerAddress(ac["owner"].address, {"from": ac["dep"]})
    print(f"{ac['owner'].address=}")
    print(f"{ct.get_signer_wl(m_ap,master_final_sig)=}")

    #TEST @@@
    sig_n2 = random.randint(42, 42200)

    m_apobj2 = WhitelistMintParams2(
        addy=accounts[0].address,
        valid_until_timestamp=mast_tstamp + 1000,
        ids=1,
        qtys=1,
        paid_ids=2,
        paid_qtys=2,        
        sig_nonce=sig_n2,
    )
    m_ap2 = (
        accounts[0].address,
        mast_tstamp + 1000,
        1,
        1,
        2,
        2,
        sig_n2,
    )
    master_signature2 = pk_master_signer.sign_recoverable(
        m_apobj2.signable_bytes(md), hasher=keccak_hash
    )
    mr2 = big_endian_to_int(master_signature2[0:32])
    ms2 = big_endian_to_int(master_signature2[32:64])
    mv2 = master_signature2[64] + 27
    master_final_sig2 = (
        mr2.to_bytes(32, "big") + ms2.to_bytes(32, "big") + mv2.to_bytes(1, "big")
    )
    ct.setSignerAddress(ac["owner"].address, {"from": ac["dep"]})
    print(f"{ac['owner'].address=}")
    print(f"{ct.get_signer_wl2(m_ap2,master_final_sig2)=}")    
    assert False

