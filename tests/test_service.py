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
PlaceHolderClassName API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN
"""

import unittest
import os
import logging
from service.models import PlaceHolderClassName, db
from service import app
from service.routes import init_db

# Disable all but ciritcal erros suirng unittest
logging.disable(logging.CRITICAL)

DATABASE_URI = os.getenv("DATABASE_URI", "postgres:///../db/test.db")

######################################################################
#  T E S T   C A S E S
######################################################################
class TestPlaceHolderClassNameService(unittest.TestCase):
    """ PlaceHolderClassName Server Tests """

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


######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    unittest.main()
