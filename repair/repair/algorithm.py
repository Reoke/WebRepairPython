from __future__ import annotations

import time

from selenium.webdriver.remote.webdriver import WebDriver

from repair.executor.repair_mode import RepairMode
from repair.semantic_model.application import encode_texts, sim_text2text, sim_text2image, sim_image2image
from repair.utils.pair import Pair
from repair.web.context import Context
from repair.web.element import Element
from repair.web.page import Page
from repair.web.state import State


class Algorithm:

    def __init__(self, page_num, page_threshold, last_state, invalid_state, on_path_filter, on_path_to_click_filter, algorithm_threshold, algorithm_move, repair_mode):
        self.page_num = page_num
        self.page_threshold = page_threshold
        self.last_state = last_state
        self.invalid_state = invalid_state
        self.on_path_filter = on_path_filter
        self.on_path_to_click_filter = on_path_to_click_filter
        self.algorithm_threshold = algorithm_threshold
        self.algorithm_move = algorithm_move
        self.repair_mode = repair_mode

    def get_element_on_path(self, driver, oe, oc, op, np, add_current_state):
        if self.on_path_filter is not None and not self.on_path_filter(driver, oe):
            return None
        url = driver.current_url
        if self.invalid_state and add_current_state:
            self.last_state = State(driver)
            self.invalid_state = False
        if self.on_path_to_click_filter is None:
            elements_for_iter = self.last_state.elements
        else:
            elements_for_iter = [i for i in self.last_state.elements if self.on_path_to_click_filter(driver, i)]
        page_locator_map = dict()
        old_windows = driver.window_handles
        driver.execute_script("window.open()")
        old_window = driver.current_window_handle
        new_window = self.__get_new_window__(old_windows, driver.window_handles)
        driver.switch_to.window(new_window)
        driver.set_page_load_timeout(1)
        is_get = True
        p1 = None
        for ne in elements_for_iter:
            try:
                if is_get:
                    driver.get(url)
                    p1 = Page.from_driver(driver)
                ne.to_web_element(driver).click()
                p2 = Page.from_driver(driver)
                if p1 != p2:
                    page_locator_map[p2] = ne
                    is_get = True
                else:
                    is_get = False
            except:
                is_get = True
        if add_current_state:
            page_locator_map[np] = None
        page_sim_list = []
        for key, value in page_locator_map.items():
            page_sim_list.append(Pair(key, self.get_page_similarity(key, op)))
        selected_pages = [item.first for item in sorted(page_sim_list, key=lambda o: -o.second)[:self.page_num]]
        if add_current_state and not np in selected_pages:
            selected_pages.append(np)
        for page in selected_pages:
            pe = page_locator_map[page]
            if pe is None:
                driver.switch_to.window(old_window)
            else:
                driver.switch_to.window(new_window)
                driver.get(url)
                try:
                    pe.to_web_element(driver).click()
                except:
                    pass
                time.sleep(2)
            ne = self.get_element_on_state2(driver, oe, oc, pe is not None)
            if ne is not None:
                driver.switch_to.window(new_window)
                driver.execute_script("window.close()")
                driver.switch_to.window(old_window)
                return Pair(pe, ne)
        driver.set_page_load_timeout(65.536)
        driver.switch_to.window(new_window)
        driver.execute_script("window.close()")
        driver.switch_to.window(old_window)
        return None

    def get_element_on_state(self, driver, oe, oc):
        return self.get_element_on_state2(driver, oe, oc, False)

    def get_element_on_state2(self, driver, oe, oc, from_path):
        web_elements = oe.locator.to_web_elements(driver)
        ne = self.get_element_on_locator(driver, oe, [Element.from_auto_locator(driver, i) for i in web_elements], oc)
        if ne is None:
            return self.search_element_on_state(driver, oe, oc, from_path)
        else:
            return ne

    def get_element_on_locator(self, driver, oe, nes, oc):
        if len(nes) == 1 and self.get_element_similarity(oe, nes[0]) >=self.algorithm_threshold:
            nes[0].locator = oe.locator
            return nes[0]
        max_s = 0
        max_e = None
        for ne in nes:
            if self.repair_mode == RepairMode.CONTEXT:
                nc = Context.from_element(driver, ne)
            else:
                nc = Context([])
            sim = self.get_context_similarity(oe, ne, oc, nc)
            if sim > max_s and sim >= self.algorithm_threshold:
                max_s = sim
                max_e = ne
        return max_e

    def search_element_on_state(self, driver, oe, oc, from_path):
        if self.invalid_state or from_path:
            ns = State(driver)
            self.__set_caches__(ns)
        else:
            ns = self.last_state
        if self.invalid_state and not from_path:
            self.last_state = ns
        max_s = 0
        max_e = None
        for ne in ns.elements:
            if self.repair_mode == RepairMode.CONTEXT:
                nc = Context.from_element_and_state(driver, ne, ns)
            else:
                nc = Context([])
            sim = self.get_context_similarity(oe, ne, oc, nc)
            if not (Element.relevant(max_e, ne) and oe.is_type_match(max_e) and not oe.is_type_match(ne)):
                if sim >= self.algorithm_threshold and Element.relevant(max_e, ne) and not oe.is_type_match(max_e) and oe.is_type_match(ne):
                    max_e = ne
                elif sim >= self.algorithm_threshold and sim >= max_s:
                    max_e = ne
            if sim >= max_s:
                max_s = sim
        if not from_path:
            self.invalid_state = False
        return max_e

    def is_page_match(self, op, np):
        return self.get_page_similarity(op, np) >= self.page_threshold

    def get_page_similarity(self, op, np):
        if len(op.page) == 0 and len(np.page) == 0:
            return 1
        if len(op.page) == 0 or len(np.page) == 0:
            return 0
        encode_texts(op.page)
        encode_texts(np.page)
        m = [[0. for _ in range(len(np.page))] for _ in range(len(op.page))]
        for i in range(len(op.page)):
            for j in range(len(np.page)):
                m[i][j] = sim_text2text(op.page[i], np.page[j])
        cnt = 0
        while self.__get_and_set_max__(m) >= self.algorithm_threshold:
            cnt += 1
        return cnt / (len(op.page) * len(np.page)) ** 0.5

    def get_context_similarity(self, oe, ne, oc, nc):
        sim = self.get_element_similarity(oe, ne)
        if len(oc.context) == 0 or len(nc.context) == 0:
            return sim
        m = [[0. for _ in range(len(nc.context))] for _ in range(len(oc.context))]
        for i in range(len(oc.context)):
            for j in range(len(nc.context)):
                m[i][j] = self.get_element_similarity(oc.context[i], nc.context[j])
        the_sum = 0.
        max_match = self.__get_and_set_max__(m)
        while max_match >= self.algorithm_threshold:
            the_sum = the_sum + (max_match - self.algorithm_threshold)
            max_match = self.__get_and_set_max__(m)
        c = 1
        return sim + self.algorithm_move * the_sum * c

    @classmethod
    def get_base_option(cls, original, targets):
        if original in targets:
            return original
        encode_texts(targets)
        max_s = 0
        the_max = None
        for target in targets:
            s = sim_text2text(original, target)
            if s > max_s:
                the_max = target
                max_s = s
        return the_max

    @classmethod
    def get_element_similarity(cls, oe, ne):
        text1 = oe.text
        text2 = ne.text
        if text1 is not None and text2 is not None:
            return sim_text2text(text1, text2)
        elif text1 is not None and ne.image is not None:
            return sim_text2image(text1, ne.image)
        elif text2 is not None and oe.image is not None:
            return sim_text2image(text2, oe.image)
        elif oe.image is not None and ne.image is not None:
            return sim_image2image(oe.image, ne.image)
        else:
            return 0

    @classmethod
    def __get_and_set_max__(cls, m):
        the_max = 0
        first = 0
        second = 0
        for i in range(len(m)):
            for j in range(len(m[0])):
                if m[i][j] > the_max:
                    the_max = m[i][j]
                    first = i
                    second = j
        for mm in m:
            mm[second] = 0
        for i in range(len(m[0])):
            m[first][i] = 0
        return the_max

    @classmethod
    def __get_new_window__(cls, old_windows, new_windows):
        for window in new_windows:
            if not window in old_windows:
                return window
        raise RuntimeError('error')

    @classmethod
    def __set_caches__(cls, state):
        strings = []
        the_bytes = []
        for element in state.elements:
            if element.text is not None:
                strings.append(element.text)
            elif element.image is not None and len(element.image) != 0:
                the_bytes.append(element.image)
        encode_texts(strings)
        encode_texts(the_bytes)