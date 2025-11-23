import argparse
import logging
import os.path
import re
import time

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.edge.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.safari.service import Service
from selenium.webdriver.firefox.service import Service

from repair.executor.repair_mode import RepairMode
from repair.statement.statement_serializer import deserialize
from repair.trace.tracer import Tracer


def main():
    parser = argparse.ArgumentParser(description='Web应用修复工具')
    parser.add_argument('--mode', required=True, choices=['trace', 'repair'], help='运行模式')
    parser.add_argument('--repair-mode', required=True, choices=['context', 'no_context'], help='修复模式')
    parser.add_argument('--testcase-path', required=True, help='测试用例文件路径')
    parser.add_argument('--trace-path', help='当运行模式为trace时，表示trace信息保存路径；当运行模式为repair时，表示修复所需trace信息加载路径；默认为测试用例路径加上.trace后缀')
    parser.add_argument('--repair-path', help='修复后的测试用例保存路径，默认为测试用例路径加上.repair后缀，仅repair运行模式下生效')
    parser.add_argument('--driver-type', required=True, choices=['chrome', 'edge', 'safari', 'firefox'])
    parser.add_argument('--driver-path', required=True, default='', help='驱动路径')
    parser.add_argument('--url-replacer', nargs='*', help='当运行模式为repair时，提供的正则替换表达式，用于将旧版本URL替换为新版本URL')
    args = parser.parse_args()
    try:
        logging.getLogger('sentence_transformers').setLevel(logging.CRITICAL + 1)
        logging.getLogger('torch').setLevel(logging.CRITICAL + 1)
        logging.getLogger('datasets').setLevel(logging.CRITICAL + 1)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
            # format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        mode = args.mode
        repair_mode = args.repair_mode
        test_case_path = args.testcase_path
        driver_type = args.driver_type
        driver_path = args.driver_path
        url_replacer = args.url_replacer
        if mode == 'repair':
            if url_replacer is None or len(url_replacer) == 0 or len(url_replacer) % 2 != 0:
                logging.error('--url-replacer必须非空，且包含偶数项')
                return
        trace_path = args.trace_path
        if trace_path is None or len(trace_path.strip()) == 0:
            trace_path = test_case_path + '.trace'
        # if os.path.exists(trace_path):
        #     logging.error('Trace文件' + trace_path + '已存在，请重新指定')
        #     return
        parent_dir = os.path.dirname(trace_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        repair_path = args.repair_path
        if repair_path is None or len(repair_path.strip()) == 0:
            repair_path = test_case_path + '.repair'
        # if os.path.exists(repair_path):
        #     logging.error('Repair文件' + trace_path + '已存在，请重新指定')
        #     return
        parent_dir = os.path.dirname(repair_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        with open(test_case_path, mode='r', encoding='utf-8') as file:
            content_str = file.read()
        statements = deserialize(content_str)
        if mode == 'trace':
            driver = get_driver(driver_type, driver_path)
            driver.maximize_window()
            tracer = Tracer(driver, statements, RepairMode.CONTEXT if repair_mode == 'context' else RepairMode.NO_CONTEXT)
            logging.info('开始trace')
            start = time.time()
            tracer.trace()
            tracer.write(trace_path)
            logging.info('结束trace，用时' + str(int(time.time() - start)) + '秒')
        else:
            logging.info('修复准备...')
            from repair.repair.repairer import Repairer
            driver = get_driver(driver_type, driver_path)
            driver.maximize_window()
            repairer = Repairer(driver, statements, Tracer.read(trace_path), lambda url: replace(url_replacer, url), RepairMode.CONTEXT if repair_mode == 'context' else RepairMode.NO_CONTEXT)
            logging.info('开始修复')
            start = time.time()
            repairer.repair()
            repairer.write(repair_path)
            logging.info('结束修复，用时' + str(int(time.time() - start)) + '秒')
    except:
        logging.error('未知错误！')

def replace(url_replacer, url):
    for i in range(0, len(url_replacer), 2):
        if re.match(url_replacer[i], url):
            return re.sub(url_replacer[i], url_replacer[i + 1], url)
    return url

def get_driver(driver_type, driver_path):
    if driver_type == 'chrome':
        service = selenium.webdriver.chrome.service.Service(executable_path=driver_path)
        options = webdriver.ChromeOptions()
        return webdriver.Edge(service=service, options=options)
    elif driver_type == 'edge':
        service = selenium.webdriver.edge.service.Service(executable_path=driver_path)
        options = webdriver.EdgeOptions()
        return webdriver.Edge(service=service, options=options)
    elif driver_type == 'safari':
        service = selenium.webdriver.safari.service.Service(executable_path=driver_path)
        options = webdriver.SafariOptions()
        return webdriver.Edge(service=service, options=options)
    else:
        service = selenium.webdriver.firefox.service.Service(executable_path=driver_path)
        options = webdriver.FirefoxOptions()
        return webdriver.Edge(service=service, options=options)



if __name__ == '__main__':
    main()