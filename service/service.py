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

# Document the type of autorization required
authorizations = {"apikey": {"type": "apiKey", "in": "header", "name": "X-Api-Key"}}

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
    doc="/apidocs",  # default also could use doc='/apidocs/'
    authorizations=authorizations,
    prefix="/api",
)

# Define the model so that the docs reflect what can be sent
recommendation_model = api.model(
    "Recommendation",
    {
        "product-id": fields.Integer(
            readOnly=True, description="The unique product ID"
        ),
        "related-product-id": fields.Integer(
            required=True, description="The unique related product ID"
        ),
        "type-id": fields.Integer(
            required=True,
            description="The type ID of the Recommendation (1: up-sell, 2: cross-sell, 3: accessory)",
        ),
        "status": fields.Boolean(
            required=True, description="Is the Recommendation currently active?"
        ),
    },
)

# query string arguments
recommendation_args = reqparse.RequestParser()
recommendation_args.add_argument(
    "product-id", type=int, required=False, help="List Recommendations by product id"
)
recommendation_args.add_argument(
    "related-product-id",
    type=int,
    required=False,
    help="List Recommendations by related product id",
)
recommendation_args.add_argument(
    "type-id", type=int, required=False, help="List Recommendations by type id"
)
recommendation_args.add_argument(
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
# Authorization Decorator
######################################################################
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "X-Api-Key" in request.headers:
            token = request.headers["X-Api-Key"]

        if app.config.get("API_KEY") and app.config["API_KEY"] == token:
            return f(*args, **kwargs)
        else:
            return {"message": "Invalid or missing token"}, 401

    return decorated


######################################################################
# Function to generate a random API key (good for testing)
######################################################################
def generate_apikey():
    """ Helper function used when testing API keys """
    return uuid.uuid4().hex


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
#  PATH: /recommendations/{product-id}/{related-product-id}
######################################################################
@api.route("/recommendations/<int:product_id>/<int:related_product_id>")
@api.param("product_id", "The product identifier")
@api.param("related_product_id", "The related product identifier")
class RecommendationResource(Resource):
    """
    RecommendationResource class

    Allows the manipulation of a single Recommendation
    GET /recommendations/<product_id>/<related_product_id> - Returns the Recommendation
    """

    # ------------------------------------------------------------------
    # RETRIEVE A Recommendation
    # ------------------------------------------------------------------
    @api.doc("get_recommendations")
    @api.response(404, "Recommendation not found")
    @api.marshal_with(recommendation_model)
    def get(self, product_id, related_product_id):
        """
        Retrieve a single Recommendation

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
                "Recommendatin for product id {} with related product id {} not found".format(
                    product_id, related_product_id
                ),
            )

        app.logger.info(
            "Returning Recommendation for product id: %s and related product id: %s",
            product_id,
            related_product_id,
        )

        return recommendation.serialize(), status.HTTP_200_OK


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
@app.before_first_request
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


def data_reset():
    """ Removes all Recommendations from the database """
    Recommendation.remove_all()


def check_content_type(content_type):
    """ Checks that the media type is correct """
    if request.headers["Content-Type"] == content_type:
        return
    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(415, "Content-Type must be {}".format(content_type))
