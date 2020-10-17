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
from service.model import Recommendation, db
from service import app

DATABASE_URI = os.getenv("DATABASE_URI", "postgres://postgres:postgres@localhost:5432/postgres")

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

    @classmethod
    def tearDownClass(cls):
        """ These run once after Test suite """
        pass

    def setUp(self):
        Recommendation.init_db(app)
        db.drop_all()  # clean up the last tests
        db.create_all()  # make our sqlalchemy tables

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_find_by_id_status(self):
        r = Recommendation(id=1, rel_id=2, typeid=1, status=True)
        db.session.add(r)
        rec = Recommendation.find_by_id_status(by_id=1, by_status=True)
        self.assertEqual(rec[0].rel_id, 2)
        self.assertEqual(rec[0].typeid, 1)



######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    unittest.main()

