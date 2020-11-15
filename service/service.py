"""
Recommendations Service

Initial service file for setting up recommendations controllers.
File created based on template.
Will add more routes in the future for additional API endpoints.
"""

import datetime
from flask import jsonify, request, url_for, make_response, abort
from flask_api import status  # HTTP Status Codes
from werkzeug.exceptions import NotFound, BadRequest

# SQLAlchemy supports a variety of backends including SQLite, MySQL, and PostgreSQL
from flask_sqlalchemy import SQLAlchemy
from service.model import Recommendation, DataValidationError

# Import Flask application
from . import app

######################################################################
# GET HEALTH CHECK
######################################################################
@app.route('/healthcheck')
def healthcheck():
    """ Let them know our heart is still beating """
    return make_response(jsonify(status=200, message='Healthy'), status.HTTP_200_OK)

######################################################################
# GET INDEX
######################################################################
@app.route('/')
def index():
    return app.send_static_file('index.html')

######################################################################
# QUERY ALL RECOMMENDATIONS
######################################################################
@app.route("/recommendations", methods=["GET"])
def get_all_recommendations():
    """ 
    Returns all the recommendations
    [
        {product_id: 1, related_product_id: 10001, type: 1, status: True},
        {product_id: 2, related_product_id: 10002, type: 2, status: True},
        {product_id: 3, related_product_id: 10003, type: 3, status: False},
        ...
    ]
    
    With HTTP_200_OK status
    """
    product_id = request.args.get('product-id')
    related_product_id = request.args.get('related-product-id')
    type_id = request.args.get('type-id')
    by_status = request.args.get('status')

    app.logger.info("Request for all recommendations in the database")

    try:
        if product_id and related_product_id:
            recommendations = Recommendation.find_by_id_relid(int(product_id), int(related_product_id))
        elif product_id:
            if type_id and by_status:
                recommendations = Recommendation.find_by_id_type_status(int(product_id), int(type_id), (by_status=="True"))
            elif type_id:
                recommendations = Recommendation.find_by_id_type(int(product_id), int(type_id))
            elif by_status:
                recommendations = Recommendation.find_by_id_status(int(product_id), (by_status=="True"))
            else:
                recommendations = Recommendation.find(int(product_id))
        elif type_id and by_status:
            recommendations = Recommendation.find_by_type_id_status(int(type_id), (by_status=="True"))
        elif type_id:
            recommendations = Recommendation.find_by_type_id(int(type_id))
        elif by_status:
            recommendations = Recommendation.find_by_status((by_status=="True"))
        else:
            recommendations = Recommendation.all()
    except DataValidationError as error:
        raise DataValidationError(str(error))
    except ValueError as error:
        raise DataValidationError(str(error))
    
    result = []
    for rec in recommendations:
        record = rec.serialize()
        result.append(record)

    return make_response(jsonify(result), status.HTTP_200_OK)
    

