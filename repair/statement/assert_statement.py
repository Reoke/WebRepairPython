from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from repair.statement.statement import Statement
from repair.web.element import Locator, Element


class AssertTextStatement(Statement):

    def __init__(self, driver, locator, expected):
        self.driver = driver
        self.locator = locator
        self.expected = expected


    def act(self):
        web_element = self.locator.to_web_element(self.driver)
        Element.scroll_to_view(self.driver, web_element)
        assert web_element.text == self.expected, f"断言失败：预期 {self.expected}，实际 {web_element.text}"

    def __repr__(self):
        return 'assert driver.find_element(' + repr(self.locator.by) + ',' + repr(self.locator.value) + ').text = ' + repr(self.expected)