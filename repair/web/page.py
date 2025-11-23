from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

class Page:

    def __init__(self, page):
        self.page = page

    @classmethod
    def from_driver(cls, driver):
        page_text = driver.find_element(By.XPATH, '/html/body').text
        return Page([line.strip() for line in page_text.split('\n') if line.strip()])

    def serialize(self):
        return self.page

    @classmethod
    def deserialize(cls, source):
        return Page(source)

    def __eq__(self, other):
        return isinstance(other, Page) and self.page == other.page

    def __hash__(self):
        return hash(tuple(self.page))