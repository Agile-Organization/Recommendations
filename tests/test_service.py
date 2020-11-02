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
from service.service import init_db, internal_server_error
from .recommendation_factory import RecommendationFactory
from werkzeug.exceptions import NotFound

# Disable all but ciritcal erros suirng unittest
logging.disable(logging.CRITICAL)

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
        app.config['SQLALCHEMY_POOL_SIZE'] = 3

    @classmethod
    def tearDownClass(cls):
        """ Run once after all tests """

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

    def test_get_related_products(self):
        """ Get related products by id tests"""
        # Test for valid id
        recommendation = self._create_recommendations(count=200, by_status=True)

        resp = self.app.get\
            ("/recommendations/" + str(recommendation[0][0].id))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(isinstance(resp, object), True, "Received incorrect recommendation")

        if recommendation[0][0].typeid == 1:
            self.assertEqual(resp.get_json()[0]["ids"][0], recommendation[0][0].rel_id, "Received incorrect records")
        elif recommendation[0][0].typeid == 2:
            self.assertEqual(resp.get_json()[1]["ids"][0], recommendation[0][0].rel_id, "Received incorrect records")
        else:
            self.assertEqual(resp.get_json()[2]["ids"][0], recommendation[0][0].rel_id, "Received incorrect records")

        num_records = len(resp.get_json()[0]["ids"]) + len(resp.get_json()[1]["ids"]) + len(resp.get_json()[2]["ids"])

        self.assertEqual(num_records, 1, "Received incorrect records")

        self.assertTrue(resp.get_json()[0]["relation_id"] == recommendation[0][0].typeid or\
           resp.get_json()[1]["relation_id"] == recommendation[0][0].typeid or\
           resp.get_json()[2]["relation_id"] == recommendation[0][0].typeid)

        # Test for negative product id
        negative_product_id = -99
        resp = self.app.get("/recommendations/" + str(negative_product_id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # # Test for string product id
        string_product_id = "test"
        resp = self.app.get("/recommendations/" + str(string_product_id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # Test for non-exists product id
        none_exists_product_id = 999999
        resp = self.app.get("/recommendations/" + str(none_exists_product_id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_recommendation_relationship_type(self):
        """ Get recommendation relationship type for two products Tests"""
        valid_recommendation = self._create_recommendations(count=1)[0][0]
        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=valid_recommendation.id,
                               product2=valid_recommendation.rel_id)
             )
        new_recommendation = Recommendation()
        new_recommendation.deserialize(resp.get_json())

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(new_recommendation,
                         valid_recommendation,
                         "recommendations does not match")

        valid_inactive_recommendation = self._create_recommendations(count=1,\
                                                          by_status=False)[0][0]
        resp = self.app.get("/recommendations/relationship",
                            query_string=
                            dict(product1=valid_inactive_recommendation.id,
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
        resp = self.app.get("/recommendations/relationship",
                            query_string=
                            dict(product1=invalid_recommendation["product-id"],\
                        product2=invalid_recommendation["related-product-id"]),)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_recommendation = \
        {
            "product-id": "20",
            "related-product-id": "-10",
            "type-id": 1,
            "status": True
        }
        resp = self.app.get("/recommendations/relationship",
                            query_string=
                            dict(product1=invalid_recommendation["product-id"],\
                        product2=invalid_recommendation["related-product-id"]),)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        valid_recommendation = self._create_recommendations(count=1)[0][0]
        not_exist_rec = \
        {
            "product-id": valid_recommendation.rel_id,
            "related-product-id": valid_recommendation.id,
            "type-id": 1,
            "status": True
        }
        resp = self.app.get(
            "/recommendations/relationship",
            query_string=dict(product1=not_exist_rec["product-id"],
                              product2=not_exist_rec["related-product-id"]))
        resp_message = resp.get_json()

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(resp_message, None, "Response should not have content")


    def test_get_active_related_products(self):
        """ Get active recommendations Test """
        resp = self.app.get("/recommendations/active/{}".format(1))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        self._create_one_recommendation(by_id=1, by_rel_id=2, by_type=1)

        resp = self.app.get("/recommendations/active/{}".format(1))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data[0]["ids"][0], 2)

        self._create_one_recommendation(by_id=1, by_rel_id=3, by_type=2)
        self._create_one_recommendation(by_id=1, by_rel_id=4, by_type=3)

        resp = self.app.get("/recommendations/active/{}".format(1))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data[1]["ids"][0], 3)


    def test_get_related_products_with_type(self):
        """ Get recommendations by id and type Test """
        resp = self.app.get("/recommendations/{}/type/{}".format(1, 1))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        recommendation = self._create_one_recommendation(by_id=1, by_rel_id=2, by_type=1)

        resp = self.app.get("/recommendations/{}/type/{}".format(recommendation[0].id, recommendation[0].typeid))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["ids"][0], 2)
        self.assertTrue(data["status"][0])


    def test_update_recommendation_between_products(self):
        """ Update Recommendations Tests """
        recommendations = self._create_recommendations(count=2, by_status=True)
        new_typeid = {1: 2, 2: 3, 3: 1}

        old_recommendation = recommendations[0][0]

        new_recommendation = Recommendation()
        new_recommendation.id = old_recommendation.id
        new_recommendation.rel_id = old_recommendation.rel_id
        new_recommendation.typeid = new_typeid[old_recommendation.typeid]
        new_recommendation.status = True

        resp = self.app.put("/recommendations",
                            json=new_recommendation.serialize(),
                            content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(resp.get_json())

        resp = self.app.put("/recommendations",
                            json=new_recommendation.serialize(),
                            content_type="not/json")
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=old_recommendation.id,
                               product2=old_recommendation.rel_id)
             )
        updated_recommendation = Recommendation()
        updated_recommendation.deserialize(resp.get_json())

        self.assertEqual(updated_recommendation,
                         new_recommendation,
                         "recommendation was not updated")

        old_recommendation = recommendations[1][0]

        invalid_recommendation = {
            "product-id": "Wrong_id",
            "related-product-id": old_recommendation.rel_id,
            "type-id": new_typeid[old_recommendation.typeid],
            "status": True
        }

        resp = self.app.put("/recommendations",
                            json=invalid_recommendation,
                            content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=old_recommendation.id,
                               product2=old_recommendation.rel_id)
             )
        updated_recommendation = Recommendation()
        updated_recommendation.deserialize(resp.get_json())

        self.assertEqual(updated_recommendation,
                         old_recommendation,
                         "recommendation should not be updated")

        invalid_recommendation = {
            "product-id": "Wrong_id",
            "related-product-id": old_recommendation.rel_id,
            "type-id": new_typeid[old_recommendation.typeid],
            "status": True
        }

        resp = self.app.put("/recommendations",
                            json=invalid_recommendation,
                            content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=old_recommendation.id,
                               product2=old_recommendation.rel_id)
             )
        updated_recommendation = Recommendation()
        updated_recommendation.deserialize(resp.get_json())

        self.assertEqual(updated_recommendation,
                         old_recommendation,
                         "recommendation should not be updated")

        invalid_recommendation = {
            "product-id": old_recommendation.id,
            "related-product-id": "Wrong_id",
            "type-id": new_typeid[old_recommendation.typeid],
            "status": True
        }

        resp = self.app.put("/recommendations",
                            json=invalid_recommendation,
                            content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=old_recommendation.id,
                               product2=old_recommendation.rel_id)
             )
        updated_recommendation = Recommendation()
        updated_recommendation.deserialize(resp.get_json())

        self.assertEqual(updated_recommendation,
                         old_recommendation,
                         "recommendation should not be updated")

        invalid_recommendation = {
            "product-id": old_recommendation.id,
            "related-product-id": old_recommendation.rel_id,
            "type-id": 10,
            "status": True
        }

        resp = self.app.put("/recommendations",
                            json=invalid_recommendation,
                            content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=old_recommendation.id,
                               product2=old_recommendation.rel_id)
             )
        updated_recommendation = Recommendation()
        updated_recommendation.deserialize(resp.get_json())

        self.assertEqual(updated_recommendation,
                         old_recommendation,
                         "recommendation should not be updated")

        does_not_exist_recommendation = {
            "product-id": 50000,
            "related-product-id": old_recommendation.rel_id,
            "type-id": 2,
            "status": True
        }

        resp = self.app.put("/recommendations",
                            json=does_not_exist_recommendation,
                            content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=old_recommendation.id,
                               product2=old_recommendation.rel_id)
             )
        updated_recommendation = Recommendation()
        updated_recommendation.deserialize(resp.get_json())

        self.assertEqual(updated_recommendation,
                         old_recommendation,
                         "recommendation should not be updated")

        valid_recommendation = old_recommendation

        resp = self.app.put("/recommendations",
                            json=valid_recommendation.serialize(),
                            content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=old_recommendation.id,
                               product2=old_recommendation.rel_id)
             )
        updated_recommendation = Recommendation()
        updated_recommendation.deserialize(resp.get_json())

        self.assertEqual(updated_recommendation,
                         old_recommendation,
                         "recommendation should not be updated")

    
    def test_delete_all_by_product_id(self):
        """ Delete recommendation by valid product id """
        recommendations = self._create_recommendations(count=5, by_status=True)

        recommendation = recommendations[0][0]

        resp = self.app.delete("/recommendations/" + str(recommendation.id))

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(resp.get_json())

        resp = self.app.get\
            ("/recommendations/" + str(recommendation.id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        recommendation = recommendations[1][0]

        """ Delete recommendation by negative product id """
        invalid_id = -99
        resp = self.app.delete("/recommendations/" + str(invalid_id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        resp = self.app.get\
            ("/recommendations/" + str(recommendation.id))

        if recommendation.typeid == 1:
            self.assertEqual(resp.get_json()[0]["ids"][0], recommendation.rel_id, "Received incorrect records")
        elif recommendation.typeid == 2:
            self.assertEqual(resp.get_json()[1]["ids"][0], recommendation.rel_id, "Received incorrect records")
        else:
            self.assertEqual(resp.get_json()[2]["ids"][0], recommendation.rel_id, "Received incorrect records")

        """ Delete recommendation by string product id """
        text_id = "text"
        resp = self.app.delete("/recommendations/" + str(text_id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        resp = self.app.get\
            ("/recommendations/" + str(recommendation.id))

        if recommendation.typeid == 1:
            self.assertEqual(resp.get_json()[0]["ids"][0], recommendation.rel_id, "Received incorrect records")
        elif recommendation.typeid == 2:
            self.assertEqual(resp.get_json()[1]["ids"][0], recommendation.rel_id, "Received incorrect records")
        else:
            self.assertEqual(resp.get_json()[2]["ids"][0], recommendation.rel_id, "Received incorrect records")

        """ Delete recommendation by non-exists product id """
        non_exists_id = 999999
        resp = self.app.delete("/recommendations/" + str(non_exists_id))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        resp = self.app.get\
            ("/recommendations/" + str(recommendation.id))

        if recommendation.typeid == 1:
            self.assertEqual(resp.get_json()[0]["ids"][0], recommendation.rel_id, "Received incorrect records")
        elif recommendation.typeid == 2:
            self.assertEqual(resp.get_json()[1]["ids"][0], recommendation.rel_id, "Received incorrect records")
        else:
            self.assertEqual(resp.get_json()[2]["ids"][0], recommendation.rel_id, "Received incorrect records")


    def test_delete_recommendation_by_rel_id(self):
        
        recommendations = self._create_recommendations(count=10, by_status=True)

        recommendation = recommendations[0][0]

        """ Delete recommendation by valid product id and valid rel_id"""
        resp = self.app.delete("/recommendations/"
                               + str(recommendation.id)
                               + "?rel_id="
                               + str(recommendation.rel_id))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(resp.get_json())

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=recommendation.id,
                               product2=recommendation.rel_id)
             )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(resp.get_json())

        recommendation = recommendations[1][0]

        """ Delete recommendation by valid product id and non-exists rel_id"""
        resp = self.app.delete("/recommendations/"
                               + str(recommendation.id)
                               + "?rel_id="
                               + str(90000))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(resp.get_json())

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=recommendation.id,
                               product2=recommendation.rel_id)
             )

        returned_recommendation = Recommendation()
        returned_recommendation.deserialize(resp.get_json())
   
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(returned_recommendation,
                         recommendation,
                         "Recommendations should not be changed")

        """ Delete recommendation by valid product id and string rel_id"""
        resp = self.app.delete("/recommendations/"
                               + str(recommendation.id)
                               + "?rel_id="
                               + "abcd")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=recommendation.id,
                               product2=recommendation.rel_id)
             )

        returned_recommendation = Recommendation()
        returned_recommendation.deserialize(resp.get_json())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(returned_recommendation,
                         recommendation,
                         "Recommendations should not be changed")

        """ Delete recommendation by valid product id and negative rel_id"""
        resp = self.app.delete("/recommendations/"
                                + str(recommendation.id)
                                + "?rel_id="
                                + "-999")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        """ Delete recommendation by string product id and valid rel_id"""
        resp = self.app.delete("/recommendations/"
                               + "abcd"
                               + "?rel_id="
                               + str(recommendation.rel_id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=recommendation.id,
                               product2=recommendation.rel_id)
             )

        returned_recommendation = Recommendation()
        returned_recommendation.deserialize(resp.get_json())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(returned_recommendation,
                         recommendation,
                         "Recommendations should not be changed")


    def test_delete_all_products_by_type_id(self):
        """ Delete recommendation by product id and type_id"""
        recommendations = self._create_recommendations(count=5, by_status=True)

        recommendation = recommendations[0][0]
  
        # Delete recommendation by valid product id and valid type_id
        resp = self.app.delete("/recommendations/" 
                                + str(recommendation.id) 
                                + "?type_id=" 
                                + str(recommendation.typeid))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(resp.get_json())

        resp = self.app.get("/recommendations/" 
                        + str(recommendation.id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        recommendation = recommendations[1][0]
        # Delete recommendation by valid product id and string type_id
        resp = self.app.delete("/recommendations/" 
                            + str(recommendation.id) 
                            + "?type_id=" 
                            + str("TEST"))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Delete recommendation by valid product id and invalid type_id
        resp = self.app.delete("/recommendations/" 
                            + str(recommendation.id) 
                            + "?type_id=" + str(5))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Delete recommendation by valid product id, valid rel_id and valid type_id
        resp = self.app.delete("/recommendations/"
                               + str(recommendation.id)
                               + "?rel_id="
                               + str(recommendation.rel_id)
                               + "&type_id="
                               + str(recommendation.typeid))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(resp.get_json())

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=recommendation.id,
                               product2=recommendation.rel_id)
             )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(resp.get_json())

        recommendation = recommendations[2][0]
        
        # Delete recommendation by valid product id, valid rel_id and invalid type_id
        resp = self.app.delete("/recommendations/"
                               + str(recommendation.id)
                               + "?rel_id="
                               + str(recommendation.rel_id)
                               + "&type_id="
                               + str(10))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=recommendation.id,
                               product2=recommendation.rel_id)
             )
   
        returned_recommendation = Recommendation()
        returned_recommendation.deserialize(resp.get_json())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(returned_recommendation,
                         recommendation,
                         "Recommendations should not be changed")

        # Delete recommendation by valid product id, invalid rel_id and valid type_id
        resp = self.app.delete("/recommendations/"
                               + str(recommendation.id)
                               + "?rel_id="
                               + str(-999)
                               + "&type_id="
                               + str(recommendation.typeid))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        resp = self.app.get\
            ("/recommendations/relationship",
             query_string=dict(product1=recommendation.id,
                               product2=recommendation.rel_id)
             )

        returned_recommendation = Recommendation()
        returned_recommendation.deserialize(resp.get_json())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(returned_recommendation,
                         recommendation,
                         "Recommendations should not be changed")


    def test_internal_server_error(self):
        """ Test internal service error handler """
        message = "Test error message"
        resp = internal_server_error(message)
        self.assertEqual(resp[1], status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(resp[0].get_json()["message"], message)

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
            resp = self.app.post("/recommendations",
                                 json=test_recommendation.serialize(),
                                 content_type="application/json")
            recommendations.append([test_recommendation,
                                    resp.headers.get("Location", None)])
        return recommendations

    def _create_one_recommendation(self, by_id, by_rel_id, by_type, by_status=True):
        """ Create one specific recommendation for testing """
        test_recommendation = Recommendation(id=by_id,
                                             rel_id=by_rel_id,
                                             typeid=by_type,
                                             status= by_status)
        resp = self.app.post("/recommendations",
                             json=test_recommendation.serialize(),
                             content_type="application/json")
        return [test_recommendation, resp.headers.get("Location", None)]

    def test_create_recommendations(self):
        """ Create recommendations Tests"""
        recommendations = self._create_recommendations(count=10, by_status=True)
        self.assertEqual(len(recommendations), 10)
        for recommendation, location in recommendations:
            self.assertTrue(recommendation.status)
            self.assertIsNotNone(location)

        recs = self._create_recommendations(count=10, by_status=False)
        self.assertEqual(len(recs), 10)
        for recommendation, location in recs:
            self.assertFalse(recommendation.status)
            self.assertIsNotNone(location)

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
