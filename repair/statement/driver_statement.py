from __future__ import annotations
from selenium.webdriver.remote.webdriver import WebDriver

from repair.statement.statement import Statement

class DriverStatement(Statement):

    def __init__(self, driver, action, value):
        self.driver = driver
        if action not in ('get', 'quit', 'refresh', 'alert'):
            raise '非法行为'
        self.action = action
        self.value = value

    def act(self):
        if self.action == 'get':
            self.driver.get(self.value)
        elif self.action == 'quit':
            self.driver.quit()
        elif self.action == 'refresh':
            self.driver.refresh()
        elif self.action == 'alert':
            if self.value == 'accept':
                self.driver.switch_to.alert.accept()
            else:
                self.driver.switch_to.alert.dismiss()

    def __repr__(self):
        if self.action == 'get':
            return 'driver.get(' + repr(self.value) + ')'
        elif self.action == 'quit':
            return 'driver.quit()'
        elif self.action == 'refresh':
            return 'driver.refresh()'
        elif self.action == 'alert':
            if self.value == 'accept':
                return 'driver.switch_to.alert.accept()'
            else:
                return 'driver.switch_to.alert.dismiss()'
