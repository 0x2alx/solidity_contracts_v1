from copy import copy
from hashlib import new
import json, shutil
from pprint import pprint
from textwrap import indent

collection_size = 777
MD_FOLDER = "./metadata/pinata_metadata/"
IMG_FOLDER = "./metadata/pinata_imgs/"


pinata_imgs_folder = "QmTdTitSjo3MXWjC1E2ftZbFCqLXtyKqbMCEgH7uWNRZ5g"
pinata_metadata_folder = ""

md_base = {}

description = "Newman Alphas"
external_url = "https://twitter.com/Newman_NFT"
name = "NewmanNFT #"
attributes = [
    {"trait_type": "Tier", "value": "Platinum"},
]


pprint(md_base)


def copy_images():
    for i in range(201, collection_size + 1):
        print(i)
        shutil.copy(IMG_FOLDER + "n_default.png", IMG_FOLDER + str(i) + ".png")


def create_md_json():
    md_base = {}
    md_base["description"] = description
    md_base["external_url"] = external_url
    md_base["name"] = name
    md_base["attributes"] = attributes
    for i in range(1, collection_size + 1):
        f = open(MD_FOLDER + f"{i}.json", "w")
        md_base["image"] = f"ipfs://{pinata_imgs_folder}/{i}.png"
        if i > 200:
            md_base["attributes"] = [
                {"trait_type": "Tier", "value": "Gold"},
            ]
            md_base["image"] = f"https://ghooost0x2a.xyz/newmanNFTimgs/{i}.png"
        md_base["name"] = name + str(i)
        f.write(
            json.dumps(
                md_base,
                indent=4,
            )
        )
        f.close()


def generate_migration_data():
    f = open("OS_scrapper/snapshot_17042022_GOOD.txt", "r")
    sn = json.loads(f.read())
    f.close()
    pprint(sn)
    f = open("OS_scrapper/migration_addys.txt", "w")
    for i in range(1, 201):
        print(sn[str(i)])
        print(i)
        assert int(i)
        f.write(sn[str(i)]["addy"] + ",")
        # if i % 10 == 0:
        #    f.write("\n\n")
    f.close()


def check_diffs():
    old_list = []
    ff = open("OS_scrapper/migration_addys_3132mixed.txt", "r")
    old_list_temp = ff.read()
    ff.close()
    old_list = old_list_temp.split(",")

    new_list = []
    ff2 = open("OS_scrapper/migration_addys.txt", "r")
    new_list_temp = ff2.read()
    ff2.close()
    new_list = new_list_temp.split(",")

    print(new_list)
    print(old_list)
    assert len(new_list) == len(old_list)

    for i in range(0, len(new_list)):
        if old_list[i] != new_list[i]:
            print("DIFF!: ")
            print("Old = " + str(i) + " - " + old_list[i])
            print("New = " + str(i) + " - " + new_list[i])


check_diffs()
# generate_migration_data()
# 544301 x 20 -- 1565421 x 60
