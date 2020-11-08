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
if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.environ['VCAP_SERVICES'])
    DATABASE_URI = vcap['user-provided'][0]['credentials']['url']

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
        Recommendation.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """ These run once after Test suite """

    def setUp(self):
        db.drop_all()  # clean up the last tests
        db.create_all()  # make our sqlalchemy tables

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_repr(self):
        """ Test Recommendation string representation """
        recommendation = self._create_recommendations(count=1)[0]
        expected = "<Recommendation %d %d %d>" % (recommendation.product_id,
                                                  recommendation.related_product_id,
                                                  recommendation.type_id)
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
        invalid_recommendation = \
        {
            "product-id": "abc",
            "related-product-id": "-10",
            "type-id": 20,
            "status": True
        }

        recommendation = Recommendation()
        self.assertRaises(DataValidationError,
                          recommendation.deserialize, invalid_recommendation)
        
        invalid_recommendation = \
        {
            "product-id": 10,
            "related-product-id": 5,
            "type-id": "not int",
            "status": True
        }

        recommendation = Recommendation()
        self.assertRaises(DataValidationError,
                          recommendation.deserialize, invalid_recommendation)

        invalid_recommendation = \
        {
            "product-id": "abc",
            "related-product-id": "-10",
            "type-id": 2,
            "status": True
        }

        self.assertRaises(DataValidationError,
                          recommendation.deserialize, invalid_recommendation)

        invalid_recommendation = \
        {
            "product-id": 10,
            "related-product-id": 20,
            "type-id": 2,
        }

        self.assertRaises(DataValidationError,
                          recommendation.deserialize, invalid_recommendation)

        invalid_recommendation = \
        {
            "product-id": 10,
            "related-product-id": 20,
            "type-id": 2,
            "status": 10
        }

        self.assertRaises(DataValidationError,
                          recommendation.deserialize, invalid_recommendation)

    def test_find(self):
        """ Test find class method """
        num_recs = 10
        recommendation = self._create_recommendations(count=num_recs)[0]
        returned_records = recommendation.find(recommendation.product_id).count()
        self.assertEqual(returned_records, 1, "Only one record should exist")

    def test_find_by_type_id(self):
        """ Test find by product_id and related_product_id function """
        recommendation = self._create_one_recommendation(by_id=1, by_rel_id=2, by_type=1)
        result = Recommendation.find_by_type_id(by_type_id=recommendation.type_id)
        
        self.assertEqual(len(result.all()), 1)
        self.assertEqual(result.first(), recommendation)

        self.assertRaises(TypeError, Recommendation.find_by_type_id, "not int")
        self.assertRaises(DataValidationError, Recommendation.find_by_type_id, 4)
    
    def test_find_by_status(self):
        """ Test find by product_id and related_product_id function """
        recommendation = self._create_one_recommendation(by_id=1, by_rel_id=2, by_type=1)
        result = Recommendation.find_by_status(by_status=True)
        
        self.assertEqual(len(result.all()), 1)
        self.assertEqual(result.first(), recommendation)

        self.assertRaises(TypeError, Recommendation.find_by_status, "not bool")
    
    def test_find_by_type_id_status(self):
        """ Test find by product_id and related_product_id function """
        recommendation = self._create_one_recommendation(by_id=1, by_rel_id=2, by_type=1)
        result = Recommendation.find_by_type_id_status(by_type_id=recommendation.type_id, by_status=True)
        
        self.assertEqual(len(result.all()), 1)
        self.assertEqual(result.first(), recommendation)

        self.assertRaises(TypeError, Recommendation.find_by_type_id_status, "not int", True)
        self.assertRaises(DataValidationError, Recommendation.find_by_type_id_status, 4, True)
        self.assertRaises(TypeError, Recommendation.find_by_type_id_status, 3, "not bool")

    def test_find_by_id_relid(self):
        """ Test find by product_id and related_product_id function """
        test_recommendation = self._create_one_recommendation(by_id=1, by_rel_id=2, by_type=1)
        find_result = Recommendation.find_by_id_relid(by_id=test_recommendation.product_id,
                                                      by_rel_id=test_recommendation.related_product_id)
        
        self.assertEqual(len(find_result.all()), 1)
        self.assertEqual(find_result.first(), test_recommendation)

        find_result_empty = Recommendation.find_by_id_relid(by_id=test_recommendation.product_id,
                                                            by_rel_id=3)
        self.assertEqual(len(find_result_empty.all()), 0)

        self.assertRaises(TypeError, Recommendation.find_by_id_relid, 1, "not_int")
        self.assertRaises(TypeError, Recommendation.find_by_id_relid, "not_int", 1)

    def test_all(self):
        """ Test all class method """
        num_recs = 10
        recommendation = self._create_recommendations(count=num_recs)[0]
        returned_records = len(recommendation.all())
        self.assertEqual(returned_records, num_recs, "Incorrect num")

    def test_find_recommendation(self):
        """ Test find recommendation function """
        valid_recommendation = self._create_recommendations(count=1)[0]
        recommendation = Recommendation.find_recommendation( \
                                                   valid_recommendation.product_id,
                                                   valid_recommendation.related_product_id,
                                                   valid_recommendation.status)

        self.assertEqual(recommendation.first(), valid_recommendation)

        valid_recommendation = self._create_recommendations(count=1,
                                                            by_status=False)[0]
        recommendation = Recommendation.find_recommendation( \
                                                   valid_recommendation.product_id,
                                                   valid_recommendation.related_product_id,
                                                   valid_recommendation.status)

        self.assertEqual(recommendation.first(), valid_recommendation)

        valid_recommendation = self._create_recommendations(count=1,
                                                            by_status=False)[0]

        self.assertRaises(TypeError, Recommendation.find_recommendation, \
               "abcd", valid_recommendation.related_product_id, valid_recommendation.status)

        self.assertRaises(TypeError, Recommendation.find_recommendation, \
               valid_recommendation.product_id, "efgh", valid_recommendation.status)

        self.assertRaises(TypeError, Recommendation.find_recommendation, \
               valid_recommendation.product_id, valid_recommendation.related_product_id, "notbool")

    def test_check_if_product_exists(self):
        """ Test check if product exists """
        valid_recommendation = self._create_recommendations(count=1,
                                                            by_status=True)[0]

        exists = Recommendation.check_if_product_exists

        recommendation_exists = exists(valid_recommendation.product_id)
        self.assertTrue(recommendation_exists)

        recommendation_exists = exists(valid_recommendation.related_product_id)
        self.assertTrue(recommendation_exists)

        recommendation_exists = exists(99999)
        self.assertFalse(recommendation_exists)

        self.assertRaises(TypeError, exists, "abcd")
        self.assertRaises(TypeError, exists, valid_recommendation.product_id, "notbool")

    def test_find_by_id_status(self):
        """ Test find_by_id_status function """
        test_recommendation = self._create_one_recommendation(by_id=1, by_rel_id=2, by_type=1)
        find_result = Recommendation.find_by_id_status(by_id=test_recommendation.product_id,
                                                       by_status=test_recommendation.status)

        self.assertEqual(len(find_result.all()), 1)
        self.assertEqual(find_result.first(), test_recommendation)

        test_recommendation = self._create_one_recommendation(by_id=1, by_rel_id=3, by_type=2)
        find_result = Recommendation.find_by_id_status(by_id=test_recommendation.product_id,
                                                       by_status=test_recommendation.status)

        self.assertEqual(len(find_result.all()), 2)

        self.assertRaises(TypeError, Recommendation.find_by_id_status, "not_int")
        self.assertRaises(TypeError, Recommendation.find_by_id_status, 1, "not_bool")

    def test_find_by_id_type(self):
        """ Test find_by_id_type function """
        test_recommendation = self._create_one_recommendation(by_id=1, by_rel_id=2, by_type=1)
        find_result = Recommendation.find_by_id_type(by_id=test_recommendation.product_id,
                                                     by_type=test_recommendation.type_id)

        self.assertEqual(len(find_result.all()), 1)
        self.assertEqual(find_result.first(), test_recommendation)

        test_recommendation = self._create_one_recommendation(by_id=1, by_rel_id=3, by_type=1)
        find_result = Recommendation.find_by_id_type(by_id=test_recommendation.product_id,
                                                     by_type=test_recommendation.type_id)

        self.assertEqual(len(find_result.all()), 2)

        self.assertRaises(TypeError, Recommendation.find_by_id_type, "not_int", 2)
        self.assertRaises(TypeError, Recommendation.find_by_id_type, 1, "not_int")
        self.assertRaises(DataValidationError, Recommendation.find_by_id_type, 1, 5)
    
    def test_find_by_id_type_status(self):
        """ Test find_by_id_type_status function """
        recommendation = self._create_one_recommendation(by_id=1, by_rel_id=2, by_type=3)
        
        result = Recommendation.find_by_id_type_status(by_id=recommendation.product_id,
                                                     by_type=recommendation.type_id, by_status=recommendation.status)

        self.assertEqual(len(result.all()), 1)
        self.assertEqual(result.first(), recommendation)

        self.assertRaises(TypeError, Recommendation.find_by_id_type_status, "not int", 2, 2)
        self.assertRaises(TypeError, Recommendation.find_by_id_type_status, 1, "not int", 2)
        self.assertRaises(TypeError, Recommendation.find_by_id_type_status, 1, 2, "not bool")
        self.assertRaises(DataValidationError, Recommendation.find_by_id_type_status, 1, 5, True)


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
        test_recommendation = Recommendation(product_id=by_id,
                                             related_product_id=by_rel_id,
                                             type_id=by_type,
                                             status=by_status)
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
