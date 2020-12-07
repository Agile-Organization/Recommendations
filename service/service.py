
"""
Recommendations Service

Initial service file for setting up recommendations controllers.
File created based on template.
Will add more routes in the future for additional API endpoints.
"""

import sys
import uuid
import logging
from functools import wraps
from flask import jsonify, request, url_for, make_response, render_template, abort
from flask_api import status  # HTTP Status Codes
from flask_restplus import Api, Resource, fields, reqparse, inputs
from werkzeug.exceptions import NotFound, BadRequest

# SQLAlchemy supports a variety of backends including SQLite, MySQL, and PostgreSQL
from flask_sqlalchemy import SQLAlchemy
from service.model import Recommendation, DataValidationError

# Import Flask application
from . import app


######################################################################
# Configure Swagger before initilaizing it
######################################################################
api = Api(
    app,
    version="1.0.0",
    title="Recommendation REST API Service",
    description="This is a Recommendation server.",
    default="recommendations",
    default_label="Recommendation operations",
    doc="/apidocs",
    prefix="/api",
)

# Define the model so that the docs reflect what can be sent
recommendation_model = api.model(
    "Recommendation",
    {
        "product-id": fields.Integer(
            readOnly=True, description="The first product id of a recommendation record"
        ),
        "related-product-id": fields.Integer(
            required=True,
            description="The second product id of a recommendation record",
        ),
        "type-id": fields.Integer(
            required=True,
            description="The type id of a recommendation record (between 1 and 3, 1: up-sell, 2: cross-sell, 3: accessory)",
        ),
        "status": fields.Boolean(
            required=True,
            description="The status of a recommendation record - is it active?",
        ),
    },
)

# query string arguments
status_type_args = reqparse.RequestParser()
'''
status_type_args.add_argument(
    "product-id", type=int, required=False, help="List Recommendations by product id"
)
status_type_args.add_argument(
    "related-product-id",
    type=int,
    required=False,
    help="List Recommendations by related product id"
)
'''
status_type_args.add_argument(
    "type-id", type=int, required=False, help="List Recommendations by type id"
)
status_type_args.add_argument(
    "status", type=inputs.boolean, required=False, help="List Recommendations by status"
)

######################################################################
# Special Error Handlers
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
# GET HEALTH CHECK
######################################################################
@app.route("/healthcheck")
def healthcheck():
    """ Let them know our heart is still beating """
    return make_response(jsonify(status=200, message="Healthy"), status.HTTP_200_OK)


@app.route("/")
def index():
    """ Index page """
    return app.send_static_file("index.html")

######################################################################
#  PATH: /recommendations
######################################################################
@api.route("/recommendations")
@api.param("product-id", "The product identifier")
@api.param("related-product-id", "The related product identifier")
@api.param("type-id", "The relationship type of a recommendation")
@api.param("status", "The status of a recommendation")
class SearchResource(Resource):
    """
    SearchResource class

    GET /api/recommendations - Returns recommendation based on query parameters
    """
    # ------------------------------------------------------------------
    # SEARCH recommendations
    # ------------------------------------------------------------------
    @api.doc("search_recommendations")
    @api.response(404, "Recommendation not found")
    @api.marshal_with(recommendation_model)
    def get(self):
        """
            Search recommendation based on query parameters

            This endpoint will return recommendation based on it's product id, related product id, type, and status.
        """
        product_id = request.args.get("product-id")
        related_product_id = request.args.get("related-product-id")
        type_id = request.args.get("type-id")
        by_status = request.args.get("status")

        app.logger.info("Request for all recommendations in the database")
        
        try:
            if product_id and related_product_id:
                recommendations = Recommendation.find_by_id_relid(
                    int(product_id), int(related_product_id)
                )
            elif product_id:
                if type_id and by_status:
                    recommendations = Recommendation.find_by_id_type_status(
                        int(product_id), int(type_id), (by_status == "True")
                    )
                elif type_id:
                    recommendations = Recommendation.find_by_id_type(
                        int(product_id), int(type_id)
                    )
                elif by_status:
                    recommendations = Recommendation.find_by_id_status(
                        int(product_id), (by_status == "True")
                    )
                else:
                    recommendations = Recommendation.find(int(product_id))
            elif related_product_id:
                if type_id and by_status:
                    recommendations = Recommendation.find_by_relid_type_status(
                        int(related_product_id), int(type_id), (by_status == "True")
                        )
                elif type_id:
                    recommendations = Recommendation.find_by_relid_type(
                        int(related_product_id), int(type_id)
                        )
                elif by_status:
                    recommendations = Recommendation.find_by_relid_status(
                        int(related_product_id), (by_status == "True")
                        )
                else:
                    recommendations = Recommendation.find_by_rel_id(int(related_product_id))
            elif type_id and by_status:
                recommendations = Recommendation.find_by_type_id_status(
                    int(type_id), (by_status == "True")
                )
            elif type_id:
                recommendations = Recommendation.find_by_type_id(int(type_id))
            elif by_status:
                recommendations = Recommendation.find_by_status((by_status == "True"))
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

        return result, status.HTTP_200_OK    


