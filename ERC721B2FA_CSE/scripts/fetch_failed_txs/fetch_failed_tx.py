from cmath import log
from re import L
import time, json, os, traceback, logging, requests, csv
from pytest import fail
from brownie import accounts, Contract, chain, web3
from pprint import pformat
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

load_dotenv()

PROVIDER = os.getenv("WEB3_HTTP_PROVIDER")
ETHERSCAN_TOKEN = os.getenv("ETHERSCAN_TOKEN")

logging.basicConfig(
    # filename="./LOGS_fetch_failed_txs.out",
    # filemode="w",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger()

CONTRACT_ADDY = "0xe8eba3bc8a1da332d4f2bc2348c99dad1d0cb9ae"
DEMON_ADDY = "0xBB9422050576bf1792117c18941804034286f232"
OS_WYV_ADDY = "0x7f268357A8c2552623316e2562D90e642bB538E5"
CTR = None
MY_ADDY = None
COLL_SIZE = 300
SEP = "##########################################################################"


def init_shit():
    global CTR
    global MY_ADDY
    CTR = Contract.from_explorer(
        CONTRACT_ADDY, as_proxy_for="0xe4E4003afE3765Aca8149a82fc064C0b125B9e5a"
    )
    logger.info(f"\t CONTRACT: {CTR}")
    # MY_ADDY = accounts.load("MM1_DEPLOYER_0408")
    # logger.info(f"\t MY_ACCOUNT: {MY_ADDY}")


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


def get_events():
    owner_addys = []
    for i in range(1, 301):
        owner = CTR.ownerOf(i)
        if owner not in owner_addys:
            owner_addys.append(owner)
            logger.info(f"\t Owner of {i} is {owner}")
        time.sleep(0.3)
    logger.info(f"\n owner_addys len: {len(owner_addys)}")
    f = open("./owner_addys.out", "w")
    for a in owner_addys:
        f.write(a)
    f.close()
    event = "Transfer"
    web3_contract = web3.eth.contract(address=CTR.address, abi=CTR.abi)
    event_filter = web3_contract.events[event].createFilter(fromBlock=14786032)
    logger.info(f"\t web3_contract.events: {web3_contract.events}")

    all_evs = event_filter.get_all_entries()
    for ev in all_evs:
        logger.info(f"\t Found event: {ev}")
        if ev["args"]["from"] == DEMON_ADDY and ev["args"]["to"] not in owner_addys:
            owner_addys.append(ev["args"]["to"])
    logger.info(f"\t found {len(all_evs)} events")
    logger.info(f"\n owner_addys len: {len(owner_addys)}")

    f = open("./owner_addys.out", "w")
    for a in owner_addys:
        f.write(a + "\n")
    f.close()


def get_failed_tx(addy):
    url = (
        "https://api.etherscan.io/api?module=account"
        "&action=txlist"
        f"&address={addy}"
        "&startblock=14786032"
        "&endblock=99999999"
        # "&page=1"
        # "&offset=10"
        "&sort=desc"
        f"&apikey={ETHERSCAN_TOKEN}"
    )
    res = requests_retry_session().get(url).json()

    # logger.info(f"\t results: {res}")

    failed_tx = []
    for txx in res["result"]:
        tx_hash = txx["hash"]
        tx_to = txx["to"]
        tx_is_error = txx["isError"]
        logger.info(
            f"\t found tx: {tx_hash} -- tx_to: {tx_to} -- OS_WYV_ADDY: {OS_WYV_ADDY} -- tx_is_error: {tx_is_error}"
        )
        if tx_is_error == "1":
            # logger.info(f"\t found failed tx for {tx_from}")
            failed_tx.append(txx)
    logger.info(f"\n\t TOTAL_FAILED_TX: {failed_tx} --- len: {len(failed_tx)}")

    return res, failed_tx


def check_failed_txs():
    # fn_obj, fn_params = ctr_inst.decode_function_input(txx["input"])
    # wyv_ctr = Contract.from_explorer(OS_WYV_ADDY)
    # web3_contract = web3.eth.contract(address=wyv_ctr.address, abi=wyv_ctr.abi)
    f = open("JSON_OUT_FAILED.out", "r")
    failed_txs = json.loads(f.read())
    f.close()

    weird_tx = []
    good_txs = []
    other_txs = []
    for txx in failed_txs:
        if txx["to"][-6:] == "b538e5":
            logger.info(
                f"\n\n\t hash: {txx['hash']} -- tx_to: {txx['to']} -- value: {txx['value']}"
            )
            # fn_obj, fn_params = web3_contract.decode_function_input(txx["input"])
            if txx["value"] != "120000000000000000":
                weird_tx.append(txx["hash"])
            else:
                good_txs.append(txx)
            # if "calldataBuy" in fn_params:
            #    logger.info(
            #        f"\t fn_obj: {fn_obj} \n fn_params: {fn_params['calldataBuy']}"
            #    )
        else:
            other_txs.append(txx)

    logger.info(f"\n\n\t weird_tx: {weird_tx}")

    csv_dict = []
    for tt in good_txs:
        gas_price = int(tt["gasPrice"])
        gas_used = int(tt["gasUsed"])
        eth_lost = gas_price * gas_used

        already_there = False
        for cc in csv_dict:
            if cc["from"] == tt["from"]:
                cc["eth_lost"] += eth_lost
                cc["hash"] += " / " + tt["hash"]
                already_there = True
        if not already_there:
            csv_dict.append(
                {"from": tt["from"], "hash": tt["hash"], "eth_lost": eth_lost}
            )

    ff = open("FAILED_TXs.csv", "w")
    for ccc in csv_dict:
        priceee = str(ccc["eth_lost"] / 1000000000000000000)[0:7]
        ff.write(f"{ccc['from']}, {ccc['hash']}, {priceee}\n")
    ff.close()

    logger.info(
        f"\t failed_txs: {len(failed_txs)} -- weird_tx: {len(weird_tx)} -- good_txs: {len(good_txs)} -- {len(other_txs)}"
    )


def get_owners():
    owners = []
    for i in range(1, 301):
        ownerrr = CTR.ownerOf(i)
        logger.info(f"\t OWNERRR: {ownerrr}")
        owners.append(ownerrr)
        time.sleep(0.1)

    logger.info(f"\t len owners: {len(owners)}")
    unique_addys = []
    for i in range(0, len(owners)):
        if owners[i] not in unique_addys:
            unique_addys.append(owners[i])

    ff = open("DDCs02_owners_20220522.csv", "w")
    for i in range(0, len(unique_addys)):
        ff.write(f"{unique_addys[i]}, {owners.count(unique_addys[i])}\n")
    ff.close()


def check_owners():
    with open("DDCs02_owners_20220522.csv", newline="\n") as f:
        reader = csv.reader(f)
        data = list(reader)

    tot = 0
    for d in data:
        logger.info(d)
        if int(CTR.balanceOf(d[0])) != int(d[1]):
            logger.error(f"\t Error with {d}")
        tot += int(d[1])
    logger.info(tot)


def main():
    init_shit()
    # get_owners()
    check_owners()

    # check_failed_txs()
    return

    owner_addys = []
    f = open("./owner_addys.out", "r")

    owner_addys_str = f.read()
    owner_addys = owner_addys_str.split("\n")

    f.close()
    logger.info(f"\t owner_addys: {owner_addys} - len: {len(owner_addys)}")
    full_res = []
    full_failed = []
    for addy in owner_addys:
        logger.info(
            f"\n ############################ \n {addy} \n ############################"
        )
        res, failed_tx = get_failed_tx(addy)

        if len(res) > 0:
            for r in res["result"]:
                full_res.append(r)
            f = open("JSON_OUT.out", "w")
            f.write(json.dumps(full_res, indent=3))
            f.close()

        if len(failed_tx) > 0:
            for ff in failed_tx:
                full_failed.append(ff)
            f = open("JSON_OUT_FAILED.out", "w")
            f.write(json.dumps(full_failed, indent=3))
            f.close()

        logger.info("\n\n")
        time.sleep(0.5)
    # get_events()


if __name__ == "__main__":
    main()
