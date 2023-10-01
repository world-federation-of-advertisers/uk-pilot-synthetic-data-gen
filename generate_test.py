from unittest import TestCase
from generate import generate
import random
import datetime
from pytest import approx


EVENT_DATA_PROVIDERS = ["EDP1", "EDP2", "EDP3"]
VIEWING_COMPLETIONS = [
    "measurable",
    "viewable_50_percent_plus",
    "viewable_100_percent",
    "non_viewable",
]
VIDEO_COMPLETION_STATUS = ["0%+", "25%+", "50%+", "75%+", "100%"]

ACCEPTABLE_RELATIVE_ERROR = 1e-3


class GenerateTest(TestCase):
    def test_simple_spec(self):
        random_seed = 42
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
        realFreqDistSpec = [(1, 800), (2, 600), (3, 500), (4, 400), (5, 650)]
        startDate = datetime.date(2022, 9, 1)
        numdays = 91
        total_impressions = 9_000
        total_reach = 2_950
        impressions = generate(
            random_seed,
            "EDP1",
            completionDistSpec,
            viewabilityDistSpec,
            realFreqDistSpec,
            startDate,
            numdays,
            total_impressions,
            total_reach,
        )

        generated_number_of_impressions = len(impressions)
        self.assertTrue(
            generated_number_of_impressions,
            approx(total_impressions, rel=ACCEPTABLE_RELATIVE_ERROR),
        )

        generated_reach = len(set(list(map(lambda x: x.vid, impressions))))
        self.assertTrue(generated_reach, approx(total_reach, rel=ACCEPTABLE_RELATIVE_ERROR))
