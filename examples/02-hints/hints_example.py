from hpman.m import _
from hpman.hpm_db import L

import argparse

_("optimizer", "adam", choices=["adam", "sgd"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    _.parse_file(__file__)
    occurrences = _.db.select(lambda row: row.name == "optimizer")
    oc = [oc for oc in occurrences if oc["hints"] is not None][0]
    choices = oc["hints"]["choices"]
    value = oc["value"]

    parser.add_argument("--optimizer", default=value, choices=choices)
    args = parser.parse_args()

    print("optimizer: {}".format(args.optimizer))
