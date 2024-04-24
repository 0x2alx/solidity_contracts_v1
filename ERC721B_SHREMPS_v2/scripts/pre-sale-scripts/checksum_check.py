from web3 import Web3
import os, logging, asyncio, random, json, pprint


def get_current_path(dirr=""):
    patth = os.path.abspath(os.path.dirname(__file__))
    if dirr != "":
        patth += f"/{dirr}"
    if not os.path.exists(patth):
        os.mkdir(patth)
    return patth

input_f = open(f"{get_current_path()}/out/MerkleTree.json", "r")

input_json = json.load(input_f)

#pprint.pprint(input_json['addys'])

for add in input_json['addys']:
    is_addy = Web3.isAddress(add)
    checksum_add = Web3.toChecksumAddress(add)
    if checksum_add != add:
        print("FUCCCCCCCCCCCKKKK")
    if not Web3.isChecksumAddress(add):
        print(f"addy = {add} / checksum = {checksum_add} /isAddress = {is_addy} / isChecksum = {Web3.isChecksumAddress(add)}\n\n")
