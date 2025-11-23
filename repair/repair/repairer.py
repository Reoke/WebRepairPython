from __future__ import annotations

import logging
import time

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.select import Select

from repair.executor.repair_mode import RepairMode
from repair.repair.algorithm import Algorithm
from repair.statement.assert_statement import AssertTextStatement
from repair.statement.driver_statement import DriverStatement
from repair.statement.element_statement import ElementStatement
from repair.statement.statement import Statement
from repair.statement.statements import Statements
from repair.statement.thread_sleep_statement import ThreadSleepStatement
from repair.web.context import Context
from repair.web.element import Element
from repair.web.page import Page


class Repairer:

    def __init__(self, driver, statements, trace_results, url_replacer, repair_mode):
        for item in statements:
            statement = item['statement']
            if isinstance(statement, DriverStatement) or isinstance(statement, ElementStatement) or isinstance(statement, AssertTextStatement):
                statement.driver = driver
        self.statements = statements
        self.trace_results = trace_results
        self.url_replacer = url_replacer
        self.repaired_statements = []
        self.sleep_time = 0
        self.ignored_time = 0
        self.algorithm = Algorithm(
            page_num=3,
            page_threshold=0,
            last_state=None,
            invalid_state=True,
            on_path_filter=None,
            on_path_to_click_filter=None,
            algorithm_threshold=0.6,
            algorithm_move=0.75,
            repair_mode=repair_mode
        )
        self.last_element = None

    def repair(self):
        for statement, result in zip(self.statements, self.trace_results):
            logging.info("修复语句：" + str(statement))
            self.__repair_one__(statement['statement'], result)

    def write(self, path):
        with open(path, 'w', encoding='utf-8') as file:
            file.write('\n'.join(repr(i) for i in self.repaired_statements))

    def __repair_one__(self, statement, trace_result):
        if isinstance(statement, DriverStatement):
            self.repaired_statements.append(self.__repair_driver_statement__(statement))
        elif isinstance(statement, ThreadSleepStatement):
            self.repaired_statements.append(self.__repair_thread_sleep__(statement))
        elif isinstance(statement, ElementStatement) or isinstance(statement, AssertTextStatement):
            self.repaired_statements.extend(self.__repair_find_element__(statement, trace_result))
        else:
            raise '非法语句'

    def __repair_driver_statement__(self, statement):
        if statement.action == 'get':
            result = DriverStatement(statement.driver, statement.action, self.url_replacer(statement.value))
        else:
            result = DriverStatement(statement.driver, statement.action, statement.value)
        result.act()
        self.algorithm.invalid_state = True
        return result

    def __repair_thread_sleep__(self, statement):
        result = ThreadSleepStatement(statement.sleep_time)
        result.act()
        self.sleep_time += result.sleep_time
        return result

    def __repair_find_element__(self, statement, trace_result):
        oe = Element.deserialize(trace_result['element'])
        if oe.text is None and oe.image is None:
            logging.warning("Invalid element retrieved")
            return self.__confirm__(statement.driver, None, None, statement, None)
        oc = Context.deserialize(trace_result['context'])
        op = Page.deserialize(trace_result['page'])
        np = Page.from_driver(statement.driver)
        option = trace_result.get('option')
        if self.algorithm.is_page_match(op, np):
            ne = self.algorithm.get_element_on_state(statement.driver, oe, oc)
            if ne is not None and ne.locator == oe.locator:
                logging.info("No Breakage: " + str(oe.locator))
                return self.__confirm__(statement.driver, ne, None, statement, option)
            elif ne is not None:
                logging.info("Breakage repair: " + str(oe.locator) + " -> [" + str(ne.locator) + "]")
                return self.__confirm__(statement.driver, ne, None, statement, option)
            else:
                path = self.algorithm.get_element_on_path(statement.driver, oe, oc, op, np, False)
                if path is not None:
                    logging.info("Breakage repair: " + str(oe.locator) + " -> [" + str(path.first.locator) + ", " + str(path.second.locator) + "]")
                    return self.__confirm__(statement.driver, path.second, path.first, statement, option)
                else:
                    logging.info("Breakage repair: " + str(oe.locator) + " -> []")
                    return self.__confirm__(statement.driver, None, None, statement, option)
        else:
            path = self.algorithm.get_element_on_path(statement.driver, oe, oc, op, np, True)
            if path is not None:
                if path.first is None and path.second.locator == oe.locator:
                    logging.info("No Breakage: " + str(oe.locator))
                    return self.__confirm__(statement.driver, path.second, None, statement, option)
                elif path.first is None:
                    logging.info("Breakage repair: " + str(oe.locator) + " -> [" + str(path.second.locator) + "]")
                    return self.__confirm__(statement.driver, path.second, None, statement, option)
                else:
                    logging.info("Breakage repair: " + str(oe.locator) + " -> [" + str(path.first.locator) + ", " + path.second.getLocator() + "]")
                    return self.__confirm__(statement.driver, path.second, path.first, statement, option)
            else:
                logging.info("Breakage repair: " + str(oe.locator) + " -> []")
                return self.__confirm__(statement.driver, None, None, statement, option)

    def __confirm__(self, driver, ne, path, statement, option):
        result = []
        if path is not None:
            self.last_element = None
            self.algorithm.invalid_state = True
            item = ElementStatement(driver, path.locator, 'click', '')
            item.act()
            self.__handle_alert__(driver)
            result.append(item)
            self.algorithm.invalid_state = True
            self.__handle_alert__(driver)
            time.sleep(2)
            self.ignored_time += 2
        if isinstance(statement, ElementStatement):
            if ne is not None:
                self.last_element = ne
                if statement.action not in ('select_by_visible_text', 'select_by_value', 'select_by_index'):
                    item = ElementStatement(statement.driver, ne.locator, statement.action, statement.value)
                else:
                    web_element = ne.to_web_element(driver)
                    if web_element.is_enabled() and web_element.tag_name.lower() == 'select':
                        select = Select(web_element)
                        options = [i.text for i in select.options]
                        best_option = self.algorithm.get_base_option(option, options)
                        if best_option != option:
                            logging.info("Select breakage: " + option + " -> " + best_option)
                    item = ElementStatement(statement.driver, ne.locator, 'select_by_visible_text', best_option)
                item.act()
                result.append(item)
                if statement.action not in ('get', 'is'):
                    self.algorithm.invalid_state = True
                if statement.action in ('click', 'submit'):
                    self.__handle_alert__(driver)
                    self.ignored_time += 2
            else:
                self.last_element = None
        else:
            if ne is not None:
                self.last_element = ne
                web_element = ne.to_web_element(driver)
                item = AssertTextStatement(statement.driver, ne.locator, web_element.text)
                item.act()
                result.append(item)
            else:
                self.last_element = None
        return result

    @classmethod
    def __handle_alert__(cls, driver):
        while True:
            try:
                driver.switch_to.alert.accept()
                time.sleep(2)
            except:
                break