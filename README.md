# Recommendations

[![Build Status](https://travis-ci.org/Agile-Organization/recommendations.svg?branch=master)](https://travis-ci.org/Agile-Organization/recommendations)
[![codecov](https://codecov.io/gh/Agile-Organization/recommendations/branch/master/graph/badge.svg?token=3LLMCBRGCQ)](undefined)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

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
| Method | Path | Description |
| :---------: | :---------: | :------------: |
|GET|/recommendations|Search recommendation based on query parameters|
|GET|/recommendations/{product_id}/{related_product_id}|Retrieve a single recommendation|
|POST|/recommendations/{product_id}/{related_product_id}|Creates a recommendation|
|PUT|/recommendations/{product_id}/{related_product_id}|Update a recommendation|
|PUT|/recommendations/{product_id}/{related_product_id}/toggle|Toggle the status of a recommendation|
|DELETE|/recommendations/{product-id}|Deletes recommendations based on product id and query parameters|
|DELETE|/recommendations/{product-id}/all|Delete all recommendations|
|DELETE|/recommendations/{product_id}/{related_product_id}|Delete a recommendation|

## Database Schema
Recommendations service has only one database table with the following columns.
| Column | Type | Contraint | Description |Details|
| :---------: | :---------: | :------------: |  :------------: | :-----------: |  
|product_id|Integer|Primary Key|Represents the id of the product|
|related_product_id|Integer|Primary Key|Represents the id of the related product||
|type_id|Integer||Represents relationship type between product and related product|1:upshell<br/>2:cross-sell<br/> 3:accessory|
|status|Boolean||Represents if the recommendation is active or in-active|

## Running Unit Tests

Once in the `/vagrant` directory just run the following command to run the unit tests and get coverage report at the end of your tests. Nose is pre configured to run coverage and show coverage report.

```shell
    $ nosetests
```

## Start the server locally and run Behave Tests

Also in the `/vagrant` directory, run the following command to start the server at http://localhost:5000/ .

```shell
    $ honcho start
```

Then you can open another terminal and run behave tests with the following command once in the `/vagrant` directory.

```shell
    $ behave
```
 
Or in the `/vagrant` directory, run the following command to start the server and run the behave tests at the same time.

```shell
    $ honcho start & behave
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
