from selenium.webdriver.remote.webelement import WebElement


def user_web_element_filter(web_element):
    tag_name = web_element.tag_name
    location = web_element.location
    return web_element.is_displayed() and web_element.is_enabled() and tag_name.lower() != 'br' and tag_name.lower() != 'hr' and location['x'] >= 0 and location['y'] >= 0