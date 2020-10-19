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
from service.model import Recommendation, db, DataValidationError
from service import app
from .recommendation_factory import RecommendationFactory

DATABASE_URI = os.getenv("DATABASE_URI",
                         "postgres://postgres:postgres@localhost:5432/postgres")

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
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    @classmethod
    def tearDownClass(cls):
        """ These run once after Test suite """

    def setUp(self):
        Recommendation.init_db(app)
        db.drop_all()  # clean up the last tests
        db.create_all()  # make our sqlalchemy tables

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_find_recommendation(self):
        """ Test find recommendation function """
        valid_recommendation = self._create_recommendations(count=1)[0]
        recommendation = Recommendation.find_recommendation( \
                                                   valid_recommendation.id,
                                                   valid_recommendation.rel_id,
                                                   valid_recommendation.status)

        self.assertEqual(recommendation.first(), valid_recommendation)

        valid_recommendation = self._create_recommendations(count=1,
                                                            by_status=False)[0]
        recommendation = Recommendation.find_recommendation( \
                                                   valid_recommendation.id,
                                                   valid_recommendation.rel_id,
                                                   valid_recommendation.status)

        self.assertEqual(recommendation.first(), valid_recommendation)

        valid_recommendation = self._create_recommendations(count=1,
                                                            by_status=False)[0]

        self.assertRaises(TypeError, Recommendation.find_recommendation, \
               "abcd", valid_recommendation.rel_id, valid_recommendation.status)

        self.assertRaises(TypeError, Recommendation.find_recommendation, \
               valid_recommendation.id, "efgh", valid_recommendation.status)

        self.assertRaises(TypeError, Recommendation.find_recommendation, \
               valid_recommendation.id, valid_recommendation.rel_id, "notbool")

    def test_check_if_product_exists(self):
        """ Test check if product exists """
        valid_recommendation = self._create_recommendations(count=1,
                                                            by_status=True)[0]

        exists = Recommendation.check_if_product_exists

        recommendation_exists = exists(valid_recommendation.id)
        self.assertTrue(recommendation_exists)

        recommendation_exists = exists(valid_recommendation.rel_id)
        self.assertTrue(recommendation_exists)

        recommendation_exists = exists(99999)
        self.assertFalse(recommendation_exists)

        self.assertRaises(TypeError, exists, "abcd")
        self.assertRaises(TypeError, exists, valid_recommendation.id, "notbool")

    def test_find_by_id_status(self):
        """ Test find_by_id_status function """
        test_recommendation = self._create_one_recommendation(by_id=1, by_rel_id=2, by_type=1)
        find_result = Recommendation.find_by_id_status(by_id=test_recommendation.id,
                                                       by_status=test_recommendation.status)

        self.assertEqual(len(find_result.all()), 1)
        self.assertEqual(find_result.first(), test_recommendation)

        test_recommendation = self._create_one_recommendation(by_id=1, by_rel_id=3, by_type=2)
        find_result = Recommendation.find_by_id_status(by_id=test_recommendation.id,
                                                       by_status=test_recommendation.status)

        self.assertEqual(len(find_result.all()), 2)

        self.assertRaises(TypeError, Recommendation.find_by_id_status, "not_int")
        self.assertRaises(TypeError, Recommendation.find_by_id_status, 1, "not_bool")

    def test_find_by_id_type(self):
        """ Test find_by_id_type function """
        test_recommendation = self._create_one_recommendation(by_id=1, by_rel_id=2, by_type=1)
        find_result = Recommendation.find_by_id_type(by_id=test_recommendation.id,
                                                     by_type=test_recommendation.typeid)

        self.assertEqual(len(find_result.all()), 1)
        self.assertEqual(find_result.first(), test_recommendation)

        test_recommendation = self._create_one_recommendation(by_id=1, by_rel_id=3, by_type=1)
        find_result = Recommendation.find_by_id_type(by_id=test_recommendation.id,
                                                     by_type=test_recommendation.typeid)

        self.assertEqual(len(find_result.all()), 2)

        self.assertRaises(TypeError, Recommendation.find_by_id_type, "not_int", 2)
        self.assertRaises(DataValidationError, Recommendation.find_by_id_type, 1, 5)


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
        test_recommendation = Recommendation(id=by_id,
                                             rel_id=by_rel_id,
                                             typeid=by_type,
                                             status= by_status)
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