######################################################################
# QUERY RELATED PRODUCTS BY PRODUCT ID
######################################################################
@app.route("/recommendations/<int:product_id>", methods=["GET"])
def get_related_products(product_id):
    """
    Retrieve all related products by providing a product id
    returns a list of 3 objects, showing a list of active ids
    and inactive ids for each realationship type
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
    app.logger.info("Request for related products with product_id: %s", product_id)

    products = Recommendation.find_by_id_status(product_id) # need to replace find method with actual function name from model file

    # assume model returns records in format of: [{product_id: 1, related_product_id: 2, type_id: 1, status: true}]
    relationships = []
    type_1_active, type_1_inactive = [], []
    type_2_active, type_2_inactive = [], []
    type_3_active, type_3_inactive = [], []

    for p in products:
        if p.type_id == 1:
            type_1_active.append(p.related_product_id) if p.status else type_1_inactive.append(p.related_product_id)
        elif p.type_id == 2:
            type_2_active.append(p.related_product_id) if p.status else type_2_inactive.append(p.related_product_id)
        else:
            type_3_active.append(p.related_product_id) if p.status else type_3_inactive.append(p.related_product_id)


    if len(type_1_active) or len(type_1_inactive):
        relationships.append(
            {
                "relation_id": 1, 
                "ids": type_1_active, 
                "inactive_ids": type_1_inactive
            })
    if len(type_2_active) or len(type_2_inactive):
        relationships.append(
            {
                "relation_id": 2, 
                "ids": type_2_active, 
                "inactive_ids": type_2_inactive
            })
    if len(type_3_active) or len(type_3_inactive):
        relationships.append(
            {
                "relation_id": 3, 
                "ids": type_3_active, 
                "inactive_ids": type_3_inactive
            })

    return make_response(jsonify(relationships), status.HTTP_200_OK)


######################################################################
# QUERY ACTIVE RECOMMENDATIONS
######################################################################
@app.route('/recommendations/<int:product_id>/active', methods=['GET'])
def get_active_related_products(product_id):
    """
    Query active recommendations of a product by providing product_id.
    Results are returned in the form of
    [
        {
            relation_id: 1,
            ids: [id1, id2, ...]
        },
        {
            relation_id: 2,
            ids: [id1, id2, ...]
        },
        {
            relation_id: 3,
            ids: [id1, id2, ...]
        }
    ]
    """
    app.logger.info("Query active recommendations for product_id: %s", product_id)
    recommendations = Recommendation.find_by_id_status(product_id)

    if not recommendations.all():
        raise NotFound("Active recommendations for product {} not found.".format(product_id))

    app.logger.info("Returning recommendations for product %s", product_id)
    type0_products = []
    type1_products = []
    type2_products = []
    for recommendation in recommendations:
        if recommendation.type_id == 1:
            type0_products.append(recommendation.related_product_id)
        elif recommendation.type_id == 2:
            type1_products.append(recommendation.related_product_id)
        else:
            type2_products.append(recommendation.related_product_id)

    result = []
    if len(type0_products):
        result.append({"relation_id": 1, "ids": type0_products})
    if len(type1_products):
        result.append({"relation_id": 2, "ids": type1_products})
    if len(type2_products):
        result.append({"relation_id": 3, "ids": type2_products})
    
    return make_response(jsonify(result), status.HTTP_200_OK)


######################################################################
# QUERY RECOMMENDATIONS BY PRODUCT ID AND TYPE
######################################################################
@app.route('/recommendations/<int:product_id>/type/<int:type_id>', methods=['GET'])
def get_related_products_with_type(product_id, type_id):
    """
    Query recommendations by product_id and type.
    Results are returned in the form of
    {ids: [id1, id2, ...], status: [status1, status2, ...]}
    """
    app.logger.info("Query type: %s recommendations for product_id: %s", type_id, product_id)
    recommendations = Recommendation.find_by_id_type(product_id, type_id)

    if not recommendations.all():
        raise NotFound("Type {} recommendations for product {} not found".format(type_id, product_id))

    app.logger.info("Returning type %s recommendations for product %s", type_id, product_id)
    active_products, inactive_products = [], []
    for recommendation in recommendations:
        if recommendation.status == True:
            active_products.append(recommendation.related_product_id)
        else:
            inactive_products.append(recommendation.related_product_id)
    result = []
    if(len(active_products)):
        result.append(
            {
                "status": "True",
                "ids": active_products
            }
        )
    if(len(inactive_products)):
        result.append(
            {
                "status": "False",
                "ids": inactive_products
            }
        )

    return make_response(jsonify(result), status.HTTP_200_OK)


######################################################################
# QUERY RELATIONSHIP BETWEEN TWO PRODUCTS
######################################################################
@app.route('/recommendations/relationship', methods=['GET'])
def get_recommendation_relationship_type():
    """
    /recommendations/relationship?product1=<int:product_id>&product2=<int:product_id>
    Returns recommendation for product1 and product2 if exists
        {
          "product-id" : <int:product-id>,
          "related-product-id" : <int:related-product-id>,
          "type-id" : <int:type_id>,
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
                         " received product: {} and related product: {} do not"\
                         " exist".format(product_id, rel_product_id))

    product_id, rel_product_id = int(product_id), int(rel_product_id)

    exists = Recommendation.check_if_product_exists
    if not exists(product_id) or not exists(rel_product_id):
        return '', status.HTTP_204_NO_CONTENT

    app.logger.info("Querying active recommendation for product: {} and"\
                    " related product: {}".format(product_id, rel_product_id))
    recommendation = Recommendation.find_recommendation(by_id=product_id,\
                                       by_rel_id=rel_product_id, by_status=True)

    app.logger.info("Returning active recommendation for product: {} and"\
                    " related product: {}".format(product_id, rel_product_id))

    if recommendation and recommendation.first():
        return jsonify(recommendation.first().serialize()), status.HTTP_200_OK

    return '', status.HTTP_204_NO_CONTENT
