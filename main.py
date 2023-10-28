from dataclasses import dataclass, asdict
from generate import generate
import random
import datetime
import csv
import pandas as pd
import time
import argparse
import numpy as np
import math

parser = argparse.ArgumentParser()

parser.add_argument("-r", "--randomseed", help="Random seed", type=int)
parser.add_argument("-e", "--edpname", help="Edp name")


def getCompletionDistSpec(configRow):
    zeroPlus = configRow["completion_0%+"]
    totalImp = configRow["Impressions"]

    if math.isnan(zeroPlus):
        return None

    assert zeroPlus == totalImp

    twentyFivePlus = configRow["completion_25%+"]
    fiftyPlus = configRow["completion_50%+"]
    seventyFivePlus = configRow["completion_75%+"]
    hundred = configRow["completion_100%"]

    return [
        ("0% - 25%", (zeroPlus - twentyFivePlus) / totalImp),
        ("25% - 50%", (twentyFivePlus - fiftyPlus) / totalImp),
        ("50% - 75%", (fiftyPlus - seventyFivePlus) / totalImp),
        ("75% - 100%", (seventyFivePlus - hundred) / totalImp),
        ("100%", hundred / totalImp),
    ]


def getViewabilityDistSpec(configRow):
    zeroPlus = configRow["viewability_0%+"]
    totalImp = configRow["Impressions"]

    assert zeroPlus == totalImp

    fiftyPlus = configRow["viewability_50%+"]
    hundred = configRow["viewability_100%"]

    return [
        ("viewable_0_percent_to_50_percent", (zeroPlus - fiftyPlus) / totalImp),
        ("viewable_50_percent_to_100_percent", (fiftyPlus - hundred) / totalImp),
        ("viewable_100_percent", hundred / totalImp),
    ]


def getRealFreqDistSpec(configRow):
    mappingDict = {1: "Frequency 1", 2: "Frequency 2", 3: "Frequency 3", 4: "Frequency 4", 5: "Frequency 5+"}
    mappedResult = [(key, configRow[mappingDict[key]]) for key in mappingDict.keys()]
    assert configRow["Total Reach"] == sum([val[1] for val in mappedResult])

    return mappedResult


def generate_and_analyze_for_edp(configRow, randomSeed):
    startDate = datetime.datetime.strptime(configRow["Start Date"], "%m/%d/%Y")
    numdays = configRow["Number of days"]

    impressions = generate(
        randomSeed,
        configRow["Publisher"],
        configRow["Advertiser"],
        configRow["Event Groups"],
        getCompletionDistSpec(configRow),
        getViewabilityDistSpec(configRow),
        getRealFreqDistSpec(configRow),
        startDate,
        numdays,
        configRow["Impressions"],
        configRow["Total Reach"],
    )

    impressionsDataFrame = pd.DataFrame.from_records([asdict(imp) for imp in impressions])
    impressionsDataFrame.to_csv(f"{configRow['Publisher']}_fake_data.csv", mode="a", index=False)


if __name__ == "__main__":
    args = parser.parse_args()
    edpName = args.edpname
    randomSeed = args.randomseed
    print("Random Seed = {},  Edp Name = {}".format(randomSeed, edpName))
    df = pd.read_csv("config.csv")
    df = df[df["Publisher"] == edpName]
    randomObject = random.Random()

    for row in df.iterrows():
        start = time.time()
        print(f"START {row}")
        generate_and_analyze_for_edp(row[1], randomObject)
        end = time.time()
        print(end - start)
        print(f"END {row}")
