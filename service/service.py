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
from service.model import Recommendation, DataValidationError

# Import Flask application
from . import app

######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """ Root URL response """
    return "Some useful information in json format about the recommendations service", status.HTTP_200_OK


######################################################################
# QUERY ACTIVE RECOMMENDATIONS
######################################################################
@app.route('/recommendations/active/<int:id>', methods=['GET'])
def get_active_related_products(id):
    app.logger.info("Query active recommendations for id: %s", id)
    recommendations = Recommendation.find_by_id_status(id)

    if not recommendations:
        raise NotFound("Active recommendations for product {} not found.".format(id))

    app.logger.info("Returning recommendations for product %s", id)
    type0_products = []
    type1_products = []
    type2_products = []
    for r in recommendations:
        if r.typeid == 0:
            type0_products.append(r.rel_id)
        elif r.typeid == 1:
            type1_products.append(r.rel_id)
        else:
            type2_products.append(r.rel_id)

    result = [
        {"relation_id": 0, "ids": type0_products},
        {"relation_id": 1, "ids": type1_products},
        {"relation_id": 2, "ids": type2_products}
    ]

    return make_response(jsonify(result), status.HTTP_200_OK)
    




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
    
