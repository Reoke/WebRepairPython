from __future__ import annotations

import base64
import time
from enum import Enum

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from repair.utils.pair import Pair
from repair.utils.string_utils import is_blank


class Element:

    def __init__(self, xpath, position, size, the_type, text, image, locator):
        self.xpath = xpath
        self.position = position
        self.size = size
        self.type = the_type
        self.text = text
        self.image = image
        self.locator = locator

    @classmethod
    def from_manual_locator(cls, driver, web_element, locator):
        cls.scroll_to_view(driver, web_element)
        xpath = cls.get_element_xpath(driver, web_element)
        position = Position.from_point(web_element.location)
        size = Dimension.from_dimension(web_element.size)
        result = Element(xpath, position, size, Type.ORDINARY, None, None, locator)
        result.set_type(web_element)
        result.set_text(web_element)
        result.set_image(driver, web_element)
        return result

    @classmethod
    def from_auto_locator(cls, driver, web_element):
        locator = cls.generate_robust(driver, web_element)
        return cls.from_manual_locator(driver, web_element, locator)

    def is_type_match(self, element):
        return self.type == element.type or (self.type == Type.VIRTUAL_INPUT and element.type == Type.INPUT) or (self.type == Type.INPUT and element.type == Type.VIRTUAL_INPUT)

    def get_relative_position(self, element):
        if element is None:
            return Pair(RelativePosition.OTHER, float('inf'))
        horizontal_overlap = self.position.x + self.size.width > element.position.x and element.position.x + element.size.width > self.position.x
        vertical_overlap = self.position.y + self.size.height > element.position.y and element.position.y + element.size.height > self.position.y
        if not horizontal_overlap and not vertical_overlap:
            return Pair(RelativePosition.OTHER, float('inf'))
        if horizontal_overlap and vertical_overlap:
            return Pair(RelativePosition.OVERLAP, 0.)
        if horizontal_overlap:
            if self.position.y + self.size.height <= element.position.y:
                return Pair(RelativePosition.UP, float(element.position.y - self.position.y))
            else:
                return Pair(RelativePosition.DOWN, float(self.position.y - element.position.y))
        if self.position.x + self.size.width <= element.position.x:
            return Pair(RelativePosition.LEFT, float(element.position.x - self.position.x))
        else:
            return Pair(RelativePosition.RIGHT, float(self.position.x - element.position.x))

    def to_web_element(self, driver):
        return driver.find_element(By.XPATH, self.xpath)

    @classmethod
    def is_parent(cls, element1, element2):
        if element1 is None or element2 is None or element1.xpath is None or element2.xpath is None:
            return False
        return element1.xpath in element2.xpath  # 不一定正确

    @classmethod
    def relevant(cls, element1, element2):
        return cls.is_parent(element1, element2) or cls.is_parent(element2, element1)

    @classmethod
    def get_element_xpath(cls, driver, element):
        return driver.execute_script('''
        var getElementXPath = function(element) {return getElementTreeXPath(element);};var getElementTreeXPath = function(element) {var paths = [];for (; element && element.nodeType == 1; element = element.parentNode)  {var index = 0;for (var sibling = element.previousSibling; sibling; sibling = sibling.previousSibling) {if (sibling.nodeType == Node.DOCUMENT_TYPE_NODE) {continue;}if (sibling.nodeName == element.nodeName) {++index;}}var tagName = element.nodeName.toLowerCase();var pathIndex = ("[" + (index+1) + "]");paths.splice(0, 0, tagName + pathIndex);}return paths.length ? "/" + paths.join("/") : null;};return getElementXPath(arguments[0]);
        ''', element)

    def get_virtual_element(self, driver):
        if self.type == Type.VIRTUAL_INPUT:
            web_element = self.to_web_element(driver)
            element = Element.from_auto_locator(driver, web_element)
            element.image = None
            element.text = web_element.get_property('placeholder')
            return element
        return None

    @classmethod
    def get_text(cls, web_element):
        text = web_element.text
        if is_blank(text):
            text = web_element.get_property('textContent')
        tag_name = web_element.tag_name.lower()
        element_type = web_element.get_property('type')
        if is_blank(text) and (tag_name == 'textarea' or (tag_name == 'input' and not element_type == 'radio' and not element_type == 'checkbox')):
            text = web_element.get_property("value")
        if is_blank(text):
            return None
        return text.strip()

    @classmethod
    def scroll_to_view(cls, driver, web_element):
        if not cls.is_element_in_view_port(driver, web_element):
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", web_element)
        time.sleep(0.5)

    @classmethod
    def is_element_in_view_port(cls, driver, web_element):
        return driver.execute_script("""
                    var elem = arguments[0];
                    var rect = elem.getBoundingClientRect();
                    return (
                        rect.top >= 0 &&
                        rect.left >= 0 &&
                        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                    );
                """, web_element)

    def set_text(self, web_element):
        self.text = web_element.text
        if is_blank(self.text):
            self.text = web_element.get_property("textContent")
        tag_name = web_element.tag_name.lower()
        element_type = web_element.get_property("type")
        if is_blank(self.text) and (tag_name == 'textarea' or (tag_name == 'input' and not element_type == 'radio' and not element_type == 'checkbox')):
            self.text = web_element.get_property("value")
        if is_blank(self.text):
            self.text = None
        else:
            self.text = self.text.strip()

    def set_image(self, driver, web_element):
        if self.text is None:
            try:
                placeholder = web_element.get_property("placeholder")
                if self.type == Type.INPUT and not is_blank(placeholder):
                    driver.execute_script("arguments[0].setAttribute('placeholder', '')", web_element)
                    self.type = Type.VIRTUAL_INPUT
                    self.image = web_element.screenshot_as_png
                    driver.execute_script("arguments[0].setAttribute('placeholder', '" + placeholder + "')", web_element)
                else:
                    self.image = web_element.screenshot_as_png
            except:
                self.image = None
        else:
            self.image = None

    def set_type(self, web_element):
        tag_name = web_element.tag_name.lower()
        if tag_name == 'select':
            self.type = Type.SELECT
        elif tag_name in ('input', 'textarea'):
            self.type = Type.INPUT
        else:
            self.type = Type.ORDINARY

    def serialize(self):
        return {
            'xpath': self.xpath,
            'position': (self.position.x, self.position.y),
            'size': (self.size.width, self.size.height),
            'type': self.type.value,
            'text': self.text,
            'image': None if self.image is None else base64.b64encode(self.image).decode('utf-8'),
            'locator': (self.locator.by, self.locator.value)
        }

    @classmethod
    def deserialize(cls, source):
        return Element(
            source['xpath'],
            Position(source['position'][0], source['position'][1]),
            Dimension(source['size'][0], source['size'][1]),
            Type(source['type']),
            source['text'],
            None if source['image'] is None else base64.b64decode(source['image']),
            Locator(source['locator'][0], source['locator'][1]))

    @classmethod
    def generate_robust(cls, driver, web_element):
        tag_name = web_element.tag_name.lower()
        the_id = web_element.get_dom_attribute('id')
        name = web_element.get_dom_attribute('name')
        class_name = web_element.get_dom_attribute('class')
        text = web_element.text.strip()
        if the_id is not None and len(the_id) > 0:
            if cls.__is_unique__(driver, By.ID, the_id):
                return Locator(By.ID, the_id)
        if name is not None and len(name) > 0:
            if cls.__is_unique__(driver, By.NAME, name):
                return Locator(By.NAME, name)
        if tag_name == 'a' and len(text) > 0:
            if cls.__is_unique__(driver, By.LINK_TEXT, text):
                return Locator(By.LINK_TEXT, text)
        if class_name is not None and len(class_name) > 0:
            classes = class_name.strip().split()
            for clss in classes:
                if len(clss) > 0:
                    if cls.__is_unique__(driver, By.CSS_SELECTOR, tag_name + '.' + clss):
                        return Locator(By.CSS_SELECTOR, tag_name + '.' + clss)
        return Locator(By.XPATH, Element.get_element_xpath(driver, web_element))

    @classmethod
    def __is_unique__(cls, driver, by, value):
        return len(driver.find_elements(by, value)) == 1



class Position:

    def __init__(self, x, y):
        self.x = x
        self.y = y

    @classmethod
    def from_point(cls, point):
        return Position(point['x'], point['y'])


class Dimension:

    def __init__(self, width, height):
        self.width = width
        self.height = height

    @classmethod
    def from_dimension(cls, dimension):
        return cls(dimension['width'], dimension['height'])


class RelativePosition(Enum):
    UP = 'up'
    DOWN = 'down'
    RIGHT = 'right'
    LEFT = 'left'
    OVERLAP = 'overlap'
    OTHER = 'other'


class Locator:
    def __init__(self, by, value):
        self.by = by
        self.value = value

    def to_web_element(self, driver):
        return driver.find_element(self.by, self.value)

    def to_web_elements(self, driver):
        return driver.find_elements(self.by, self.value)

    def __eq__(self, other):
        return isinstance(other, Locator) and self.by == other.by and self.value == other.value

    def __hash__(self):
        return hash((self.by, self.value))

    def __repr__(self):
        return '(' + repr(self.by) + ', ' + repr(self.value) + ')'


class Type(Enum):
    SELECT = 'select'
    INPUT = 'input'
    VIRTUAL_INPUT = 'virtual_input'
    ORDINARY = 'ordinary'