######################################################################
#  PATH: /recommendations/{product-id}/{related-product-id}
######################################################################
@api.route("/recommendations/<int:product_id>/<int:related_product_id>")
@api.param("product-id", "The product identifier")
@api.param("related-product-id", "The related product identifier")
class RecommendationResource(Resource):
    """
    RecommendationResource class

    Allows the manipulation of a single Recommendation
    GET /api/recommendations/<product_id>/<related_product_id> - Returns the Recommendation
    POST /recommendations/<product_id>/<related_product_id> - Create a new recommendation
    """

    # ------------------------------------------------------------------
    # RETRIEVE A Recommendation
    # ------------------------------------------------------------------
    @api.doc("get_recommendations")
    @api.response(404, "Recommendation not found")
    @api.marshal_with(recommendation_model)
    def get(self, product_id, related_product_id):
        """
        Retrieve a single recommendation

        This endpoint will return a Recommendation based on it's product id and related product id.
        """
        app.logger.info(
            "Querying Recommendation for product id: %s and related product id: %s",
            product_id,
            related_product_id,
        )
        recommendation = (
            Recommendation.find_recommendation(product_id, related_product_id).first()
            or Recommendation.find_recommendation(
                product_id, related_product_id, False
            ).first()
        )

        if not recommendation:
            api.abort(
                status.HTTP_404_NOT_FOUND,
                "404 Not Found: Recommendation for product id {} with related product id {} not found".format(
                    product_id, related_product_id
                ),
            )

        app.logger.info(
            "Returning Recommendation for product id: %s and related product id: %s",
            product_id,
            related_product_id,
        )

        return recommendation.serialize(), status.HTTP_200_OK

    #------------------------------------------------------------------
    # UPDATE AN EXISTING PET
    #------------------------------------------------------------------
    @api.doc('update_recommendations')
    @api.response(404, 'Recommendation not found')
    @api.response(400, 'The posted Recommendation data was not valid')
    @api.expect(recommendation_model)
    @api.marshal_with(recommendation_model)
    def put(self, product_id, related_product_id):
        """
        Update a recommendation
        This endpoint will update a Recommendation based the body that is posted
        """
        app.logger.info('Request to Update a recommendation with product-id [%s] and related-product-id [%s]', product_id, related_product_id)
        check_content_type("application/json")

        find = Recommendation.find_recommendation
        recommendation = (
            find(
                by_id=product_id,
                by_rel_id=related_product_id,
                by_status=True
            ).first()
            or 
            find(
                by_id=product_id,
                by_rel_id=related_product_id,
                by_status=False
            ).first()
        )

        if not recommendation:
            api.abort(
                status.HTTP_404_NOT_FOUND,
                "404 Not Found: Recommendation for product id '{}' with related product id '{}' not found.Please call POST to create this record.".format(
                    product_id, related_product_id
                )
            )

        app.logger.debug('Payload = %s', api.payload)
        recommendation.deserialize(api.payload)
        recommendation.save()

        return recommendation.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # ADD A NEW RECOMMENDATION
    # ------------------------------------------------------------------
    @api.doc("create_recommendations")
    @api.expect(recommendation_model)
    @api.response(400, "The posted data was not valid")
    @api.response(201, "Recommendation created successfully")
    @api.marshal_with(recommendation_model, code=201)
    def post(self, product_id, related_product_id):
        """
        Creates a recommendation
        This endpoint will create a Recommendation based the data in the body that is posted
        """
        app.logger.info("Request to create a recommendation")
        check_content_type("application/json")

        recommendation = Recommendation()
        app.logger.debug("Payload = %s", api.payload)
        recommendation.deserialize(api.payload)

        if recommendation.product_id == recommendation.related_product_id:
            raise BadRequest("product_id cannot be the same as related_product_id")

        existing_recommendation = (
            Recommendation.find_recommendation(
                recommendation.product_id, 
                recommendation.related_product_id
            ).first()
            or 
            Recommendation.find_recommendation(
                recommendation.product_id,
                recommendation.related_product_id,
                by_status=False,
            ).first()
        )

        if existing_recommendation:
            raise BadRequest(
                "Recommendation with given product id and related product id already exists"
            )

        recommendation.create()
        location_url = api.url_for(
            RecommendationResource, 
            product_id=recommendation.product_id, 
            related_product_id=recommendation.related_product_id,
            _external=True
            )

        app.logger.info(
            "recommendation from product ID [%s] to related product ID [%s] created.",
            recommendation.product_id,
            recommendation.related_product_id,
        )
        return (
            recommendation.serialize(),
            status.HTTP_201_CREATED,
            {"location": location_url}
        )

    ######################################################################
    # DELETE A RELEATIONSHIP BETWEEN A PRODUCT and A RELATED PRODUCT
    ######################################################################
    @api.doc("delete a recommendation with product id and related product id")
    @api.response(204, 'Recommendation deleted')
    def delete(self, product_id, related_product_id):
        """
        Delete a recommendation
        This endpoint will delete one unique recommendation based on
        the product id and related product id provided in the URI
        """
        app.logger.info(
            "Request to delete a recommendation by product id and related product id"
        )

        find_result = Recommendation.find_by_id_relid(product_id, related_product_id)

        if not find_result.first():
            return "", status.HTTP_204_NO_CONTENT

        recommendation = find_result.first()
        app.logger.info(
            "Deleting recommendation with product id %s and related product id %s ...",
            recommendation.product_id,
            recommendation.related_product_id,
        )
        recommendation.delete()
        app.logger.info(
            "Deleted recommendation with product id %s and related product id %s ...",
            recommendation.product_id,
            recommendation.related_product_id,
        )

        return "", status.HTTP_204_NO_CONTENT

