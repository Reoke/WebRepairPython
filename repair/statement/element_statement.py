from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.select import Select

from repair.statement.statement import Statement
from repair.web.element import Element, Locator


class ElementStatement(Statement):

    def __init__(self, driver, locator, action, value):
        self.driver = driver
        self.locator = locator
        if action not in ('send_keys', 'click', 'clear', 'select_by_visible_text', 'select_by_value', 'select_by_index'):
            raise '非法行为'
        self.action = action
        self.value = value

    def act(self):
        web_element = self.locator.to_web_element(self.driver)
        Element.scroll_to_view(self.driver, web_element)
        if self.action == 'send_keys':
            web_element.send_keys(self.value)
        elif self.action == 'click':
            web_element.click()
        elif self.action == 'clear':
            web_element.clear()
        elif self.action == 'select_by_visible_text':
            Select(web_element).select_by_visible_text(self.value)
        elif self.action == 'select_by_value':
            Select(web_element).select_by_value(self.value)
        elif self.action == 'select_by_index':
            Select(web_element).select_by_index(self.value)

    def __repr__(self):
        prefix = 'driver.find_element(' + repr(self.locator.by) + ',' + repr(self.locator.value) + ')'
        if self.action == 'send_keys':
            return prefix + '.send_keys(' + repr(self.value) + ')'
        elif self.action == 'click':
            return prefix + '.click()'
        elif self.action == 'clear':
            return prefix + '.clear()'
        elif self.action in ['select_by_visible_text', 'select_by_value', 'select_by_index']:
            return 'Select(' + prefix + ').' + self.action + '(' + repr(self.value) + ')'