######################################################################
# QUERY RECOMMENDATIONS BY PRODUCT ID AND RELATED PRODUCT ID
######################################################################
@app.route('/recommendations/<int:product_id>/<int:rel_product_id>', methods=['GET'])
def get_recommendation(product_id, rel_product_id):
    """
    Query recommendations by product id and related product id.
    Result is returned in a json format
    """
    app.logger.info("Querying Recommendation for product id: %s and related product id: %s", product_id, rel_product_id)
    recommendation = Recommendation.find_recommendation(product_id, rel_product_id).first() or Recommendation.find_recommendation(product_id, rel_product_id, False).first()

    if not recommendation:
        raise NotFound("Recommendatin for product id {} with related product id {} not found".format(product_id, rel_product_id))

    app.logger.info("Returning Recommendation for product id: %s and related product id: %s", product_id, rel_product_id)

    return make_response(jsonify(recommendation.serialize()), status.HTTP_200_OK)


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
    if recommendation.product_id == recommendation.related_product_id:
        raise BadRequest('product_id cannot be the same as related_product_id') 

    recommendation.create()
    message = recommendation.serialize()
    location_url = url_for("get_related_products", product_id=recommendation.product_id, _external=True)

    app.logger.info("recommendation from ID [%s] to ID [%s] created.",
                    recommendation.product_id, recommendation.related_product_id)
    return make_response(jsonify(message), status.HTTP_201_CREATED, {"Location": location_url})


######################################################################
# CREATE RELATIONSHIP BETWEEN PRODUCTS (RESTful)
######################################################################
@app.route('/recommendations/<int:product_id>/<int:rel_product_id>', methods=['POST'])
def create_recommendation(product_id, rel_product_id):
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

    if recommendation.product_id == recommendation.related_product_id:
        raise BadRequest('product_id cannot be the same as related_product_id') 

    existing_recommendation = Recommendation.find_recommendation(recommendation.product_id, recommendation.related_product_id).first() or Recommendation.find_recommendation(recommendation.product_id, recommendation.related_product_id, by_status=False).first()

    if existing_recommendation:
        raise BadRequest('Recommendation with given product id and related product id already exists')

    recommendation.create()
    message = recommendation.serialize()
    location_url = "/recommendations/{}/{}".format(recommendation.product_id, recommendation.related_product_id)

    app.logger.info("recommendation from product ID [%s] to related product ID [%s] created.",
                    recommendation.product_id, recommendation.related_product_id)
    return make_response(jsonify(message), status.HTTP_201_CREATED, {"Location": location_url})




