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
Recommendation API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN
"""

import unittest
import os
import logging
from flask import request
from flask_api import status
from service.model import Recommendation, db
from service import app
from service.service import init_db
<<<<<<< HEAD
from flask_api import status
=======
from .recommendation_factory import RecommendationFactory
>>>>>>> master

# Disable all but ciritcal erros suirng unittest
logging.disable(logging.CRITICAL)

<<<<<<< HEAD
DATABASE_URI = os.getenv("DATABASE_URI", "postgres://postgres:postgres@localhost:5432/postgres")
=======
DATABASE_URI = os.getenv("DATABASE_URI",
                         "postgres://postgres:postgres@localhost:5432/postgres")
>>>>>>> master

######################################################################
#  T E S T   C A S E S
######################################################################
class TestRecommendationService(unittest.TestCase):
    """ Recommendation Server Tests """

    @classmethod
    def setUpClass(cls):
        """ Run once before all tests """
        app.debug = False
        app.testing = True
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    @classmethod
    def tearDownClass(cls):
        """ Run once after all tests """
        pass

    def setUp(self):
        """ Runs before each test """
        init_db()
        db.drop_all()  # clean up the last tests
        db.create_all()  # create new tables
        self.app = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_index(self):
        """ Test index call """
        resp = self.app.get("/")
        data = resp.get_json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(data)

    def _create_recommendations(self, count, by_status=True):
        """ Factory method to create Recommendations in bulk count <= 10000 """
        if not isinstance(count, int): return []
        if not isinstance(by_status, bool): return []
        recommendations = []
        for _ in range(count):
            test_recommendation = RecommendationFactory()
            test_recommendation.status = by_status
            resp = self.app.post(
                "/recommendations",
                json=test_recommendation.serialize(),
                content_type="application/json"
            )
            recommendations.append([
                                    test_recommendation,
                                    resp.headers.get("Location", None)
                                   ])
        return recommendations

    def test_create_recommendations(self):
        """ Tests create recommendations """
        recommendations = self._create_recommendations(count=10, by_status=True)
        self.assertEqual(len(recommendations), 10)
        for recommendation, location in recommendations:
            self.assertTrue(recommendation.status)
            self.assertIsNotNone(location)

        recommendations = self._create_recommendations(count=10,
                                                                by_status=False)
        self.assertEqual(len(recommendations), 10)
        for recommendation, location in recommendations:
            self.assertFalse(recommendation.status)
            self.assertIsNotNone(location)

        recommendations = self._create_recommendations(count=-10)
        self.assertEqual(len(recommendations), 0)

        recommendations = self._create_recommendations(count="ab")
        self.assertEqual(len(recommendations), 0)

        recommendations = self._create_recommendations(count=20, by_status="ab")
        self.assertEqual(len(recommendations), 0)

    def test_get_recommendation_relationship_type(self):
        """ Get recommendation relationship type for two products """
        valid_recommendation = self._create_recommendations(count=1)[0][0]
        resp = self.app.get\
            (
            "/recommendations/relationship",
            query_string=dict
                (
                    product1=valid_recommendation.id,
                    product2=valid_recommendation.rel_id
                )
            )
        new_recommendation = Recommendation()
        new_recommendation.deserialize(resp.get_json())

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(new_recommendation,
                         valid_recommendation,
                         "recommendations does not match")

        valid_inactive_recommendation = self._create_recommendations(count=1,
                                                          by_status=False)[0][0]
        resp = self.app.get(
            "/recommendations/relationship",
            query_string=dict(product1=valid_inactive_recommendation.id,
            product2=valid_inactive_recommendation.rel_id),
        )
        resp_message = resp.get_json()

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(resp_message, None, "Response should not have content")

        invalid_recommendation = \
        {
            "product-id": "abc",
            "related-product-id": "-10",
            "type-id": 1,
            "status": True
        }
        resp = self.app.get(
            "/recommendations/relationship",
            query_string=dict(product1=invalid_recommendation["product-id"],
            product2=invalid_recommendation["related-product-id"]),
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_recommendation = \
        {
            "product-id": "20",
            "related-product-id": "-10",
            "type-id": 1,
            "status": True
        }
        resp = self.app.get(
            "/recommendations/relationship",
            query_string=dict(product1=invalid_recommendation["product-id"],
            product2=invalid_recommendation["related-product-id"]),
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        valid_recommendation = self._create_recommendations(count=1)[0][0]
        does_not_exist_recommendation = \
        {
            "product-id": valid_recommendation.rel_id,
            "related-product-id": valid_recommendation.id,
            "type-id": 1,
            "status": True
        }
        resp = self.app.get(
            "/recommendations/relationship",
            query_string=dict
            (
            product1=does_not_exist_recommendation["product-id"],
            product2=does_not_exist_recommendation["related-product-id"]),
            )
        resp_message = resp.get_json()

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(resp_message, None, "Response should not have content")
        
    
    def test_get_active_related_products(self):
        r = Recommendation(id=1, rel_id=2, typeid=1, status=True)
        db.session.add(r)
        resp = self.app.get("/recommendations/active/1")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data[0]["ids"][0], 2)
        


######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    unittest.main()
