# Copyright 2022 The UK Pilot Synthetic Data Gen Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Script to generate impressions for a single Campaign."""


from dataclasses import dataclass, asdict
import datetime
import numpy as np
from scipy import stats
import operator
import inspect
import csv
import math
from functools import reduce


# Total number of Virtual people, per the UK population
NUM_VIDS = 60_000_000

# Daily uniform noise size as fraction of the impressions that day.
DAILY_NOISE_FACTOR = 0.1

# Acceptable change applied to max frequency to make the num impressions
# play well with freq distribution.
ACCEPTABLE_FREQ_DIST_CORRECTION_FACTOR = 0.1

RAND_MIN = 0
RAND_MAX = 100_000

DEMO_BUCKETS = [{"age_range": "16-34", "sex" : "female" }, 
                {"age_range": "35-54", "sex" : "female" },
                {"age_range": "55+", "sex"   : "female" },
                {"age_range": "16-34", "sex" : "male" }, 
                {"age_range": "35-54", "sex" : "male" },
                {"age_range": "55+", "sex"   : "male" }]

class CampaignSpec:
    """Samples impressions on a given EDP on given dates, such that they approximately align with the given number of impressions, reach, and distributions of frequency, video completion, and viewability

    1. At initialization normalizes and reconstructs the frequency distribution to pad the frequency to meet the requirements of the other parameters.
        E.g. If freq distrubution is specified by [(1, 800), (2, 600), (3, 500)] 800 impressions with freq=1, 600 with freq=2...
             Then converts it to the prob distribution [(1, 0.42), (2, 0.31), (3, 0.27)]
             Given freq dist implies 1*800+ 2*600 + 3*500 = 4100 impressions but the given impresison requirement can be different (e.g. 5000)
                If so, then pads another frequency (4) to match that 4100+ 4*225 = 5000.
             Also makes sure that this correction does not change the given freq dist more than a small amount
    2. At initialization creates a pool of vids to be used in the sampling. This pool of vids consists of repeats specified by the frequency distribution.
        E.g : If the freq dist specifies 5 impressions with freq=1 and 3 with freq=2 using vidSet {1..100} we can generate
              vids=[1, 2, 3, 4, 5, 6 , 6, 7, 7, 8, 8] then, randomly shuffle this pool of vids.
    3. Selects number of impressions for each day = (total_impressions/numdays) + noise.  Where noise is uniform.
    3. For each day, pops vids from the pool according to the number of impressions for that day.
    4. For each impression, independently samples the video completion and viewability specified by the given distributions for them.
    """

    def __init__(
        self, edpId, mcId, cId, sd, nd, nImp, tr, freqDistSpec, videoCompDistSpec, viewabilityDistSpec, randomObject
    ):
        self.eventDataProviderId = edpId
        self.measurementConsumerId = mcId
        self.campaignId = cId
        self.num_days = nd
        self.dates = [sd + datetime.timedelta(days=x) for x in range(nd)]
        self.total_impressions = nImp
        self.total_reach = tr
        self.random = randomObject
        tempFreqDist = DiscreteDist(self.normalize(freqDistSpec), self.random.randint(RAND_MIN, RAND_MAX))
        self.freq_dist = self.reconstruct_freq_dist(tempFreqDist)
        self.video_completion_dist = (
            NoOpDiscreteDist()
            if videoCompDistSpec == None
            else DiscreteDist(videoCompDistSpec, self.random.randint(RAND_MIN, RAND_MAX))
        )
        self.viewability_dist = DiscreteDist(viewabilityDistSpec, self.random.randint(RAND_MIN, RAND_MAX))

        self.vids = self.sampleVids()

    def normalize(self, freqDistSpec):
        temp_normailized = [(val, round(reach / self.total_reach, 3)) for (val, reach) in freqDistSpec]
        max_freq = max([val for (val, prob) in temp_normailized])
        prob_for_max_freq = list(filter(lambda x: x[0] == max_freq, temp_normailized))[0][1]

        distButMax = list(filter(lambda x: x[0] != max_freq, temp_normailized))
        implied_prob_for_max_freq = round(1 - sum([prob for (val, prob) in distButMax]), 3)

        # There can be a correction but not much
        assert implied_prob_for_max_freq >= prob_for_max_freq
        assert (implied_prob_for_max_freq - prob_for_max_freq) < ACCEPTABLE_FREQ_DIST_CORRECTION_FACTOR

        normailized = distButMax + [(max_freq, implied_prob_for_max_freq)]
        return normailized

    def reconstruct_freq_dist(self, freqDist):
        max_freq = max([val for (val, prob) in freqDist.prob_tuples])

        prob_for_max_freq = list(filter(lambda x: x[0] == max_freq, freqDist.prob_tuples))[0][1]

        implied_number_of_impressions = sum(
            [self.total_reach * prob * val for (val, prob) in freqDist.prob_tuples if val != max_freq]
        )

        remaining_number_of_impressions = self.total_impressions - implied_number_of_impressions
        reach_in_max_freq = self.total_reach * prob_for_max_freq
        new_max_freq = math.ceil(remaining_number_of_impressions / reach_in_max_freq)
        new_prob_tuples = list(filter(lambda x: x[0] != max_freq, freqDist.prob_tuples)) + [
            (new_max_freq, prob_for_max_freq)
        ]
        new_freq_dist = DiscreteDist(new_prob_tuples, freqDist.seed)

        print(
            "Changed the old max frequency",
            max_freq,
            "to a new max frequency ==> ",
            new_max_freq,
        )
        return new_freq_dist

    # Demos are uniformly distributed
    def getDemo(self, vid):
        num_buckets = len(DEMO_BUCKETS)

        # Calculate the ideal number of IDs per bucket
        ids_per_bucket = math.ceil(NUM_VIDS / num_buckets)

        # Determine the bucket index based on the person ID
        bucket_index = (vid - 1) // ids_per_bucket 
        demo_bucket = DEMO_BUCKETS[bucket_index]

        return (demo_bucket["age_range"], demo_bucket["sex"])

    def sampleImpressionsForDay(self, date):
        impressions = []
        numImpressionsThisDay = int(
            (self.total_impressions / float(self.num_days))
            * self.random.uniform(1 - DAILY_NOISE_FACTOR, 1 + DAILY_NOISE_FACTOR)
        )
        for i in range(numImpressionsThisDay):
            vid = self.vids.pop()
            age_range, sex = self.getDemo(vid)
            imp = Impression(
                eventDataProviderId=self.eventDataProviderId,
                campaignId=self.campaignId,
                mcId=self.measurementConsumerId,
                vid=vid,
                sex=sex,
                age_range=age_range,
                digital_video_completion_status=self.video_completion_dist.sample(),
                viewability=self.viewability_dist.sample(),
                date=date.strftime("%d-%m-%Y"),
            )
            impressions.append(imp)
        return impressions

    # Sampled vids to fit the freq_dist, total_impressions and reach requirements
    def sampleVids(self):
        paddingFactor = 1 + (DAILY_NOISE_FACTOR)
        # Multiplied by the padding factor so that we don't run out of vids to sample due to daily reach noises adding up
        vidsToUse = self.random.sample(range(NUM_VIDS), int(paddingFactor * self.total_reach))
        vids = []
        while len(vidsToUse) > 0:  # Keep generating until you run out of vids used for sampling
            numImpressionsForVid = self.freq_dist.sample()
            vid = vidsToUse.pop()
            vid_replicated = [vid] * numImpressionsForVid
            vids += vid_replicated
        self.random.shuffle(vids)
        return vids


