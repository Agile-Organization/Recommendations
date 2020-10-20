"""
Recommendations Service

Initial service file for setting up recommendations controllers.
File created based on template.
Will add more routes in the future for additional API endpoints.
"""

import os
import sys
import logging
import datetime
from flask import Flask, jsonify, request, url_for, make_response, abort
from flask_api import status  # HTTP Status Codes
from werkzeug.exceptions import NotFound, BadRequest

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
    return jsonify(datetime.datetime.now()), status.HTTP_200_OK

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

    products = Recommendation.find_by_id_status(id) # need to replace find method with actual function name from model file
 
    if not products.first():
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

    relationships = [
        {"relation_id": 1, "ids": type_1_active, "inactive_ids": type_1_inactive},
        {"relation_id": 2, "ids": type_2_active, "inactive_ids": type_2_inactive},
        {"relation_id": 3, "ids": type_3_active, "inactive_ids": type_3_inactive}
    ]

    return make_response(jsonify(relationships), status.HTTP_200_OK)

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
        if r.typeid == 1:
            type0_products.append(r.rel_id)
        elif r.typeid == 2:
            type1_products.append(r.rel_id)
        else:
            type2_products.append(r.rel_id)

    result = [
        {"relation_id": 1, "ids": type0_products},
        {"relation_id": 2, "ids": type1_products},
        {"relation_id": 3, "ids": type2_products}
    ]

    return make_response(jsonify(result), status.HTTP_200_OK)

######################################################################
# CREATE RELATIONSHIP BETWEEN PRODUCTS
######################################################################
@app.route('/recommendations', methods=['POST'])
def create_recommendation_between_products():
    """
    Creates a Recommendation
    This endpoint will create a recommendation based the data in the body that is posted
    {
        "product-id" : 1,
        "related-product-id" : 2,
        "type-id" : 1,
        "status" : 1
    }
    """
    app.logger.info("Request to create a recommendation")
    check_content_type("application/json")
    recommendation = Recommendation()
    recommendation.deserialize(request.get_json())
    recommendation.create()
    message = recommendation.serialize()
    location_url = url_for("get_related_products", id=recommendation.id, _external=True)

    app.logger.info("recommendation from ID [%s] to ID [%s] created.", recommendation.id, recommendation.rel_id)
    return make_response(jsonify(message), status.HTTP_201_CREATED, {"Location": location_url} )

######################################################################
# QUERY RELATIONSHIP BETWEEN TWO PRODUCTS
######################################################################
@app.route('/recommendations/relationship', methods=['GET'])
def get_recommendation_relationship_type():
    """
    /recommendations/relationship?product1=<int:id>&product2=<int:id>
    Returns recommendation for product1 and product2 if exists
        {
          "product-id" : <int:product-id>,
          "related-product-id" : <int:related-product-id>,
          "type-id" : <int:typeid>,
          "status" : True
        }
        With HTTP_200_OK status
    """
    product_id = request.args.get('product1')
    rel_product_id = request.args.get('product2')

    product_id_valid = product_id \
                       and product_id.isnumeric() \
                       and "-" not in product_id
    rel_product_id_valid = rel_product_id \
                           and rel_product_id.isnumeric() \
                           and "-" not in rel_product_id

    if not product_id_valid or not rel_product_id_valid:
        raise BadRequest("Bad Request 2 invalid product ids provided,"\
                         " received product: %s and related product: %s do not"\
                         " exist".format(product_id, rel_product_id))

    product_id, rel_product_id = int(product_id), int(rel_product_id)

    exists = Recommendation.check_if_product_exists
    if not exists(product_id) or not exists(rel_product_id):
        return '', status.HTTP_204_NO_CONTENT

    app.logger.info("Querying active recommendation for product: %s and"\
                    " related product: %s".format(product_id, rel_product_id))
    recommendation = Recommendation.find_recommendation(by_id=product_id,\
                                       by_rel_id=rel_product_id, by_status=True)

    app.logger.info("Returning active recommendation for product: %s and"\
                    " related product: %s".format(product_id, rel_product_id))

    if recommendation and recommendation.first():
        return jsonify(recommendation.first().serialize()), status.HTTP_200_OK

    return '', status.HTTP_204_NO_CONTENT

######################################################################
# UPDATE RECOMMENDATION TYPEID FOR TWO PRODUCTS
######################################################################
@app.route('/recommendations', methods=['PUT'])
def update_recommendation_between_products():
    """
    Updates a Recommendation
        This endpoint will update a recommendation based the data in the request body.
        Expected data in body:
        {
          "product-id" : <int:product-id>,
          "related-product-id" : <int:related-product-id>,
          "type-id" : <int:typeid>,
          "status" : <bool: status>
        }
        The old recommendation will be replaced with data
        sent in the request body if any old recommendation exists.
        If no old recommendation exists returns a HTTP_404_NOT_FOUND
    """
    app.logger.info("Request to update a recommendation")
    check_content_type("application/json")

    try:
        recommendation = Recommendation()
        recommendation.deserialize(request.get_json())

        find = Recommendation.find_recommendation
        old_recommendation = find(by_id=recommendation.id,
                                  by_rel_id=recommendation.rel_id).first() \
                                  or find(by_id=recommendation.id,
                                     by_rel_id=recommendation.rel_id,
                                     by_status=False).first()
    except TypeError as error:
        raise DataValidationError(error)
    except DataValidationError as error:
        raise DataValidationError(error)

    if not old_recommendation:
        raise NotFound("Recommendation does not exist"\
                       " please do a POST instead of PUT")

    old_typeid = old_recommendation.typeid
    old_recommendation.typeid = recommendation.typeid
    old_recommendation.status = recommendation.status

    app.logger.info("Updating Recommendation typeid for product %s with "\
                    "related product %s from %s to %s.", recommendation.id,
                    recommendation.rel_id, old_typeid, recommendation.typeid)

    old_recommendation.save()

    app.logger.info("Recommendation typeid updated for product %s with "\
                    "related product %s from %s to %s.", recommendation.id,
                    recommendation.rel_id, old_typeid, recommendation.typeid)

    return '', status.HTTP_200_OK

######################################################################
# Error Handlers
######################################################################
@app.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles Value Errors from bad data """
    return bad_request(error)


@app.errorhandler(status.HTTP_400_BAD_REQUEST)
def bad_request(error):
    """ Handles bad requests with 400_BAD_REQUEST """
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
