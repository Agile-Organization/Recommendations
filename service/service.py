"""
Recommendations Service

Initial service file for setting up recommendations controllers. 
File created based on template.
Will add more routes in the future for additional API endpoints.
"""

import os
import sys
import logging
from flask import Flask, jsonify, request, url_for, make_response, abort
from flask_api import status  # HTTP Status Codes
from werkzeug.exceptions import NotFound

# SQLAlchemy supports a variety of backends including SQLite, MySQL, and PostgreSQL
from flask_sqlalchemy import SQLAlchemy
from service.models import Recommendation, DataValidationError

# Import Flask application
from . import app

######################################################################
# HELPER CLASSES
######################################################################
class RelatedProducts:
    def __init__(self, typeid, active_product_list, inactive_product_list):
        self.relationship_id = typeid
        self.ids = active_product_list
        self.inactive_ids = inactive_product_list

######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """ Root URL response """
    return "Some useful information in json format about the recommendations service", status.HTTP_200_OK

######################################################################
# QUERY RELATED PRODUCTS BY ID
######################################################################
@app.route("/recommendations/<int:id>", methods=["GET"])
def get_related_products(id):
    """
    Retrieve all related products by providing a product id
    returns a list of 3 objects, showing a list of active ids and inactive ids for each realationship type
    [
        {
            relationship-id: 1,
            ids: [id1, id2, id3, ...],
            inactive-ids: [id10, id20, id30, ...]
        },
        {
            relationship-id: 2,
            ids: [id4, id5, id6, ...],
            inactive-ids: [id40, id50, id60, ...]
        },
        {
            relationship-id: 3,
            ids: [id7, id8, id9, ...],
            inactive-ids: [id70, id80, id90, ...]
        }
    ]
    """
    app.logger.info("Request for related products with id: %s", id)
    products = Recommendation.find(id) # need to replace find method with actual function name from model file
    
    if not products:
        raise NotFound("Product with id '{}' was not found.".format(id))
    
    # assume model returns records in format of: [{id: 1, rel_id: 2, typeid: 1, status: true}]
    relationships = []
    type_1_active, type_1_inactive = [], []
    type_2_active, type_2_inactive = [], []
    type_3_active, type_3_inactive = [], []

    for p in products:
        if p.typeid == 1:
            type_1_active.append(p.rel_id) if p.status else type_1_inactive.append(p.rel_id)
        elif p.typeid == 2:
            type_2_active.append(p.rel_id) if p.status else type_2_inactive.append(p.rel_id)
        else:
            type_3_active.append(p.rel_id) if p.status else type_3_inactive.append(p.rel_id)

    relationships.append(RelatedProducts(1, type_1_active, type_1_inactive))
    relationships.append(RelatedProducts(2, type_2_active, type_2_inactive))
    relationships.append(RelatedProducts(3, type_3_active, type_3_inactive))

    return make_response(jsonify(relationships.serialize()), status.HTTP_200_OK)


######################################################################
# Error Handlers
######################################################################
@app.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles Value Errors from bad data """
    return bad_request(error)


@app.errorhandler(status.HTTP_400_BAD_REQUEST)
def bad_request(error):
    """ Handles bad reuests with 400_BAD_REQUEST """
    app.logger.warning(str(error))
    return (
        jsonify(
            status=status.HTTP_400_BAD_REQUEST, error="Bad Request", message=str(error)
        ),
        status.HTTP_400_BAD_REQUEST,
    )


@app.errorhandler(status.HTTP_404_NOT_FOUND)
def not_found(error):
    """ Handles resources not found with 404_NOT_FOUND """
    app.logger.warning(str(error))
    return (
        jsonify(
            status=status.HTTP_404_NOT_FOUND, error="Not Found", message=str(error)
        ),
        status.HTTP_404_NOT_FOUND,
    )


@app.errorhandler(status.HTTP_405_METHOD_NOT_ALLOWED)
def method_not_supported(error):
    """ Handles unsuppoted HTTP methods with 405_METHOD_NOT_SUPPORTED """
    app.logger.warning(str(error))
    return (
        jsonify(
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
            error="Method not Allowed",
            message=str(error),
        ),
        status.HTTP_405_METHOD_NOT_ALLOWED,
    )


@app.errorhandler(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
def mediatype_not_supported(error):
    """ Handles unsuppoted media requests with 415_UNSUPPORTED_MEDIA_TYPE """
    app.logger.warning(str(error))
    return (
        jsonify(
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            error="Unsupported media type",
            message=str(error),
        ),
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    )


@app.errorhandler(status.HTTP_500_INTERNAL_SERVER_ERROR)
def internal_server_error(error):
    """ Handles unexpected server error with 500_SERVER_ERROR """
    app.logger.error(str(error))
    return (
        jsonify(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=str(error),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################

def init_db():
    """ Initialies the SQLAlchemy app """
    global app
    Recommendation.init_db(app)


def check_content_type(content_type):
    """ Checks that the media type is correct """
    if request.headers["Content-Type"] == content_type:
        return
    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(415, "Content-Type must be {}".format(content_type))
    
