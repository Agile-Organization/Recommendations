# Copyright 2016, 2017 Agile Organization All Rights Reserved.
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
Test cases for PlaceHolderClassName Model

Test cases can be run with:
  nosetests
  coverage report -m
"""

import unittest
import os
from service.models import PlaceHolderClassName, db
from service import app

DATABASE_URI = os.getenv("DATABASE_URI", "postgres:///../db/test.db")

######################################################################
#  T E S T   C A S E S
######################################################################
class TestPlaceHolderClassName(unittest.TestCase):
    """ Test Cases for PlaceHolderClassName """

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
        PlaceHolderClassName.init_db(app)
        db.drop_all()  # clean up the last tests
        db.create_all()  # make our sqlalchemy tables

    def tearDown(self):
        db.session.remove()
        db.drop_all()


######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    unittest.main()
