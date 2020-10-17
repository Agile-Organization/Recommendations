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
from service.model import Recommendation, db
from service import app
from service.service import init_db
from .recommendation_factory import RecommendationFactory

# Disable all but ciritcal erros suirng unittest
logging.disable(logging.CRITICAL)

DATABASE_URI = os.getenv("DATABASE_URI", "postgres:///../db/test.db")

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
        self.assertEqual(data["name"], "Customer REST API Service")

    def _create_recommendations(self, count):
        """ Factory method to create Recommendations in bulk count <= 10000 """
        recommendations = []
        for _ in range(count):
            test_recommendation = RecommendationFactory()
            resp = self.app.post(
                "/recommendations",
                json=test_recommendation.serialize(),
                content_type="application/json"
            )
            self.assertEqual(
                resp.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Recommendation"
            )
            recommendations.append(test_recommendation)
        return recommendations

    def test_create_recommendations(self):
        """ Create a new Recommendation Factory """
        test_recommendation = RecommendationFactory()
        resp = self.app.post(
            "/recommendations",
            json=test_recommendation.serialize(),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        location = resp.headers.get("Location", None)
        self.assertTrue(location != None)

        new_recommendation = Recommendation()
        new_recommendation.deserialize(request.get_json())

        self.assertEqual(
            new_recommendation.id,
            test_recommendation.id,
            "id does not match"
        )
        self.assertEqual(
            new_recommendation.rel_id,
            test_recommendation.rel_id,
            "related-product-id does not match"
        )
        self.assertEqual(
            new_recommendation.typeid,
            test_recommendation.typeid,
            "type-id does not match"
        )
        self.assertEqual(
            new_recommendation.status,
            test_recommendation.status,
            "status does not match"
        )

        resp = self.app.get(location, content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_recommendation = Recommendation()
        new_recommendation.deserialize(request.get_json())

        self.assertEqual(
            new_recommendation.id,
            test_recommendation.id,
            "id does not match"
        )
        self.assertEqual(
            new_recommendation.rel_id,
            test_recommendation.rel_id,
            "related-product-id does not match"
        )
        self.assertEqual(
            new_recommendation.typeid,
            test_recommendation.typeid,
            "type-id does not match"
        )
        self.assertEqual(
            new_recommendation.status,
            test_recommendation.status,
            "status does not match"
        )

    def test_get_recommendation_relationship_type(self):
        """ Get recommendation relationship type for two products """
        valid_recommendation = self._create_recommendations(1)[0]

        resp = self.app.get(
            "/recommendations/relationship",
            query_string=dict(product1=valid_recommendation["id"],
            product2=valid_recommendation["related-product-id"]),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        new_recommendation = resp.get_json()

        self.assertEqual(
        new_recommendation["related-product-id"],
        valid_recommendation["related-product-id"],
        "related product id does not match"
        )

        invalid_recommendation = \
        {
            "product-id": "abc",
            "related-product-id": "-10",
            "type-id": 1,
            "status": True
        }

        resp = self.app.get(
            "/recommendations/relationship",
            query_string=dict(product1=invalid_recommendation["id"],
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
            query_string=dict(product1=invalid_recommendation["id"],
            product2=invalid_recommendation["related-product-id"]),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        does_not_exist_recommendation = \
        {
            "product-id": "11000",
            "related-product-id": "12000",
            "type-id": 1,
            "status": True
        }

        resp = self.app.get(
            "/recommendations/relationship",
            query_string=dict(product1=does_not_exist_recommendation["id"],
            product2=does_not_exist_recommendation["related-product-id"]),
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        resp_message = resp.get_json()
        self.assertEqual(resp_message, '', "Response should not have content")


######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    unittest.main()