######################################################################
#  PATH: /recommendations/{product-id}/{related-product-id}/toggle
######################################################################
@api.route("/recommendations/<int:product_id>/<int:related_product_id>/toggle")
@api.param("product-id", "The product identifier")
@api.param("related-product-id", "The related product identifier")
class ToggleResource(Resource):
    """ Handle the toggle action of a single Recommendation """
    # ------------------------------------------------------------------
    # TOGGLE A NEW RECOMMENDATION
    # ------------------------------------------------------------------
    @api.doc("toggle_recommendations")
    @api.response(404, "Recommendation not found")
    def put(self, product_id, related_product_id):
        """ 
        Toggle the status of a recommendation
        """
        app.logger.info("Request to toggle a recommendation status")

        find = Recommendation.find_recommendation
        recommendation = (
            find(by_id=product_id, by_rel_id=related_product_id, by_status=False).first()
            or find(by_id=product_id, by_rel_id=related_product_id, by_status=True).first()
        )

        if not recommendation:
            api.abort(
                status.HTTP_404_NOT_FOUND,
                "404 Not Found: Recommendation for product id {} with related product id {} not found".format(
                    product_id, related_product_id
                ),
            )

        recommendation.status = not recommendation.status

        app.logger.info(
            "Toggling Recommendation status for product %s with related product %s.",
            product_id,
            related_product_id
        )

        recommendation.save()

        app.logger.info(
            "Toggled Recommendation status for product %s with related product %s.",
            product_id,
            related_product_id
        )

        return recommendation.serialize(), status.HTTP_200_OK

