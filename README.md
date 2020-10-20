# Recommendations
The recommendations resource is a representation a product recommendation based on another product. In essence it is just a relationship between two products that "go together" (e.g., radio and batteries, printers and ink, shirts and pants, etc.). It could also recommend based on what other customers have purchased like "customers who bought item A usually buy item B". Recommendations have a recommendation type like (1: up-sell, 2: cross-sell, 3: accessory). This way a product page could request all of the up-sells for a product. (Hint: an up-sell is a more full featured and expensive product that you recommend instead of the one they initially want to buy, cross-sells are other items just like this one with similar features and price.)

# Steps To Run and Test The Code Base
## Prerequisites
Download [Vagrant](https://www.vagrantup.com/)

Download [VirtualBox](https://www.virtualbox.org/)

Download [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

You can download Vagrant, VirtualBox, Git using the above official links on any operating system.

## Steps to run the Recommendations service
The following commands will clone the recommendations repository and simulate production environment for the recommendations service.
```shell
    $ git clone https://github.com/Agile-Organization/recommendations
    $ cd recommendations
    $ vagrant up
    $ vagrant ssh
    $ cd /vagrant
```
To run the flask service application execute the following commands:
```shell
    $ flask run --host=0.0.0.0
```
## API Endpoints
You can invoke the API endpoints at http://0.0.0.0:5000/ on your machine once the flask application is running.
The API endpoints available as of now are:
```shell
    POST /recommendations
      - Creates a Recommendation
        This endpoint will create a recommendation based the data in the body that is posted
        Expected data in request body:
          {
              "product-id" : <int:product-id>,
              "related-product-id" : <int:related-product-id>,
              "type-id" : <int:typeid>,
              "status" : True
        }
        Returns a success message and HTTP_201_CREATED status if successful
    POST /recommendations/<int:id>
      - Retrieve all related products by providing a product id
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
        Returns HTTP_200_OK status
    GET /recommendations/relationship?product1=<int:product-id>&product2=<int:related-product-id>
      - Returns recommendation for product1 and product2 if exists
        {
              "product-id" : <int:product-id>,
              "related-product-id" : <int:related-product-id>,
              "type-id" : <int:typeid>,
              "status" : True
        }
        Returns HTTP_200_OK status
        
        Returns Null with HTTP_204_NO_CONTENT if no recommendation exists for product1 and product2
    GET /recommendations/active/<int:id>
      - Returns all active recommendations for the product id provided in route url;
        Return Format:
        [
            {"relation_id": 1, "ids": <type0_products_list>},
            {"relation_id": 2, "ids": <type1_products_list>},
            {"relation_id": 3, "ids": <type2_products_list>}
        ]
        Returns HTTP_200_OK status
    PUT /recommendations
      - Updates a Recommendation
        This endpoint will update a recommendation based the data in the request body.
        Expected data in body:
        {
              "product-id" : <int:product-id>,
              "related-product-id" : <int:related-product-id>,
              "type-id" : <int:typeid>,
              "status" : <bool: status>
        }
        The old recommendation will be replaced with data sent in the request body if any old recommendation exists.
        If everything works out well returns HTTP_200_OK status
        If no old recommendation exists returns a HTTP_404_NOT_FOUND
    DELETE /recommendations/<int:id>/related-product/<int:rel_id>
      - Deletes a Recommendation
        This endpoint will delete a recommendation based
        the product id and related product id provided in the route
        Returns: HTTP_204_NO_CONTENT
          
```
## Database Schema
Recommendations service has only one database table with the following columns.
```shell
    id = <Integer> Primary Key: Represents the product id
    rel_id = <Integer> Primary Key: Represents the related product id
    typeid = <Integer> : Represents relationship type between product and related product; (1: up-sell, 2: cross-sell, 3: accessory)
    status = <Boolean> : Represents if the recommendation is active or in-active
```
## Running Unit Tests

Once in the `/vagrant` directory just run the following command to run the unit tests and get coverage report at the end of your tests. Nose is pre configured to run coverage and show coverage report.

```shell
    $ nosetests
```

## Code Analysis Using Pylint

Code analysis settings are pre-configured to get code analysis for the code base just run the following commands once in `/vagrant` directory.

```shell
    $ pylint service
    $ pylint tests
```
If you want to run tests for any other directories you can run `pylint <directory-name>` to get your analysis.

## Exiting Gracefully
To exit the production environment run the following commands:

```shell
    $ exit
    $ vagrant halt
```
