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
import json
import logging
from flask import request
from flask_api import status
from service.model import Recommendation, db
from service import app
from service.service import init_db, generate_apikey, data_load, internal_server_error
from .recommendation_factory import RecommendationFactory
from werkzeug.exceptions import NotFound

# Disable all but ciritcal erros suirng unittest
logging.disable(logging.CRITICAL)

# Get configuration from environment
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgres://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/api/recommendations"
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
class TestRecommendationService(unittest.TestCase):
    """ Recommendation Server Tests """

    @classmethod
    def setUpClass(cls):
        """ Run once before all tests """
        app.debug = False
        app.testing = True
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        api_key = generate_apikey()
        app.config["API_KEY"] = api_key
        init_db()

    @classmethod
    def tearDownClass(cls):
        """ Run once after all tests """
        db.session.close()  # <-- Explicitly close the connection after all tests

    def setUp(self):
        """ Runs before each test """
        db.drop_all()  # clean up the last tests
        db.create_all()  # create new tables
        self.app = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_heartbeat(self):
        """ Test heartbeat call """
        resp = self.app.get("/healthcheck")

        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual("Healthy", resp.get_json()["message"])

    def test_index(self):
        """ Test index call """
        resp = self.app.get("/")
        data = resp.get_json()

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(data)

    def test_internal_server_error(self):
        """ Test internal service error handler """
        message = "Test error message"
        resp = internal_server_error(message)
        self.assertEqual(resp[1], status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(resp[0].get_json()["message"], message)

    def test_get_recommendation(self):
        """ Get Recommendation Tests"""
        recommendation = self._create_recommendations(1)[0]

        # Test Case 1
        resp = self.app.get(
            BASE_URL
            + "/"
            + str(recommendation.product_id)
            + "/"
            + str(recommendation.related_product_id)
        )
        print(resp.get_json())
        returned_recommendation = Recommendation()
        returned_recommendation.deserialize(resp.get_json())

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(recommendation, returned_recommendation)

        # Test Case 2
        resp = self.app.get(
            BASE_URL + "/" + str(recommendation.product_id) + "/" + str(99999)
        )

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # Test Case 3
        resp = self.app.get(
            BASE_URL + "/" + str(recommendation.product_id) + "/" + str(-99999)
        )

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # Test Case 4
        resp = self.app.get(BASE_URL + "/" + str(recommendation.product_id) + "/abcd")

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    ######################################################################
    #   HELPER FUNCTIONS
    ######################################################################
    def _create_recommendations(self, count, by_status=True):
        """ Factory method to create Recommendations in bulk count <= 10000 """
        if not isinstance(count, int):
            return []
        if not isinstance(by_status, bool):
            return []
        recommendations = []
        for _ in range(count):
            test_recommendation = RecommendationFactory()
            test_recommendation.status = by_status
            data_load(test_recommendation.serialize())
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
        data_load(test_recommendation.serialize())
        return [test_recommendation]


######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    unittest.main()
