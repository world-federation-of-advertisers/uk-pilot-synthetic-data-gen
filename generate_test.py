from unittest import TestCase
from generate import generate
import random
import datetime
from pytest import approx
import collections


EVENT_DATA_PROVIDERS = ["EDP1", "EDP2", "EDP3"]
VIEWING_COMPLETIONS = [
    "measurable",
    "viewable_50_percent_plus",
    "viewable_100_percent",
    "non_viewable",
]
VIDEO_COMPLETION_STATUS = ["0%+", "25%+", "50%+", "75%+", "100%"]

ACCEPTABLE_RELATIVE_ERROR = 1e-1


class GenerateTest(TestCase):
    def test_simple_spec(self):
        random_seed = 42
        randomObject = random.Random()
        randomObject.seed(random_seed)
        completionDistSpec = [
            ("0%+", 0.2),
            ("25%+", 0.2),
            ("50%+", 0.2),
            ("75%+", 0.2),
            ("100%", 0.2),
        ]
        viewabilityDistSpec = [
            ("measurable", 0.4),
            ("viewable_50_percent_plus", 0.4),
            ("viewable_100_percent", 0.1),
            ("non_viewable", 0.1),
        ]
        maxFreq = 5
        realFreqDistSpec = [(1, 800), (2, 600), (3, 500), (4, 400), (maxFreq, 650)]
        startDate = datetime.date(2022, 9, 1)
        numdays = 91
        total_impressions = 9_000
        total_reach = 2_950
        impressions = generate(
            randomObject,
            "EDP1",
            "SomeMC",
            "SomeCampaign",
            completionDistSpec,
            viewabilityDistSpec,
            realFreqDistSpec,
            startDate,
            numdays,
            total_impressions,
            total_reach,
        )

        generated_number_of_impressions = len(impressions)

        # Assert generated number of impressions is correct
        self.assertTrue(
            generated_number_of_impressions == approx(total_impressions, rel=ACCEPTABLE_RELATIVE_ERROR),
        )

        # Assert generated reach is correct
        generated_reach = len(set(list(map(lambda x: x.vid, impressions))))
        self.assertTrue(generated_reach == approx(total_reach, rel=ACCEPTABLE_RELATIVE_ERROR))

        completionCountDict = dict(list(map(lambda x: (x[0], 0), completionDistSpec)))
        viewabilityCountsDict = dict(list(map(lambda x: (x[0], 0), viewabilityDistSpec)))

        # Assert generated completion and viewibilty distributions are correct
        for imp in impressions:
            completionCountDict[imp.digital_video_completion_status] += 1
            viewabilityCountsDict[imp.viewability] += 1

        for viewabilityKey in viewabilityCountsDict:
            self.assertTrue(
                (viewabilityCountsDict[viewabilityKey] / generated_number_of_impressions)
                == approx(dict(viewabilityDistSpec)[viewabilityKey], rel=ACCEPTABLE_RELATIVE_ERROR),
            )

        for completionKey in completionCountDict:
            self.assertTrue(
                (completionCountDict[completionKey] / generated_number_of_impressions)
                == approx(dict(completionDistSpec)[completionKey], rel=ACCEPTABLE_RELATIVE_ERROR),
            )

        # Assert that Frequency Distribution is correct
        counter = collections.Counter(map(lambda x: x.vid, impressions))
        hist = dict(collections.Counter([i[1] for i in counter.items()]).items())
        if maxFreq + 1 in hist:
            hist[maxFreq] += hist[maxFreq + 1]
        # print(hist)
        realFreqDict = dict(realFreqDistSpec)
        for freqKey in realFreqDict:
            self.assertTrue(
                hist[freqKey] == approx(realFreqDict[freqKey], rel=2e-1),
            )
