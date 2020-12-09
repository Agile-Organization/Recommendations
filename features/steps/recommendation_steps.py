from os import getenv
import logging
import json
import requests
from behave import *
from service import app
from compare import expect, ensure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import StaleElementReferenceException

WAIT_SECONDS = int(getenv("WAIT_SECONDS", "60"))
ID_PREFIX = "recommendation_"


@given("the following recommendations")
def step_impl(context):
    """ Delete all Recommendations and load new ones """
    headers = {"Content-Type": "application/json"}
    # list all of the recommendations and delete them one by one
    context.resp = requests.get(context.base_url + "/api/recommendations")
    expect(context.resp.status_code).to_equal(200)
    for recommendation in context.resp.json():
        context.resp = requests.delete(
            context.base_url
            + "/api/recommendations/"
            + str(recommendation["product-id"])
            + "/"
            + str(recommendation["related-product-id"]),
            headers=headers,
        )
        expect(context.resp.status_code).to_equal(204)

    # load the database with new recommendations
    create_url = context.base_url
    for row in context.table:
        data = {
            "product-id": int(row["product-id"]),
            "related-product-id": int(row["related-product-id"]),
            "type-id": int(row["type-id"]),
            "status": row["status"] == "True",
        }
        payload = json.dumps(data)
        context.resp = requests.post(
            create_url 
            + "/api/recommendations",
            data=payload, 
            headers=headers)
        expect(context.resp.status_code).to_equal(201)


@when('I visit the "home page"')
def step_impl(context):
    """ Make a call to the base URL """
    context.driver.get(context.base_url)


@then('I should see "{message}" in the title')
def step_impl(context, message):
    """ Check the document title for a message """
    expect(context.driver.title).to_contain(message)


@then('I should not see "{message}"')
def step_impl(context, message):
    error_msg = "I should not see '%s' in '%s'" % (message, context.resp.text)
    ensure(message in context.resp.text, False, error_msg)


@when('I set the "{element_name}" to "{text_string}"')
def step_impl(context, element_name, text_string):
    element_id = ID_PREFIX + element_name.lower()
    element = context.driver.find_element_by_id(element_id)
    element.clear()
    element.send_keys(text_string)


@when('I select "{text}" in the "{element_name}" dropdown')
def step_impl(context, text, element_name):
    element_id = ID_PREFIX + element_name.lower()
    element = Select(context.driver.find_element_by_id(element_id))
    element.select_by_value(text)


@when('I press the "{button}" button')
def step_impl(context, button):
    button_id = button.lower() + "-btn"
    context.driver.find_element_by_id(button_id).click()


@then('I should see the message "{message}"')
def step_impl(context, message):
    found = WebDriverWait(context.driver, WAIT_SECONDS).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, "flash_message"), message
        )
    )
    expect(found).to_be(True)


class element_in_a_table(object):
    def __init__(self, locator, product_id, related_product_id, type_id):
        self.locator = locator
        self.product_id = product_id
        self.related_product_id = related_product_id
        self.type_id = type_id

    def __call__(self, driver):
        element = driver.find_element_by_id(self.locator)
        rows_number = len(element.find_elements(By.TAG_NAME, "tr"))
        rows = element.find_elements(By.TAG_NAME, "tr")
        for i in range(rows_number):
            try:
                cols = rows[i].text.split(" ")
                if (
                    cols[0] == self.product_id
                    and cols[1] == self.related_product_id
                    and cols[2] == self.type_id):
                    return True
            except StaleElementReferenceException:
                rows = element.find_elements(By.TAG_NAME, "tr")
                cols = rows[i].text.split(" ")
                if (
                    cols[0] == self.product_id
                    and cols[1] == self.related_product_id
                    and cols[2] == self.type_id):
                    return True
        return False

@then(
    'I should see a recommendation from "{product_id}" to "{related_product_id}" with type "{type_id}"'
)
def step_impl(context, product_id, related_product_id, type_id):
    found = WebDriverWait(context.driver, WAIT_SECONDS).until(
        element_in_a_table("search_results", product_id, related_product_id, type_id)
    )
    expect(found).to_be(True)


class element_not_in_a_table(object):
    def __init__(self, locator, product_id, related_product_id, type_id):
        self.locator = locator
        self.product_id = product_id
        self.related_product_id = related_product_id
        self.type_id = type_id

    def __call__(self, driver):
        element = driver.find_element_by_id(self.locator)
        rows_number = len(element.find_elements(By.TAG_NAME, "tr"))
        rows = element.find_elements(By.TAG_NAME, "tr")
        for i in range(rows_number):
            try:
                cols = rows[i].text.split(" ")
                if (
                    cols[0] == self.product_id
                    and cols[1] == self.related_product_id
                    and cols[2] == self.type_id):
                    return False
            except StaleElementReferenceException:
                rows = element.find_elements(By.TAG_NAME, "tr")
                cols = rows[i].text.split(" ")
                if (
                    cols[0] == self.product_id
                    and cols[1] == self.related_product_id
                    and cols[2] == self.type_id):
                    return False
        return True

@then(
    'I should not see a recommendation from "{product_id}" to "{related_product_id}" with type "{type_id}"'
)
def step_impl(context, product_id, related_product_id, type_id):
    not_found = WebDriverWait(context.driver, WAIT_SECONDS).until(
        element_not_in_a_table(
            "search_results", product_id, related_product_id, type_id
        )
    )
    expect(not_found).to_be(True)


@then('I should see "{value}" in the "{element_name}" field')
def step_impl(context, value, element_name):
    element_id = ID_PREFIX + element_name.lower()
    found = WebDriverWait(context.driver, WAIT_SECONDS).until(
        expected_conditions.text_to_be_present_in_element_value(
            (By.ID, element_id), value
        )
    )
    expect(found).to_be(True)


@then('the "{element_name}" field should be empty')
def step_impl(context, element_name):
    element_id = ID_PREFIX + element_name.lower()
    element = context.driver.find_element_by_id(element_id)
    expect(element.get_attribute("value")).to_be("")


##################################################################
# These two function simulate copy and paste
##################################################################
@when('I copy the "{element_name}" field')
def step_impl(context, element_name):
    element_id = ID_PREFIX + element_name.lower()
    element = WebDriverWait(context.driver, WAIT_SECONDS).until(
        expected_conditions.presence_of_element_located((By.ID, element_id))
    )
    context.clipboard = element.get_attribute("value")
    logging.info("Clipboard contains: %s", context.clipboard)


@when('I paste the "{element_name}" field')
def step_impl(context, element_name):
    element_id = ID_PREFIX + element_name.lower()
    element = WebDriverWait(context.driver, WAIT_SECONDS).until(
        expected_conditions.presence_of_element_located((By.ID, element_id))
    )
    element.clear()
    element.send_keys(context.clipboard)