@dataclass
class Impression:
    """Class that represents a single impression."""

    # Id of the Event Data Provider
    eventDataProviderId: str

    # Id of the campaign this impression belongs to
    campaignId: str

    # Id of the Measurement Consumer this impression belongs to
    mcId: str

    # virtual person id
    vid: int

    # Sex of the virtual person
    sex : str

    # Age range of the virtual person
    age_range : str

    # Only for video
    digital_video_completion_status: float  # in unit interval

    # For both digital and video.
    viewability: str  # measurable, viewable_50_percent_plus, viewable_100_percent.

    # Date this impression happened
    date: str  # of the '%d-%m-%Y'


class DiscreteDist:
    """Class that represents Discrete distribution."""

    def __init__(self, prob_tuples, random_seed):
        self.seed = random_seed
        self.prob_tuples = prob_tuples
        self.vals = list(map(operator.itemgetter(0), prob_tuples))

        # Values must be unique
        assert len(set(self.vals)) == len(prob_tuples)

        self.probs = np.arange(len(prob_tuples)), list(map(operator.itemgetter(1), prob_tuples))
        self.custm = stats.rv_discrete(name="custm", values=self.probs, seed=self.seed)

    def sample(self):
        return self.vals[self.custm.rvs(size=1)[0]]


class NoOpDiscreteDist(DiscreteDist):
    def __init__(self):
        super().__init__([(0, 1)], 0)

    def sample(self):
        return "NaN"


def generate(
    randomObject,
    edpId,
    mcId,
    campaignId,
    completionDistSpec,
    viewabilityDistSpec,
    realFreqDistSpec,
    startdate,
    numdays,
    total_impressions,
    total_reach,
):
    campaignSpec = CampaignSpec(
        edpId,
        mcId,
        campaignId,
        startdate,
        numdays,
        total_impressions,
        total_reach,
        realFreqDistSpec,
        completionDistSpec,
        viewabilityDistSpec,
        randomObject,
    )
    return reduce(
        list.__add__,
        [campaignSpec.sampleImpressionsForDay(date) for date in campaignSpec.dates],
    )
