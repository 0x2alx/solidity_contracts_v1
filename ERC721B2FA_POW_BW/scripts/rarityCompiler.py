import requests, json
from operator import itemgetter
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from pprint import pprint

BASE_GATEWAY_URL = "https://gateway.pinata.cloud/ipfs"
BASE_IPFS_FOLDER = "QmRaKNw9fD4MgEzY2HVoQtDtC7BrGUcUTyo2kxG92u2k8i"
BASE_METADA_SUFF = ".json"
FIRST_TOKEN = 1

debug = False


def main():
    fetchMetada()


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def getMDURL(id):
    return BASE_GATEWAY_URL + "/" + BASE_IPFS_FOLDER + "/" + str(id) + BASE_METADA_SUFF


def fetchMetada():
    token = FIRST_TOKEN
    all_jsons = []
    all_traits = {}
    try:
        with open("./all_jsons.json", "r") as f:
            all_jsons = json.load(f)
    except:
        print("Error")
    if len(all_jsons) == 0:
        while True:
            resp = requests_retry_session().get(getMDURL(token))
            if not resp.ok:
                break
            else:
                resp_json = resp.json()
                all_jsons.append(resp_json)
                print(len(all_jsons))
                if debug == True and token >= 5:
                    break
                token += 1
    pprint(all_jsons)
    print("\n\n")
    print(len(all_jsons))

    for nft in range(0, len(all_jsons)):
        attributes = all_jsons[nft]["attributes"]
        # pprint(attributes)
        for attr in range(0, len(attributes)):
            tname = attributes[attr]["trait_type"]
            tval = attributes[attr]["value"]
            # print(tname)
            # print(tval)
            if not tname in all_traits:
                all_traits[tname] = {}
            if not tval in all_traits[tname]:
                all_traits[tname][tval] = 1
            else:
                all_traits[tname][tval] = int(all_traits[tname][tval]) + 1

    print(all_traits)
    calcRarity(all_jsons, all_traits)


def calcRarity(all_jsons, all_traits):
    combined_rars = {}
    highest_attr_count = 0

    for nft in range(0, len(all_jsons)):
        attributes = all_jsons[nft]["attributes"]
        pprint(attributes)
        compound_rar = 0
        nb_attr = len(attributes)
        if nb_attr > highest_attr_count:
            highest_attr_count = nb_attr
        for attr in range(0, nb_attr):
            print("\n################################")
            tname = attributes[attr]["trait_type"]
            tval = attributes[attr]["value"]
            # print(tname)
            # print(tval)
            rar = 1 / int(all_traits[tname][tval])
            attributes[attr]["rarity"] = rar
            compound_rar += rar
            print("rar = " + str(rar))
        if nb_attr == 1:
            compound_rar *= highest_attr_count
        print("Compound rar = " + str(compound_rar))
        all_jsons[nft]["rarity"] = compound_rar * 100
        combined_rars[nft] = compound_rar * 100

        print("\n\n")
    # pprint(all_jsons)
    # print(combined_rars)
    sorted_rars = sorted(combined_rars.items(), key=itemgetter(1), reverse=True)

    for i, val in enumerate(sorted_rars):
        print(
            "Rank: "
            + str(i + 1)
            + " - Avril #"
            + str(val[0])
            + " - Rarity: "
            + str(int(val[1]))
        )

    f = open("./all_jsons.json", "w")
    # comb_json = [{i: j for x in all_jsons for i, j in x.items()}]
    # pprint(comb_json)
    f.write(
        json.dumps(
            all_jsons,
            indent=4,
        )
    )
    f.close()


if __name__ == "__main__":
    main()
