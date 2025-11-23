from __future__ import annotations
from selenium.webdriver.remote.webdriver import WebDriver

from repair.web.collector import collect1
from repair.web.filter import user_web_element_filter


class State:

    def __init__(self, driver):
        self.elements = collect1(driver, user_web_element_filter)
