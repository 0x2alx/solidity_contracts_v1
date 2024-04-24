import brownie, pytest, pathlib, json, random, logging, sha3, time
from brownie import exceptions
from brownie.network.gas.strategies import GasNowStrategy
from eip712_structs import make_domain
from coincurve import PrivateKey, PublicKey
from eip712_structs import EIP712Struct, Address, String, Uint, Boolean, Bytes
from eth_utils import big_endian_to_int

LOGGER = logging.getLogger(__name__)


class Struct_one(EIP712Struct):
    var1 = Uint(32)
    var2 = Uint(32)
    var3 = Uint(32)
    var4 = Uint(32)
    var5 = Uint(32)
    var6 = Uint(32)


class Struct_test(EIP712Struct):
    var1 = Uint(256)
    var2 = Uint(256)
    var3 = Uint(256)
    var4 = Uint(256)
    var5 = Uint(256)
    var6 = Uint(256)


def test_premint_misc(fn_isolation, TESTG, ac, accounts):
    ct = ac["dep"].deploy(TESTG)

    # TEST SIGNED MINT

    md = make_domain(
        name="TESTG",
        version="1",
        chainId=1,
        verifyingContract=ct.address,
    )

    keccak_hash = lambda x: sha3.keccak_256(x).digest()
    pk_master_signer = PrivateKey.from_hex(ac["owner"].private_key[2:])
    var11 = random.randint(42, 46666)
    var12 = random.randint(42, 46666)
    var13 = random.randint(42, 46666)
    var14 = random.randint(42, 46666)
    var15 = random.randint(42, 46666)
    var16 = random.randint(42, 46666)
    sttwo = Struct_test(
        var1=var11,
        var2=var12,
        var3=var13,
        var4=var14,
        var5=var15,
        var6=var16,
    )
    sttwol = (
        var11,
        var12,
        var13,
        var14,
        var15,
        var16,
    )
    stone = Struct_one(
        var1=var11,
        var2=var12,
        var3=var13,
        var4=var14,
        var5=var15,
        var6=var16,
    )
    stonel = (
        var11,
        var12,
        var13,
        var14,
        var15,
        var16,
    )
    master_signature_one = pk_master_signer.sign_recoverable(
        stone.signable_bytes(md), hasher=keccak_hash
    )
    master_signature_two = pk_master_signer.sign_recoverable(
        sttwo.signable_bytes(md), hasher=keccak_hash
    )
    mr = big_endian_to_int(master_signature_one[0:32])
    ms = big_endian_to_int(master_signature_one[32:64])
    mv = master_signature_one[64] + 27
    mr2 = big_endian_to_int(master_signature_two[0:32])
    ms2 = big_endian_to_int(master_signature_two[32:64])
    mv2 = master_signature_two[64] + 27
    master_final_sig_one = (
        mr.to_bytes(32, "big") + ms.to_bytes(32, "big") + mv.to_bytes(1, "big")
    )
    master_final_sig_two = (
        mr2.to_bytes(32, "big") + ms2.to_bytes(32, "big") + mv2.to_bytes(1, "big")
    )

    ct.setMasterSigConf(ac["owner"].address, {"from": ac["dep"]})

    # ct.testInitMapping1(stonel, master_final_sig_one, {"from": ac["dep"]})
    # ct.testUpdateMapping1(stonel, master_final_sig_one, {"from": ac["dep"]})
    ct.testInitMapping(sttwol, master_final_sig_two, {"from": ac["dep"]})
    for i in range(0, 20):
        ct.testUpdateMapping(sttwol, master_final_sig_two, {"from": ac["dep"]})
