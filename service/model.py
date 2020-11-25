"""
Models for Recommendations Service

All of the models are stored in this module

Models
-------
Recommendations - The recommendations resource is a representation a
product recommendation based on another product.

Attributes:
-------
product id (int) - a unique number which indicates a product
related product id (int) - a unique number which indicates the recommended
product of product A relationship type id (int) - the numbers which indicates
the products' realationship: 1 - accessory, 2 - up-sells, 3 - cross-sells
active status (boolean) - whether this recommendation pair is actived or not.

"""

import os
import logging
from flask_sqlalchemy import SQLAlchemy

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """ Used for an data validation errors when deserializing """

    def __init__(self, message):
        super().__init__(message)


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

    product_id = db.Column(db.Integer, primary_key=True)
    related_product_id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer)
    status = db.Column(db.Boolean())

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return "<Recommendation %d %d %d>" % (
            self.product_id,
            self.related_product_id,
            self.type_id,
        )

    def __eq__(self, other):
        return (
            self.product_id == other.product_id
            and self.related_product_id == other.related_product_id
            and self.type_id == other.type_id
            and self.status == other.status
        )

    def create(self):
        """
        Creates a recommendation pair to the database
        """
        self.logger.info(
            "Creating recommendation from product_id : [%s] to product_id : [%s]",
            self.product_id,
            self.related_product_id,
        )
        if not 1 <= self.type_id <= 3:
            raise DataValidationError("Invalid type_id; cannot be created")
        db.session.add(self)
        db.session.commit()

    def save(self):
        """
        Updates a recommendation to the database
        """
        self.logger.info("Saving %s", self.product_id)
        if not 1 <= self.type_id <= 3:
            raise DataValidationError("Invalid type_id; cannot be saved")
        db.session.commit()

    def delete(self):
        """ Removes all recommendation from the data store by using product product_id"""
        self.logger.info("Deleting %s", self.product_id)
        db.session.delete(self)
        db.session.commit()

    def serialize(self):
        """ Serializes a recommendation into a dictionary """
        return {
            "product-id": self.product_id,
            "related-product-id": self.related_product_id,
            "type-id": self.type_id,
            "status": self.status,
        }

    def deserialize(self, data):
        """
        Deserializes a recommendation from a dictionary
        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            if not isinstance(data["type-id"], int):
                raise DataValidationError(
                    "Invalid recommendation:" " type_id outside [1,3]"
                )
            if not isinstance(data["product-id"], int):
                raise DataValidationError("by_id is not of type int")
            if not isinstance(data["related-product-id"], int):
                raise DataValidationError("by_rel_id is not of type int")
            if not isinstance(data["status"], bool):
                raise DataValidationError("by_status is not of type bool")
            if not 1 <= data["type-id"] <= 3:
                raise DataValidationError(
                    "Invalid recommendation:" " type_id outside [1,3]"
                )

            self.product_id = data["product-id"]
            self.related_product_id = data["related-product-id"]
            self.type_id = data["type-id"]
            self.status = data["status"]
        except KeyError as error:
            raise DataValidationError(
                "Invalid recommendation: missing " + error.args[0]
            )
        except DataValidationError as error:
            raise DataValidationError(
                "Invalid recommendation: body of request"
                " contained"
                "bad or no data" + str(error)
            )
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
        """ Finds a recommendation by it's product_id """
        cls.logger.info("Processing lookup for product_id %s ...", by_id)
        return cls.query.filter(cls.product_id == by_id)

    @classmethod
    def find_by_rel_id(cls, by_rel_id):
        "Finds a recommendation by it's related_product_id"
        cls.logger.info("Processing lookup for related_product_id %s ...", by_rel_id)
        return cls.query.filter(cls.related_product_id==by_rel_id)

    @classmethod
    def find_by_type_id(cls, by_type_id):
        """ Finds a recommendation by it's type_id """
        if not by_type_id or not isinstance(by_type_id, int):
            raise TypeError("by_type is not of type int")
        if not 1 <= by_type_id <= 3:
            raise DataValidationError("Invalid recommendation: type_id outside [1,3]")

        cls.logger.info("Processing lookup for type_id %s ...", by_type_id)
        return cls.query.filter(cls.type_id == by_type_id)

    @classmethod
    def find_by_status(cls, by_status):
        """ Finds a recommendation by it's status """
        if not isinstance(by_status, bool):
            raise TypeError("by_status is not of type bool")

        cls.logger.info("Processing lookup for status %s ...", by_status)
        return cls.query.filter(cls.status == by_status)

    @classmethod
    def find_by_type_id_status(cls, by_type_id, by_status):
        """ Finds a recommendation by it's type_id """
        if not by_type_id or not isinstance(by_type_id, int):
            raise TypeError("by_type is not of type int")
        if not 1 <= by_type_id <= 3:
            raise DataValidationError("Invalid recommendation: type_id outside [1,3]")
        if not isinstance(by_status, bool):
            raise TypeError("by_status is not of type bool")

        cls.logger.info(
            "Processing lookup for type_id %s  and status %s ...", by_type_id, by_status
        )
        return cls.query.filter(cls.type_id == by_type_id, cls.status == by_status)

    @classmethod
    def find_by_id_relid(cls, by_id, by_rel_id):
        """ Find a unique recommendation by product_id and rel_product_id """
        if not by_id or not isinstance(by_id, int):
            raise TypeError("by_id is not of type int")
        if not by_rel_id or not isinstance(by_rel_id, int):
            raise TypeError("by_rel_id is not of type int")

        cls.logger.info(
            "Processing lookup for product_id %s with rel product_id %s ...",
            by_id,
            by_rel_id,
        )
        return cls.query.filter(
            cls.product_id == by_id, cls.related_product_id == by_rel_id
        )

    @classmethod
    def find_by_id_status(cls, by_id: int, by_status):
        """ Find [status: active/inactive] recommendations of a [product: product_id] """
        if not by_id or not isinstance(by_id, int):
            raise TypeError("by_id is not of type int")
        if not isinstance(by_status, bool):
            raise TypeError("by_status is not of type bool")

        cls.logger.info(
            "Processing lookup for product_id %s with status %s", by_id, by_status
        )
        return cls.query.filter(cls.product_id == by_id, cls.status == by_status)

    @classmethod
    def find_by_id_type(cls, by_id: int, by_type: int):
        """ Find recommendations of a [product: product_id] with [type: type_id] """
        if not by_id or not isinstance(by_id, int):
            raise TypeError("by_id is not of type int")
        if not by_type or not isinstance(by_type, int):
            raise TypeError("by_type is not of type int")
        if not 1 <= by_type <= 3:
            raise DataValidationError("Invalid recommendation: type_id outside [1,3]")

        cls.logger.info(
            "Processing lookup for product_id %s with type_id %s", by_id, by_type
        )
        return cls.query.filter(cls.product_id == by_id, cls.type_id == by_type)

    @classmethod
    def find_by_id_type_status(cls, by_id: int, by_type: int, by_status):
        """ Find recommendations of a [product: product_id] with [type: type_id] and [active status: status]"""
        if not by_id or not isinstance(by_id, int):
            raise TypeError("by_id is not of type int")
        if not by_type or not isinstance(by_type, int):
            raise TypeError("by_type is not of type int")
        if not 1 <= by_type <= 3:
            raise DataValidationError("Invalid recommendation: type_id outside [1,3]")
        if not isinstance(by_status, bool):
            raise TypeError("by_status is not of type bool")

        cls.logger.info(
            "Processing lookup for product_id %s with type_id %s and status %r",
            by_id,
            by_type,
            by_status,
        )
        return cls.query.filter(
            cls.product_id == by_id, cls.type_id == by_type, cls.status == by_status
        )

    @classmethod
    def find_by_relid_status(cls, by_rel_id: int, by_status):
        """ Find [status: active/inactive] recommendations of a [related product: related_product_id] """
        if not by_rel_id or not isinstance(by_rel_id, int):
            raise TypeError("by_rel_id is not of type int")
        if not isinstance(by_status, bool):
            raise TypeError("by_status is not of type bool")

        cls.logger.info("Processing lookup for related_product_id %s with status %s", by_rel_id, by_status)
        return cls.query.filter(cls.related_product_id==by_rel_id, cls.status==by_status)

    @classmethod
    def find_by_relid_type(cls, by_rel_id: int, by_type: int):
        """ Find recommendations of a [related product: related_product_id] with [type: type_id] """
        if not by_rel_id or not isinstance(by_rel_id, int):
            raise TypeError("by_rel_id is not of type int")
        if not by_type or not isinstance(by_type, int):
            raise TypeError("by_type is not of type int")
        if not 1 <= by_type <= 3:
            raise DataValidationError("Invalid recommendation: type_id outside [1,3]")

        cls.logger.info("Processing lookup for related_product_id %s with type_id %s", by_rel_id, by_type)
        return cls.query.filter(cls.related_product_id==by_rel_id, cls.type_id==by_type)

    @classmethod
    def find_by_relid_type_status(cls, by_rel_id:int, by_type:int, by_status: bool):
        "Find recommendations of a [related product: related_product_id] with [type: type_id] and [active status: status] "
        if not by_rel_id or not isinstance(by_rel_id, int):
            raise TypeError("by_rel_id is not of type int")
        if not by_type or not isinstance(by_type, int):
            raise TypeError("by_type is not of type int")
        if not 1 <= by_type <= 3:
            raise DataValidationError("Invalid recommendation: type_id outside [1,3]")
        if not isinstance(by_status, bool):
            raise TypeError("by_status is not of type bool")
        
        cls.logger.info("Processing lookup for related_product_id %s with type_id %s and status %r", by_rel_id, by_type, by_status)
        return cls.query.filter(cls.related_product_id==by_rel_id, cls.type_id==by_type, cls.status==by_status)

    @classmethod
    def find_recommendation(cls, by_id: int, by_rel_id: int, by_status=True):
        """Find recommendation relationship for product and rel_product
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

        cls.logger.info(
            "Processing lookup for product_id %s with"
            " related_product_id %s and status %s",
            by_id,
            by_rel_id,
            by_status,
        )
        return cls.query.filter(
            cls.product_id == by_id,
            cls.related_product_id == by_rel_id,
            cls.status == by_status,
        )

    @classmethod
    def check_if_product_exists(cls, by_id: int, by_status=True):
        """Check if the product exists in the database
        Args:
            by_id (int): A integer representing the product id
            by_status (bool): A boolean representing the recommendation status
        Returns:
            True if the product exists in either product_id column
            or related_product_id column else False
        """
        if not by_id or not isinstance(by_id, int):
            raise TypeError("by_id is not of type int")
        if not isinstance(by_status, bool):
            raise TypeError("by_status is not of type bool")

        cls.logger.info(
            "Processing lookup for product_id %s with status %s", by_id, by_status
        )
        return (
            cls.query.filter(
                (cls.product_id == by_id) | (cls.related_product_id == by_id),
                cls.status == by_status,
            ).first()
            is not None
        )
