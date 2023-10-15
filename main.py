from dataclasses import dataclass, asdict
from generate import generate
import random
import datetime
import csv
import pandas as pd
import time
import argparse


parser = argparse.ArgumentParser()

parser.add_argument("-r", "--randomseed", help="Random seed", type=int)
parser.add_argument("-e", "--edpname", help="Edp name")


# read random seed from the command line (DONE)
# read EDP id from the command line (DONE)
# read the config from the sheet in this folder (DONE)
# filter the rows based on EDPid (DONE)
# convert 0+ .. to 0-25 ...
# create config from each row
# in the generator add the campaign name and MC name (DONE)


# Later:
# Figure out the issue with MRC 2 sec
# different event templates supporting different fields (DONE)

# random_seed = 30

# config_digital_1 = {
# 	'edp_name' : "EDP_DIGITAL1",
# 	'completionDistSpec' : [("0% - 25%", 0.2), ("25% - 50%", 0.2), ("50% - 75%", 0.2), ("75% - 100%", 0.2), ("100%", 0.2)],
# 	'viewabilityDistSpec' : [("viewable_0_percent_to_50_percent", 0.4), ("viewable_50_percent_to_100_percent", 0.4), ("viewable_100_percent", 0.2)],
# 	'realFreqDistSpec' : [(1, 800_000), (2, 600_000), (3, 500_000), (4, 400_000), (5, 650_000)],
# 	'total_impressions' :  9_000_000,
# 	'total_reach' : 2_950_000,
# }

# config_digital_2 = {
# 	'edp_name' : "EDP_DIGITAL2",
# 	'completionDistSpec' : [("0% - 25%", 0.1), ("25% - 50%", 0.1), ("50% - 75%", 0.1), ("75% - 100%", 0.1), ("100%", 0.6)],
# 	'viewabilityDistSpec' : [("viewable_0_percent_to_50_percent", 0.2), ("viewable_50_percent_to_100_percent", 0.2), ("viewable_100_percent", 0.6)],
# 	'realFreqDistSpec' : [(1, 2_400_000), (2, 1_800_000), (3, 1_500_000), (4, 1_200_000), (5, 1_950_000)],
# 	'total_impressions' :  27_000_000,
# 	'total_reach' : 8_850_000,
# }

# config_tv = {
# 	'edp_name' : "EDP_TV",
# 	'completionDistSpec' : [("0% - 25%", 0), ("25% - 50%", 0), ("50% - 75%", 0), ("75% - 100%", 0), ("100%", 1)],
# 	'viewabilityDistSpec' : [("viewable_0_percent_to_50_percent", 0), ("viewable_50_percent_to_100_percent", 0), ("viewable_100_percent", 1)],
# 	'realFreqDistSpec' : [(1, 4_800_000), (2, 3_600_000), (3,3_000_000), (4, 2_400_000), (5, 3_900_000)],
# 	'total_impressions' :  54_000_000,
# 	'total_reach' : 17_700_000,
# }

def generate_and_analyze_for_edp(config):
	print(config)
	print("########")
	# startDate = datetime.date(2022, 9, 1)
	# numdays = 91
	# impressions = generate(random_seed, config['edp_name'], config['completionDistSpec'],
	# 				        config['viewabilityDistSpec'], config['realFreqDistSpec'],
	# 				        startDate, numdays, config['total_impressions'],
	# 				        config['total_reach'])

	# impressionsDataFrame = pd.DataFrame.from_records([asdict(imp) for imp in impressions] )
	# impressionsDataFrame.to_csv(f"{config['edp_name']}_fake_data.csv", index=False)


if __name__ == "__main__":
    args = parser.parse_args()
    edpName = args.edpname
    randomSeed = args.randomseed
    print("Random Seed = {},  Edp Name = {}".format(randomSeed, edpName))
    df = pd.read_csv("config.csv")
    df = df[df['Publisher'] == edpName]
    print(df)
    for row in df.iterrows():
    	# print(f"START {config['edp_name']}")
    	generate_and_analyze_for_edp(row)
    	# print(f"END {config['edp_name']}")

    # start = time.time()
    # main()
    # end = time.time()
    # print(end - start)
