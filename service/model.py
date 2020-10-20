"""
Models for Recommendations Service

All of the models are stored in this module

Models
-------
Recommendations - The recommendations resource is a representation a product recommendation based on another product.

Attributes:
-------
product id (int) - a unique number which indicates a product
related product id (int) - a unique number which indicates the recommended product of product A
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

    id = db.Column(db.Integer, primary_key=True)
    rel_id = db.Column(db.Integer, primary_key=True)
    typeid = db.Column(db.Integer)
    status = db.Column(db.Boolean())

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return "<Recommendation %d %d %d>" % (self.id, self.rel_id, self.typeid)

    def __eq__(self, other):
        return self.id == other.id \
               and self.rel_id == other.rel_id \
               and self.typeid == other.typeid \
               and self.status == other.status

    def create(self):
        """
        Creates a recommendation pair to the database
        """
        self.logger.info("Creating recommendation from ID : [%s] to ID : [%s]", self.id, self.rel_id)
        if not 1 <= self.typeid <= 3:
            raise DataValidationError("Invalid typeid; cannot be created")
        db.session.add(self)
        db.session.commit()

    def save(self):
        """
        Updates a recommendation to the database
        """
        self.logger.info("Saving %s", self.id)
        if not 1 <= self.typeid <= 3:
            raise DataValidationError("Invalid typeid; cannot be saved")
        db.session.commit()

    def delete(self):
        """ Removes all recommendation from the data store by using product id"""
        self.logger.info("Deleting %s", self.id)
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        """ Serializes a recommendation into a dictionary """
        return {
            "product-id": self.id,
            "related-product-id": self.rel_id,
            "type-id": self.typeid,
            "status": self.status
        }

    def deserialize(self, data):
        """
        Deserializes a recommendation from a dictionary
        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            if not 1 <= data["type-id"] <= 3:
                raise DataValidationError("Invalid recommendation:"\
                                          " type_id outside [1,3]")
            self.id = data["product-id"]
            self.rel_id  = data["related-product-id"]
            self.typeid = data["type-id"]
            self.status = data["status"] if "status" in data else True
        except KeyError as error:
            raise DataValidationError("Invalid recommendation: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError(
                "Invalid recommendation: body of request contained" "bad or no data"
            )
        except Exception as error:
            raise DataValidationError("Invalid recommendation: body of request"\
                                      " contained" "bad or no data")
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def init_db(cls, app):
        """ Initializes the database session """
        app.logger.info("Initializing database")
        cls.app = app
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    def all(cls):
        """ Returns all of the recommendations in the database """
        cls.logger.info("Processing all recommendations")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """ Finds a recommendation by it's ID """
        cls.logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.get(by_id)

    @classmethod
    def find_or_404(cls, by_id):
        """ Find a recommendation by it's id """
        cls.logger.info("Processing lookup or 404 for id %s ...", by_id)
        return cls.query.get_or_404(by_id)

    @classmethod
    def find_by_id_status(cls, by_id: int, by_status=True):
        """ Find active recommendations of a product [id] """
        cls.logger.info("Processing lookup for id %s with status %s", by_id, by_status)
        return cls.query.filter(cls.id==by_id, cls.status==by_status)

    @classmethod
    def find_by_id_and_typeid(cls, by_id: int, by_typeid: int):
        """ Find all the recommendations of a product by using a typeid"""
        cls.logger.info("Processing lookup for id %s with type id %s", by_id, by_typeid)
        return cls.query.filter(cls.id == by_id, cls.typeid == by_typeid)

    @classmethod
    def find_recommendation(cls, by_id: int, by_rel_id: int, by_status=True):
        """ Find recommendation relationship for product and rel_product
        Args:
            by_id (int): A integer representing the product id
            by_rel_id (int): A integer representing the related product id
            status (bool): A boolean representing the status of recommendation
        Returns:
            The recommendation if exists
        """
        if not by_id or not isinstance(by_id, int):
            raise TypeError("by_id is not of type int")
        if not by_rel_id or not isinstance(by_rel_id, int):
            raise TypeError("by_rel_id is not of type int")
        if not isinstance(by_status, bool):
            raise TypeError("by_status is not of type bool")

        cls.logger.info("Processing lookup for id %s with"\
                        " rel_id %s and status %s", by_id, by_rel_id, by_status)
        return cls.query.filter(cls.id == by_id,
                                cls.rel_id == by_rel_id, cls.status == by_status)

    @classmethod
    def check_if_product_exists(cls, by_id: int, by_status=True):
        """ Check if the product exists in the database
        Args:
            by_id (int): A integer representing the product id
            by_status (bool): A boolean representing the recommendation status
        Returns:
            True if the product exists in either id column
            or rel_id column else False
        """
        if not by_id or not isinstance(by_id, int):
            raise TypeError("by_id is not of type int")
        if not isinstance(by_status, bool):
            raise TypeError("by_status is not of type bool")

        cls.logger.info("Processing lookup for id %s with status %s",\
                                                            by_id, by_status)
        return cls.query.filter((cls.id == by_id) | (cls.rel_id == by_id),
                                cls.status == by_status).first() is not None
