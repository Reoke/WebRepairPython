from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from repair.executor.repair_mode import RepairMode
from repair.utils.string_utils import occur_times, is_stop_word
from repair.web.collector import collect3
from repair.web.element import Element, RelativePosition
from repair.web.filter import user_web_element_filter
from repair.web.state import State


class Context:

    def __init__(self, elements):
        self.context = elements

    @classmethod
    def from_element(cls, driver, element):
        return Context(cls.__collect1__(driver, element))

    @classmethod
    def from_element_and_state(cls, driver, element, state):
        return Context(cls.__collect2__(driver, element, state))

    def serialize(self):
        return [element.serialize() for element in self.context]

    @classmethod
    def deserialize(cls, source):
        return Context([Element.deserialize(item) for item in source])

    @classmethod
    def __collect1__(cls, driver, element):
        context = []
        path = element.xpath
        cnt = occur_times(path, '/')
        cls.__add_if_not_null__(context, element.get_virtual_element(driver))
        while len(context) == 0 and cnt > 2:
            prev = path
            path = path[:path.rfind('/')]
            cnt -= 1
            elements = collect3(driver, path, user_web_element_filter, prev)
            context.extend(elements)
            cls.__reserve_basic_elements__(context, element, path)
        return cls.__filtered_context__(context, element)

    @classmethod
    def __collect2__(cls, driver, element, state):
        context = []
        path = element.xpath
        cnt = occur_times(path, '/')
        cls.__add_if_not_null__(context, element.get_virtual_element(driver))
        while len(context) == 0 and cnt > 2:
            prev = path
            path = path[:path.rindex('/')]
            cnt -= 1
            for e in state.elements:
                if path in e.xpath and not prev in e.xpath:
                    context.append(e)
            cls.__reserve_basic_elements__(context, element, path)
        return cls.__filtered_context__(context, element)

    @classmethod
    def __filtered_context__(cls, context, element):
        result = []
        up = None
        down = None
        right = None
        left = None
        d_up = float('inf')
        d_down = float('inf')
        d_right = float('inf')
        d_left = float('inf')
        for ce in context:
            pair = ce.get_relative_position(element)
            if pair.first == RelativePosition.OVERLAP:
                result.append(ce)
            elif pair.first == RelativePosition.UP:
                if pair.second < d_up:
                    up = ce
                    d_up = pair.second
            elif pair.first == RelativePosition.DOWN:
                if pair.second < d_down:
                    down = ce
                    d_down = pair.second
            elif pair.first == RelativePosition.RIGHT:
                if pair.second < d_right:
                    right = ce
                    d_right = pair.second
            elif pair.first == RelativePosition.LEFT:
                if pair.second < d_left:
                    left = ce
                    d_left = pair.second
        cls.__add_if_not_null__(result, up, down, right, left)
        for ce in context:
            pair1 = ce.get_relative_position(element)
            pair2 = None
            if pair1.first == RelativePosition.UP:
                pair2 = ce.get_relative_position(up)
                if (pair2.first == RelativePosition.RIGHT or pair2.first == RelativePosition.LEFT or pair2.first == RelativePosition.OVERLAP) and ce != up:
                    result.append(ce)
            elif pair1.first == RelativePosition.DOWN:
                pair2 = ce.get_relative_position(down)
                if (pair2.first == RelativePosition.RIGHT or pair2.first == RelativePosition.LEFT or pair2.first == RelativePosition.OVERLAP) and ce != down:
                    result.append(ce)
            elif pair1.first == RelativePosition.RIGHT:
                pair2 = ce.get_relative_position(up)
                if (pair2.first == RelativePosition.UP or pair2.first == RelativePosition.DOWN or pair2.first == RelativePosition.OVERLAP) and ce != right:
                    result.append(ce)
            elif pair1.first == RelativePosition.LEFT:
                pair2 = ce.get_relative_position(up)
                if (pair2.first == RelativePosition.UP or pair2.first == RelativePosition.DOWN or pair2.first == RelativePosition.OVERLAP) and ce != left:
                    result.append(ce)
        return result


    @classmethod
    def __add_if_not_null__(cls, the_list, *elements):
        for element in elements:
            if element is not None:
                the_list.append(element)

    @classmethod
    def __reserve_basic_elements__(cls, elements, element, root_path):
        the_map = dict()
        the_map[element.xpath] = element
        for e in elements:
            the_map[e.xpath] = e
        for path, value in the_map.items():
            if value.text is not None and is_stop_word(value.text):
                if value in elements:
                    elements.remove(value)
            path = path[:path.rindex('/')]
            parent = None
            while parent is None and root_path in path:
                parent = the_map.get(path)
                path = path[:path.rindex('/')]
            if parent is not None and (not cls.__valid_text__(parent) or cls.__valid_text__(value)):
                if parent in elements:
                    elements.remove(parent)

    @classmethod
    def __valid_text__(cls, element):
        return element.text is not None and not is_stop_word(element.text)

    @classmethod
    def __valid_image__(cls, element):
        return element.image is not None and len(element.image) != 0
