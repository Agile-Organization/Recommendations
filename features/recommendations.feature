Feature: The recommendation service back-end
    As a recommendation service
    I need a RESTful catalog service
    So that I can keep track of all the recommendations

Background:
    Given the following recommendations:
        | product-id | related-product-id | type-id | status |
        | 1          | 2                  | 1       | True   |
        | 1          | 3                  | 2       | True   |
        | 1          | 4                  | 3       | False  |
        | 10         | 22                 | 2       | True   |

Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Recommendation RESTful Service" in the title
    And I should not see "404 Not Found"

Scenario: Create a Recommendation
    When I visit the "Home Page"
    And I set the "product_id" to "21"
    And I set the "related_product_id" to "23"
    And I set the "type_id" to "1"
    And I select "True" in the "status" dropdown
    And I press the "Create" button
    Then I should see the message "Success"
    When I copy the "product_id" field
    And I press the "Clear" button
    Then the "product_id" field should be empty
    And the "related_product_id" field should be empty
    And the "type_id" field should be empty
    When I paste the "product_id" field
    And I set the "related_product_id" to "23"
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "1" in the "type_id" field
    And I should see "True" in the "status" field

Scenario: List all active recommendations
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see a recommendation from "1" to "2" with type "1"
    And I should see a recommendation from "1" to "3" with type "2"
    And I should see a recommendation from "1" to "4" with type "3"

Scenario: Read an existing recommendation
    When I visit the "Home Page"
    And I set the "product_id" to "10"
    And I set the "related_product_id" to "22"
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "2" in the "type_id" field
    And I should see "True" in the "status" field

Scenario: Read a non-exist recommendation
    When I visit the "Home Page"
    And I set the "product_id" to "1"
    And I set the "related_product_id" to "7"
    And I press the "Retrieve" button
    Then I should see the message "404 Not Found"

Scenario: Read a recommendation without providing product_id and related_product_id
    When I visit the "Home Page"
    And I press the "Retrieve" button
    Then I should see the message "Please enter Product ID and Related Product ID"

Scenario: Read a recommendation without providing product_id
    When I visit the "Home Page"
    And I set the "related_product_id" to "7"
    And I press the "Retrieve" button
    Then I should see the message "Please enter Product ID and Related Product ID"

Scenario: Read a recommendation without providing product_id and related_product_id
    When I visit the "Home Page"
    And I set the "product_id" to "1"
    And I press the "Retrieve" button
    Then I should see the message "Please enter Product ID and Related Product ID"

Scenario: Update a recommendation with valid ids
    When I visit the "Home Page"
    And I set the "product_id" to "10"
    And I set the "related_product_id" to "22"
    And I set the "type_id" to "3"
    And I select "False" in the "status" dropdown
    And I press the "Update" button
    Then I should see the message "Success"
    When I press the "Clear" button
    And I set the "product_id" to "10"
    And I set the "related_product_id" to "22"
    And I press the "Retrieve" button
    Then I should see "3" in the "type_id" field
    And I should see "False" in the "status" field


Scenario: Update a recommendation with non-exists ids
    When I visit the "Home Page"
    And I set the "product_id" to "10"
    And I set the "related_product_id" to "99"
    And I set the "type_id" to "2"
    And I select "False" in the "status" dropdown
    And I press the "Update" button
    Then I should see the message "404 Not Found"