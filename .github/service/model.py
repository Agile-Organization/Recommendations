"""
Models for Recommendations Service

All of the models are stored in this module

Models
-------
Recommendations - The recommendations resource is a representation a product recommendation based on another product.

Atttibutes:
-------
productA id (int) - a unique number which indicates a product
productB id (int) - a unique number which indicates the recommended product of product A
relationship type id (int) - the numbers which indicates the products' realationship: 0 - accessory, 1 - up-sells, 2 - cross-sells
active status (boolean) - whether this recommendation pair is actived or not. 

"""

import logging
from flask_sqlalchemy import SQLAlchemy

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """ Used for an data validation errors when deserializing """
    pass

class Recommendation(db.Model):
    """
    Class that represents a Recommendation

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    logger = logging.getLogger(__name__)
    app = None

    ##################################################
    # Table Schema
    ##################################################

    idA = db.Column(db.Integer, primary_key=True)
    idB = db.Column(db.Integer, primary_key=True)
    typeid = db.Column(db.Integer, primary_key = True)
    status = db.Column(db.Boolean())

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return "<Recommendation %d %d %d>" % (self.idA, self.idB, self.typeid)

    def create(self):
        """ 
        Creates a recommendation pair to the database
        """ 
        logger.info("Creating %s", self.name)
        self.id = None  # id must be none to generate next primary key
        db.session.add(self)
        db.session.commit()

    def save(self):
        """
        Updates a recommendation to the database
        """
        logger.info("Saving %s", self.idA)
        db.session.commit()
    
    # todo. 
    # As we discuss, delete methods should have three different ways.
    def delete(self):
        """ Removes all recommendation from the data store by using product id"""
        logger.info("Deleting %s", self.idA)
        db.session.delete(self)
        db.session.commit()

    # todo. 
    # I suppose here should be the GET method.
    # As we discussed, we may need four different methods to implement it.
    def serialize(self):
        """ Serializes a recommendation into a dictionary """
        return {
            "productA-id": self.idA,
            "productB-id": self.idB,
            "type-id": self.typeid
        }

    def deserialize(self, data):
        """
        Deserializes a recommendation from a dictionary
        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.idA = data["productA-id"]
        except KeyError as error:
            raise DataValidationError("Invalid recommendation: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError(
                "Invalid recommendation: body of request contained" "bad or no data"
            )
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def init_db(cls, app):
        """ Initializes the database session """
        logger.info("Initializing database")
        cls.app = app
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    def all(cls):
        """ Returns all of the recommendations in the database """
        logger.info("Processing all recommendations")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """ Finds a recommendation by it's ID """
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.get(by_id)

    @classmethod
    def find_or_404(cls, by_id):
        """ Find a recommendation by it's id """
        logger.info("Processing lookup or 404 for id %s ...", by_id)
        return cls.query.get_or_404(by_id)

    # todo
    # This method is searching by name, however, as we discuss, we don't need name in a recommendation.

    # @classmethod
    # def find_by_name(cls, name):
    #     """ Returns all recommendations with the given name
    #     Args:
    #         name (string): the name of the recommendations you want to match
    #     """
    #     logger.info("Processing name query for %s ...", name)
    #     return cls.query.filter(cls.name == name)