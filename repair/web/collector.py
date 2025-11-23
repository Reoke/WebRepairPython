from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from repair.web.element import Element


def collect1(driver, web_element_filter, *exclude_paths):
    return collect4(driver, '/html/body', True, web_element_filter, *exclude_paths)

def collect2(driver, add_root, web_element_filter, *exclude_paths):
    return collect4(driver, '/html/body', add_root, web_element_filter, *exclude_paths)

def collect3(driver, start_xpath, web_element_filter, *exclude_paths):
    return collect4(driver, start_xpath, True, web_element_filter, *exclude_paths)

def collect4(driver, start_xpath, add_root, web_element_filter, *exclude_paths):
    timeout = driver.timeouts.implicit_wait
    driver.implicitly_wait(0.)
    element_set = []
    try:
        web_element = driver.find_element(By.XPATH, start_xpath)
        xpath = Element.get_element_xpath(driver, web_element)
        if not xpath in exclude_paths:
            if add_root and web_element_filter(web_element):
                element_set.append(Element.from_auto_locator(driver, web_element))
            __collect__(driver, element_set, web_element, web_element_filter, *exclude_paths)
    finally:
        driver.implicitly_wait(timeout)
    return element_set


def __collect__(driver, element_set, web_element, web_element_filter, *exclude_paths):
    web_elements = web_element.find_elements(By.XPATH, './*')
    for child_web_element in web_elements:
        xpath = Element.get_element_xpath(driver, child_web_element)
        if child_web_element.size['height'] <= 0 or child_web_element.size['width'] <= 0 or 'svg' in xpath:
            continue
        if not xpath in exclude_paths:
            if web_element_filter(child_web_element):
                element_set.append(Element.from_auto_locator(driver, child_web_element))
            __collect__(driver, element_set, child_web_element, web_element_filter, exclude_paths)