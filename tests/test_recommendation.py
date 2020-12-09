# Copyright 2020 Agile Organization All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Recommendation Model

Test cases can be run with:
  nosetests
  coverage report -m
"""

import unittest
import os
import json
from service.model import Recommendation, db, DataValidationError
from service import app
from .recommendation_factory import RecommendationFactory

# Get configuration from environment
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgres://postgres:postgres@localhost:5432/postgres"
)

# Override if we are running in Cloud Foundry
if "VCAP_SERVICES" in os.environ:
    vcap = json.loads(os.environ["VCAP_SERVICES"])
    user_provided_services = vcap["user-provided"]
    for service in user_provided_services:
        if service["name"] == "ElephantSQL-test":
            DATABASE_URI = service["credentials"]["url"]
            break

######################################################################
#  T E S T   C A S E S
######################################################################
class TestRecommendation(unittest.TestCase):
    """ Test Cases for Recommendation """

    @classmethod
    def setUpClass(cls):
        """ These run once before Test suite """
        app.debug = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        Recommendation.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """ These run once after Test suite """
        db.session.close()  # <-- Explicitly close the connection after all tests

    def setUp(self):
        db.drop_all()  # clean up the last tests
        db.create_all()  # make our sqlalchemy tables

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_repr(self):
        """ Test Recommendation string representation """
        recommendation = self._create_recommendations(count=1)[0]
        expected = "<Recommendation %d %d %d>" % (
            recommendation.product_id,
            recommendation.related_product_id,
            recommendation.type_id,
        )
        actual = str(recommendation)
        self.assertEqual(expected, actual, "String representation is invalid")

    def test_create(self):
        """ Test Recommendation Create function """
        recommendation = Recommendation()
        recommendation.product_id = 10
        recommendation.related_product_id = 20
        recommendation.type_id = 20
        recommendation.status = True

        self.assertRaises(DataValidationError, recommendation.create)

    def test_save(self):
        """ Test Recommendation Save function """
        recommendation = self._create_recommendations(count=1)[0]
        recommendation.type_id = 20

        self.assertRaises(DataValidationError, recommendation.save)

    def test_deserialize(self):
        """ Test Recommendation deserialize function """
        invalid_recommendation = {
            "product-id": "abc",
            "related-product-id": "-10",
            "type-id": 20,
            "status": True,
        }

        recommendation = Recommendation()
        self.assertRaises(
            DataValidationError, recommendation.deserialize, invalid_recommendation
        )

        invalid_recommendation = {
            "product-id": 10,
            "related-product-id": 5,
            "type-id": "not int",
            "status": True,
        }

        recommendation = Recommendation()
        self.assertRaises(
            DataValidationError, recommendation.deserialize, invalid_recommendation
        )

        invalid_recommendation = {
            "product-id": "abc",
            "related-product-id": "-10",
            "type-id": 2,
            "status": True,
        }

        self.assertRaises(
            DataValidationError, recommendation.deserialize, invalid_recommendation
        )

        invalid_recommendation = {
            "product-id": 10,
            "related-product-id": 20,
            "type-id": 2,
        }

        self.assertRaises(
            DataValidationError, recommendation.deserialize, invalid_recommendation
        )

        invalid_recommendation = {
            "product-id": 10,
            "related-product-id": 20,
            "type-id": 2,
            "status": 10,
        }

        self.assertRaises(
            DataValidationError, recommendation.deserialize, invalid_recommendation
        )

    def test_all(self):
        """ Test all class method """
        num_recs = 10
        recommendation = self._create_recommendations(count=num_recs)[0]
        returned_records = len(recommendation.all())
        self.assertEqual(returned_records, num_recs, "Incorrect num")


    def test_check_if_product_exists(self):
        """ Test check if product exists """
        valid_recommendation = self._create_recommendations(count=1, by_status=True)[0]

        exists = Recommendation.check_if_product_exists

        recommendation_exists = exists(valid_recommendation.product_id)
        self.assertTrue(recommendation_exists)

        recommendation_exists = exists(valid_recommendation.related_product_id)
        self.assertTrue(recommendation_exists)

        recommendation_exists = exists(99999)
        self.assertFalse(recommendation_exists)

        self.assertRaises(TypeError, exists, "abcd")
        self.assertRaises(TypeError, exists, valid_recommendation.product_id, "notbool")

    
    def test_search_recommendations(self):
        """ Test search recommendations function """
        # create 4 recommendations
        recommendation_1 = self._create_one_recommendation(
            by_id=1, by_rel_id=2, by_type=3, by_status=True
        )

        recommendation_2 = self._create_one_recommendation(
            by_id=1, by_rel_id=3, by_type=1, by_status=True
        )

        recommendation_3 = self._create_one_recommendation(
            by_id=1, by_rel_id=4, by_type=2, by_status=False
        )

        recommendation_4 = self._create_one_recommendation(
            by_id=2, by_rel_id=3, by_type=2, by_status=False
        )

        args_1 = {}
        result_1 = Recommendation.search_recommendations(args_1)
        
        args_2 = {
            "product-id": recommendation_1.product_id
        }
        result_2 = Recommendation.search_recommendations(args_2)

        args_3 = {
            "product-id": recommendation_2.product_id,
            "related-product-id": recommendation_2.related_product_id
        }
        result_3 = Recommendation.search_recommendations(args_3)

        self.assertEqual(len(result_1), 4)
        self.assertEqual(len(result_2), 3)
        self.assertEqual(len(result_3), 1)

        self.assertEqual(result_3[0], recommendation_2)

        invalid_args_1 = {
            "product-id": "test",
            "type-id": 1
        }
        self.assertRaises(
            TypeError, Recommendation.search_recommendations, invalid_args_1
        )

        invalid_args_2 = {
            "product-id": 1,
            "type-id": 999
        }
        self.assertRaises(
            DataValidationError, Recommendation.search_recommendations, invalid_args_2
        )

        invalid_args_3 = {
            "product-id": 1,
            "status": "yes"
        }
        self.assertRaises(
            TypeError, Recommendation.search_recommendations, invalid_args_3
        )
     

    ######################################################################
    #   HELPER FUNCTIONS
    ######################################################################
    def _create_recommendations(self, count, by_status=True):
        """ Factory method to create Recommendations in bulk count <= 10000 """
        recommendations = []
        if not isinstance(count, int):
            return []
        if not isinstance(by_status, bool):
            return []
        for _ in range(count):
            test_recommendation = RecommendationFactory()
            test_recommendation.status = by_status
            test_recommendation.create()
            recommendations.append(test_recommendation)
        return recommendations

    def _create_one_recommendation(self, by_id, by_rel_id, by_type, by_status=True):
        """ Create one specific recommendation for testing """
        test_recommendation = Recommendation(
            product_id=by_id,
            related_product_id=by_rel_id,
            type_id=by_type,
            status=by_status,
        )
        test_recommendation.create()
        return test_recommendation

    def test_create_recommendations(self):
        """ Tests create recommendations """
        recommendations = self._create_recommendations(count=10, by_status=True)
        self.assertEqual(len(recommendations), 10)
        for recommendation in recommendations:
            self.assertTrue(recommendation.status)

        recs = self._create_recommendations(count=10, by_status=False)
        self.assertEqual(len(recs), 10)
        for recommendation in recs:
            self.assertFalse(recommendation.status)

        recommendations = self._create_recommendations(count=-10)
        self.assertEqual(len(recommendations), 0)

        recommendations = self._create_recommendations(count="ab")
        self.assertEqual(len(recommendations), 0)

        recommendations = self._create_recommendations(count=20, by_status="ab")
        self.assertEqual(len(recommendations), 0)


######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    unittest.main()