######################################################################
#  PATH: /recommendations/{product_id}
######################################################################
@api.route("/recommendations/<int:product_id>")
class RecommendationSubset(Resource):
    """ Handles all interactions with collections of recommendations owned by product_id """
    ######################################################################
    # DELETE ALL RELEATIONSHIPS OF A PRODUCT BASED ON TYPE AND/OR STATUS
    ######################################################################
    @api.doc("delete all recommendations of a product with a certain type or status")
    @api.expect(status_type_args, validate=True)
    @api.response(204, 'Recommendation deleted')
    def delete(self, product_id):
        """
        Deletes recommendations based on product id and query parameters
        This endpoint will delete all the recommendations based on
        the product id and the parameter type and stauts
        """
        args = status_type_args.parse_args()
        type_id = args["type-id"]
        recommendation_status = args["status"]
        app.logger.info(type_id)
        app.logger.info(recommendation_status)        
        if type_id is None and recommendation_status is None:
            raise BadRequest("Bad Request must provide at least 1 parameter")

        if  (not (type_id is None)) and type_id not in [1, 2, 3]:
            raise BadRequest("Bad Request invalid type id provided")

        if (not (recommendation_status is None)) and recommendation_status not in [True, False]:
            raise BadRequest("Bad Request invalid status provided")

        if (not (type_id is None)) and (not (recommendation_status is None)):
            app.logger.info("Request to delete recommendations by type_id and status")

            recommendations = Recommendation.find_by_id_type_status(
                product_id, type_id, recommendation_status
            )

            for recommendation in recommendations:
                app.logger.info(
                    "Deleting all related products for product %s in type %s with status %r",
                    recommendation.product_id,
                    recommendation.type_id,
                    recommendation.status,
                )
                recommendation.delete()
                app.logger.info(
                    "Deleted all related products for product %s in type %s with status %r",
                    recommendation.product_id,
                    recommendation.type_id,
                    recommendation.status,
                )

            return "", status.HTTP_204_NO_CONTENT

        elif (not (type_id is None)):
            app.logger.info("Request to delete recommendations by type_id")
            recommendations = Recommendation.find_by_id_type(product_id, type_id)

            for recommendation in recommendations:
                app.logger.info(
                    "Deleting all related products for product %s in type %s with ",
                    recommendation.product_id,
                    recommendation.type_id,
                )
                recommendation.delete()
                app.logger.info(
                    "Deleted all related products for product %s in type %s with ",
                    recommendation.product_id,
                    recommendation.type_id,
                )

            return "", status.HTTP_204_NO_CONTENT

        elif (not (recommendation_status is None)):
            app.logger.info("Request to delete recommendations by status")
            recommendations = Recommendation.find_by_id_status(
                product_id, recommendation_status
            )

            for recommendation in recommendations:
                app.logger.info(
                    "Deleting all related products for product %s in status %r",
                    recommendation.product_id,
                    recommendation.status,
                )
                recommendation.delete()
                app.logger.info(
                    "Deleted all related products for product %s in status %r",
                    recommendation.product_id,
                    recommendation.status,
                )

            return "", status.HTTP_204_NO_CONTENT

######################################################################
#  PATH: /recommendations/{product_id}/all
######################################################################
@api.route("/recommendations/<int:product_id>/all")
class RecommendationAll(Resource):
    """ Handles all interactions with all recommendations owned by product_id """
    ######################################################################
    # DELETE ALL RELEATIONSHIP OF A PRODUCT BY PRODUCT ID
    ######################################################################
    @api.doc("delete all recommendations of a product")
    @api.response(204, 'Recommendation deleted')
    def delete(self, product_id):
        """
        Deletes all recommendations
        This endpoint will delete all the recommendations based on
        the product id provided in the URI
        """
        app.logger.info("Request to delete recommendations by product id")
        recommendations = Recommendation.find(product_id)
 
        if not recommendations.first():
            return "", status.HTTP_204_NO_CONTENT
 
        for recommendation in recommendations:
            app.logger.info(
                "Deleting all related products for product %s",
                recommendation.product_id,
            )
            recommendation.delete()
            app.logger.info(
                "Deleted all related products for product %s",
                recommendation.product_id,
            )

        return "", status.HTTP_204_NO_CONTENT

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################

def init_db():
    """ Initialies the SQLAlchemy app """
    global app
    Recommendation.init_db(app)


# load sample data
def data_load(payload):
    """ Loads a Recommendation into the database """
    recommendation = Recommendation()
    recommendation.product_id = payload["product-id"]
    recommendation.related_product_id = payload["related-product-id"]
    recommendation.type_id = payload["type-id"]
    recommendation.status = payload["status"]
    recommendation.create()


def check_content_type(content_type):
    """ Checks that the media type is correct """
    if request.headers["Content-Type"] == content_type:
        return
    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(415, "Content-Type must be {}".format(content_type))