######################################################################
# UPDATE RECOMMENDATION
######################################################################
@app.route('/recommendations/<int:product_id>/<int:related_product_id>', methods=['PUT'])
def update_recommendation(product_id, related_product_id):
    """
    Updates a Recommendation
        This endpoint will update a recommendation based the data in the request body.
        Expected data in body:
        {
          "product-id" : <int:product-id>,
          "related-product-id" : <int:related-product-id>,
          "type-id" : <int:type_id>,
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
        old_recommendation = find(by_id=recommendation.product_id, 
                                  by_rel_id=recommendation.related_product_id, 
                                  by_status=True).first() \
                          or find(by_id=recommendation.product_id, 
                                  by_rel_id=recommendation.related_product_id,
                                  by_status=False).first()
    except DataValidationError as error:
        raise DataValidationError(error)

    if not old_recommendation:
        raise NotFound("Recommendation does not exist. Please call POST to create this record")

    old_typeid = old_recommendation.type_id
    old_recommendation.type_id = recommendation.type_id
    old_recommendation.status = recommendation.status

    app.logger.info("Updating Recommendation type_id for product %s with "\
                    "related product %s from %s to %s.", recommendation.product_id,
                    recommendation.related_product_id, old_typeid, recommendation.type_id)

    old_recommendation.save()

    app.logger.info("Recommendation type_id updated for product %s with "\
                    "related product %s from %s to %s.", recommendation.product_id,
                    recommendation.related_product_id, old_typeid, recommendation.type_id)

    return '', status.HTTP_200_OK


######################################################################
# TOGGLE RECOMMENDATION STATUS FOR TWO PRODUCTS
######################################################################
@app.route('/recommendations/<int:product_id>/<int:rel_product_id>/toggle', methods=['PUT'])
def toggle_recommendation_between_products(product_id, rel_product_id):
    """
    Updates a Recommendation
        This endpoint will toggle a recommendation status
        if the recommendation exists.
    """
    app.logger.info("Request to toggle a recommendation status")

    find = Recommendation.find_recommendation
    recommendation = find(by_id=product_id, by_rel_id=rel_product_id, by_status=False).first() or find(by_id=product_id, by_rel_id=rel_product_id, by_status=True).first()

    if not recommendation:
        raise NotFound("Recommendation does not exist")

    recommendation.status = not recommendation.status

    app.logger.info("Toggling Recommendation status for product %s with "\
                    "related product %s.", product_id, rel_product_id)

    recommendation.save()

    app.logger.info("Toggled Recommendation status for product %s with "\
                    "related product %s.", product_id, rel_product_id)

    return jsonify({'status': recommendation.status}), status.HTTP_200_OK


######################################################################
# DELETE ALL RELEATIONSHIP OF A PRODUCT BY OR TYPE AND/OR STATUS
######################################################################
@app.route('/recommendations/<int:product_id>', methods=['DELETE'])
def delete_by_type_status(product_id):
    """ Deletes recommendations
    This endpoint will delete all the recommendations based on
    the product id and the parameter type and stauts
    """
    type_id = request.args.get('type_id')
    recommendation_status = request.args.get('status')

    if not type_id and not recommendation_status:
        raise BadRequest("Bad Request must provide at least 1 parameter")

    if(type_id and type_id not in ["1", "2", "3"]):
        raise BadRequest("Bad Request invalid type id provided")

    if(recommendation_status and recommendation_status not in ["True", "False"]):
        raise BadRequest("Bad Request invalid status provided")

    if(type_id and recommendation_status):
        app.logger.info("Request to delete recommendations by type_id and status")
        type_id = int(type_id)
        recommendation_status = bool(recommendation_status)

        recommendations = Recommendation.find_by_id_type_status(product_id, type_id, recommendation_status)

        for recommendation in recommendations:
            app.logger.info("Deleting all related products for product %s in type %s with status %r", 
                                recommendation.product_id, recommendation.type_id, recommendation.status)
            recommendation.delete()
            app.logger.info("Deleted all related products for product %s in type %s with status %r", 
                                recommendation.product_id, recommendation.type_id, recommendation.status)

        return '', status.HTTP_204_NO_CONTENT

    elif(type_id):
        app.logger.info("Request to delete recommendations by type_id")
        type_id = int(type_id)
        recommendations = Recommendation.find_by_id_type(product_id, type_id)

        for recommendation in recommendations:
            app.logger.info("Deleting all related products for product %s in type %s with ", recommendation.product_id, recommendation.type_id)
            recommendation.delete()
            app.logger.info("Deleted all related products for product %s in type %s with ", recommendation.product_id, recommendation.type_id)

        return '', status.HTTP_204_NO_CONTENT

    elif(recommendation_status):
        app.logger.info("Request to delete recommendations by status")
        recommendation_status = bool(recommendation_status)
        recommendations = Recommendation.find_by_id_status(product_id, recommendation_status)

        for recommendation in recommendations:
            app.logger.info("Deleting all related products for product %s in status %r", recommendation.product_id, recommendation.status)
            recommendation.delete()
            app.logger.info("Deleted all related products for product %s in status %r", recommendation.product_id, recommendation.status)

        return '', status.HTTP_204_NO_CONTENT


######################################################################
# DELETE ALL RELEATIONSHIP OF A PRODUCT BY PRODUCT ID
######################################################################
@app.route('/recommendations/<int:product_id>/all', methods=['DELETE'])
def delete_all_by_id(product_id):
    """ Deletes recommendations
    This endpoint will delete all the recommendations based on
    the product id provided in the URI
    """

    app.logger.info("Request to delete recommendations by product id")

    recommendations = Recommendation.find(product_id)

    if not recommendations.first():
        return '', status.HTTP_204_NO_CONTENT

    for recommendation in recommendations:
        app.logger.info("Deleting all related products for product %s with ", recommendation.product_id)
        recommendation.delete()
        app.logger.info("Deleted all related products for product %s with ", recommendation.product_id)

    return '', status.HTTP_204_NO_CONTENT


######################################################################
# DELETE A RELEATIONSHIP BETWEEN A PRODUCT and A RELATED PRODUCT
######################################################################
@app.route('/recommendations/<int:product_id>/<int:rel_product_id>', methods=['DELETE'])
def delete_by_id_relid(product_id, rel_product_id):
    """
    Deletes recommendation
    This endpoint will delete one unique recommendation based on
    the product id and related product id provided in the URI
    """
    app.logger.info("Request to delete a recommendation by product id and related product id")

    find_result = Recommendation.find_by_id_relid(product_id, rel_product_id)

    if not find_result.first():
        return '', status.HTTP_204_NO_CONTENT

    recommendation = find_result.first()
    app.logger.info("Deleting recommendation with product id %s and related product id %s ...", 
                    recommendation.product_id, recommendation.related_product_id)
    recommendation.delete()
    app.logger.info("Deleted recommendation with product id %s and related product id %s ...", 
                    recommendation.product_id, recommendation.related_product_id)
    
    return '', status.HTTP_204_NO_CONTENT


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
