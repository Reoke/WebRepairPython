import json
import logging

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.select import Select

from repair.executor.repair_mode import RepairMode
from repair.statement.assert_statement import AssertTextStatement
from repair.statement.driver_statement import DriverStatement
from repair.statement.element_statement import ElementStatement
from repair.statement.statement import Statement
from repair.statement.statements import Statements
from repair.statement.thread_sleep_statement import ThreadSleepStatement
from repair.web.context import Context
from repair.web.element import Element, Locator
from repair.web.page import Page


class Tracer:

    def __init__(self, driver, statements, repair_mode):
        for item in statements:
            statement = item['statement']
            if isinstance(statement, DriverStatement) or isinstance(statement, ElementStatement) or isinstance(statement, AssertTextStatement):
                statement.driver = driver
        self.statements = statements
        self.repair_mode = repair_mode
        self.results = []
        self.sleep_time = 0

    def trace(self):
        for statement in self.statements:
            logging.info("Trace语句：" + str(statement))
            self.__trace_one__(statement['statement'], statement['line'])

    def write(self, path):
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(self.results, file, ensure_ascii=False, indent=4)

    @classmethod
    def read(cls, path):
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def __trace_one__(self, statement, line):
        if isinstance(statement, DriverStatement):
            result = self.__trace_driver_statement__(statement)
        elif isinstance(statement, ThreadSleepStatement):
            result = self.__trace_thread_sleep__(statement)
        elif isinstance(statement, ElementStatement):
            result = self.__trace_find_element__(statement)
        elif isinstance(statement, AssertTextStatement):
            result = self.__trace_assert_text__(statement)
        else:
            raise '非法语句'
        result['line'] = line
        self.results.append(result)

    def __trace_driver_statement__(self, statement):
        statement.act()
        return {'statement': 'DriverStatement', 'action': statement.action, 'value': statement.value}

    def __trace_thread_sleep__(self, statement):
        statement.act()
        self.sleep_time += statement.sleep_time
        return {'statement': 'ThreadSleepStatement', 'sleep_time': statement.sleep_time}

    def __trace_find_element__(self, statement):
        result = {'statement': 'ElementStatement', 'locator_by': statement.locator.by, 'locator_value': statement.locator.value, 'action': statement.action, 'action_value': statement.value}
        web_element = statement.locator.to_web_element(statement.driver)
        element = Element.from_manual_locator(statement.driver, web_element, Locator(statement.locator.by, statement.locator.value))
        if self.repair_mode == RepairMode.CONTEXT:
            context = Context.from_element(statement.driver, element)
        else:
            context = Context([])
        page = Page.from_driver(statement.driver)
        result['element'] = element.serialize()
        result['context'] = context.serialize()
        result['page'] =  page.serialize()
        statement.act()
        if statement.action in ('select_by_visible_text', 'select_by_value', 'select_by_index'):
            result['option'] = Select(web_element).first_selected_option.text
        return result

    def __trace_assert_text__(self, statement):
        result = {'statement': 'AssertTextStatement', 'locator_by': statement.locator.by, 'locator_value': statement.locator.value, 'expected': statement.expected}
        web_element = statement.locator.to_web_element(statement.driver)
        element = Element.from_manual_locator(statement.driver, web_element, Locator(statement.locator.by, statement.locator.value))
        if self.repair_mode == RepairMode.CONTEXT:
            context = Context.from_element(statement.driver, element)
        else:
            context = Context([])
        page = Page.from_driver(statement.driver)
        result['element'] = element.serialize()
        result['context'] = context.serialize()
        result['page'] =  page.serialize()
        statement.act()
        return result
