from hashlib import new
import os, logging, asyncio, random
from web3 import Web3


def get_current_path(dirr=""):
    patth = os.path.abspath(os.path.dirname(__file__))
    if dirr != "":
        patth += f"/{dirr}"
    if not os.path.exists(patth):
        os.mkdir(patth)
    return patth


logging.basicConfig(
    # filename=f"{get_current_path('twbots_out')}/LOGS_tweets_bot_list.out",
    # filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%D %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("tempp")
logger.setLevel(logging.INFO)


async def main():
    raw_input_f = open(f"{get_current_path()}/markletree_INPUT_RAW", "r")

    raw_list = raw_input_f.readlines()
    new_list = []
    duplicates = []
    for rr in raw_list:
        addyyy_t = rr.lower().replace(" ", "").replace("\n", "")
        addyyy = Web3.toChecksumAddress(addyyy_t)
        print(len(str(addyyy)))
        if len(str(addyyy)) != 42 and raw_list.index(rr) != len(raw_list) - 1:
            print("ERROR")
            print(rr)
            exit(1)
        if not Web3.isChecksumAddress(addyyy):
            print(f"addy {addyyy} no checksumed")
            exit(1)
        if str(addyyy) + "\n" not in new_list:
            new_list.append(str(addyyy) + "\n")
        else:
            duplicates.append(str(addyyy) + "\n")

    new_list[len(new_list) - 1] = new_list[len(new_list) - 1].rstrip("\n")
    if False:
        counter = 0
        while len(new_list) < 2500:
            modified_str = new_list[random.randint(0, len(new_list) - 1)]
            modified = list(modified_str)
            while modified_str.lower() in new_list:
                changing = random.randint(2, 40)
                ch_to = random.randint(0, 9)
                logger.info(f"Changing {changing} to {ch_to}")
                modified[changing] = ch_to
                modified_str = ""
                for f in modified:
                    modified_str += str(f)
                logger.info(f"Testing {modified_str}")
            new_list.append(modified_str)
            counter += 1

        logger.info(new_list)
        logger.info(len(new_list))

    logger.info(f"Final count of unique addresses: {len(new_list)}")
    logger.info(f"Duplicates: {duplicates} --- {len(duplicates)}")
    raw_output_f = open(f"{get_current_path()}/markletree_OUTPUT_CLEANED", "w")
    raw_output_f.writelines(new_list)

    return
    _added = []
    for f in raw_list:
        lower_c = str(f).lower()
        logger.info(f"address: {f}")
        if lower_c != f:
            logger.info(f"\tLower_case addy = {lower_c}")
        if lower_c not in _added:
            _added.append(lower_c)

    logger.info(f"total addys = {len(raw_list)}")
    logger.info(f"total addys added (without duplicates) = {len(_added)}")
    raw_output_f = open(f"{get_current_path()}/markletree_OUTPUT", "w")
    raw_output_f.writelines(_added)


if __name__ == "__main__":
    asyncio.run(main())
