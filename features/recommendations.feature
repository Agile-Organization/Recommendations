Feature: The recommendation service back-end
    As a recommendation service
    I need a RESTful catalog service
    So that I can keep track of all the recommendations

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
