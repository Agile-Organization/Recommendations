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

WAIT_SECONDS = int(getenv('WAIT_SECONDS', '60'))
ID_PREFIX = 'recommendation_'

@given('the following recommendations')
def step_impl(context):
    """ Delete all Recommendations and load new ones """
    headers = {'Content-Type': 'application/json'}
    # list all of the pets and delete them one by one
    context.resp = requests.get(context.base_url + '/recommendations', headers=headers)
    expect(context.resp.status_code).to_equal(200)
    for recommendation in context.resp.json():
        context.resp = requests.delete(context.base_url + '/recommendations/' + str(recommendation["product-id"]) + "/" + str(recommendation["related-product-id"]) , headers=headers)
        expect(context.resp.status_code).to_equal(204)
    
    # load the database with new pets
    create_url = context.base_url + '/recommendations'
    for row in context.table:
        data = {
            "product-id": int(row['product_id']),
            "related-product-id": int(row['related_product_id']),
            "type-id": int(row['type_id']),
            "status": row['status'] in ['True', 'true', '1']
            }
        payload = json.dumps(data)
        context.resp = requests.post(create_url, data=payload, headers=headers)
        expect(context.resp.status_code).to_equal(201)

@when('I visit the "home page"')
def step_impl(context):
    """ Make a call to the base URL """
    context.driver.get(context.base_url)

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
    element.select_by_visible_text(text)

@when('I press the "{button}" button')
def step_impl(context, button):
    button_id = button.lower() + '-btn'
    context.driver.find_element_by_id(button_id).click()

@then('I should see the message "{message}"')
def step_impl(context, message):
    found = WebDriverWait(context.driver, WAIT_SECONDS).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, 'flash_message'),
            message
        )
    )
    expect(found).to_be(True)

@then('I should see a recommendation from "{product_id}" to "{related_product_id}" with type "{type_id}"')
def step_impl(context, product_id, related_product_id, type_id):
    #found = WebDriverWait(context.driver, WAIT_SECONDS).until(
    #    expected_conditions.text_to_be_present_in_element(
    #        (By.ID, 'search_results'),
    #        product_id + " " + related_product_id + " " + type_id + " true"
    #    )
    #)
    #expect(found).to_be(True)

    element = context.driver.find_element_by_id('search_results')
    found = False
    rows = element.find_elements(By.TAG_NAME, "tr")
    for row in rows:
        cols = row.text.split(' ')
        if cols[0] == product_id and cols[1] == related_product_id:
            expect(row.text).to_equal(product_id + " " + related_product_id + " " + type_id + " true")
            found = True
            break
    expect(found).to_be(True)

@then('I should not see a recommendation from "{product_id}" to "{related_product_id}" with type "{type_id}"')
def step_impl(context, product_id, related_product_id, type_id):
    element = context.driver.find_element_by_id('search_results')
    not_found = True
    rows = element.find_elements(By.TAG_NAME, "tr")
    for row in rows:
        cols = row.text.split(' ')
        if cols[0] == product_id and cols[1] == related_product_id and cols[2] == type_id:
            not_found = False
            break
    expect(not_found).to_be(True)
