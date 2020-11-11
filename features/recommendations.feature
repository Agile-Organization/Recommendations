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

Scenario: List all active recommendations
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see a recommendation from "1" to "2" with type "1"
    And I should see a recommendation from "1" to "3" with type "2"
    And I should not see a recommendation from "1" to "4" with type "3"

