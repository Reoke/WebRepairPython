import ast
from typing import List, Any

from repair.statement.assert_statement import AssertTextStatement
from repair.statement.driver_statement import DriverStatement
from repair.statement.element_statement import ElementStatement
from repair.statement.statements import Statements
from repair.statement.thread_sleep_statement import ThreadSleepStatement
from repair.web.element import Locator


def serialize(statements):
    scripts = []
    for item in statements:
        scripts.append(repr(item['statement']))
    return '\n'.join(scripts)

def deserialize(script):
    result = Statements()
    tree = ast.parse(script)  # 解析为AST
    for stmt in tree.body:

        # 处理assert语句（ast.Assert节点）
        if isinstance(stmt, ast.Assert):
            # 获取断言的核心表达式（如driver.find_element(...).text == '123'）
            test_expr = stmt.test
            if isinstance(test_expr, ast.Compare):
                # 解析比较表达式：left（左边）、ops（运算符）、comparators（右边）
                left_expr = test_expr.left
                operators = [_get_operator__(op) for op in test_expr.ops]
                expected_values = [_get_node_value__(node) for node in test_expr.comparators]
                # 只处理单运算符的比较（如A == B，不处理A > B and B < C等复杂情况）
                if len(operators) == 1 and len(expected_values) == 1:
                    op = operators[0]
                    if op != '==':  # 暂时只考虑相等的情况
                        continue
                    expected_val = expected_values[0]
                    # 解析左边表达式：driver.find_element('xx', 'xxx').attr（如.text）
                    if isinstance(left_expr, ast.Attribute):
                        # left_expr是"element.attr"（如element.text），需提取element和attr
                        attr_name = left_expr.attr  # 属性名（如text）
                        if attr_name != 'text':
                            continue
                        element_expr = left_expr.value  # element部分（如driver.find_element(...)）

                        # 检查element_expr是否是driver.find_element(...)调用
                        if isinstance(element_expr, ast.Call):
                            find_element_call = element_expr
                            if (isinstance(find_element_call.func, ast.Attribute) and
                                    find_element_call.func.attr == 'find_element' and
                                    isinstance(find_element_call.func.value, ast.Name) and
                                    find_element_call.func.value.id == 'driver'):
                                # 提取定位器信息
                                by = _get_node_value__(find_element_call.args[0]) if len(find_element_call.args) > 0 else ''
                                value = _get_node_value__(find_element_call.args[1]) if len(find_element_call.args) > 1 else ''
                                result.append({'line': stmt.lineno, 'statement': AssertTextStatement(None, Locator(by, value), expected_val)})
            continue  # 处理完assert后跳过其他逻辑



        if not isinstance(stmt, ast.Expr):
            continue  # 只处理表达式语句（函数调用类）
        call_node = stmt.value
        if not isinstance(call_node, ast.Call):
            continue  # 只处理函数调用
        func = call_node.func
        # 情况1：time.sleep(xxxx) → ['sleepStatement', xxxx]
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name) and func.value.id == 'time' and func.attr == 'sleep':
                sleep_time = _get_node_value__(call_node.args[0]) if call_node.args else None
                result.append({'line': stmt.lineno, 'statement': ThreadSleepStatement(sleep_time)})
                continue
        # 情况2：driver相关的driverStatement（如driver.get、driver.quit、driver.switch_to.alert.accept等）
        if isinstance(func, ast.Attribute):
            # 解析属性链（如driver.switch_to.alert.accept → ['driver', 'switch_to', 'alert', 'accept']）
            chain = _parse_driver_chain__(func)
            if len(chain) >= 2 and chain[0] == 'driver':  # 确保以driver开头
                # 基础结构：['driverStatement', 'driver', ...方法链...]
                if chain[1] in ('get', 'quit', 'refresh'):
                    result.append({'line': stmt.lineno, 'statement': DriverStatement(None, chain[1], _get_node_value__(call_node.args[0]) if len(call_node.args) > 0 else '')})
                elif len(chain) > 3 and chain[1] == 'switch_to' and chain[2] == 'alert':
                    result.append({'line': stmt.lineno, 'statement': DriverStatement(None, chain[2], chain[3])})
                continue
        # 情况3：driver.find_element(...).action(...) → ['elementStatement', 'driver', by, value, action, arg]
        if isinstance(func, ast.Attribute):
            # 外层action的调用者是find_element的结果（即func.value是find_element的Call节点）
            if isinstance(func.value, ast.Call):
                find_element_call = func.value
                # 检查内层是否是driver.find_element调用
                if isinstance(find_element_call.func, ast.Attribute) and find_element_call.func.attr == 'find_element' and isinstance(find_element_call.func.value, ast.Name) and find_element_call.func.value.id == 'driver':
                    # 提取定位器（by和value）
                    by = _get_node_value__(find_element_call.args[0]) if len(find_element_call.args) > 0 else ''
                    value = _get_node_value__(find_element_call.args[1]) if len(find_element_call.args) > 1 else ''
                    # 提取action（如click、send_keys）
                    action = func.attr
                    # 提取action的参数（无参则为''）
                    action_arg = _get_node_value__(call_node.args[0]) if call_node.args else ''
                    result.append({'line': stmt.lineno, 'statement': ElementStatement(None, Locator(by, value), action, action_arg)})
                    continue
        # 情况4：Select(driver.find_element(...)).xxx(...) → ['elementStatement', 'driver', by, value, select_method, method_arg]
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Call):
            # 外层是Select实例的方法调用（如select_by_visible_text），内层是Select(...)的调用
            select_instance_call = func.value
            if (isinstance(select_instance_call.func, ast.Name) and
                select_instance_call.func.id == 'Select'):
                # 提取Select的参数：必须是driver.find_element(...)调用
                if select_instance_call.args and isinstance(select_instance_call.args[0], ast.Call):
                    find_element_in_select = select_instance_call.args[0]
                    # 检查是否是driver.find_element调用
                    if isinstance(find_element_in_select.func, ast.Attribute) and find_element_in_select.func.attr == 'find_element' and isinstance(find_element_in_select.func.value, ast.Name) and find_element_in_select.func.value.id == 'driver':
                        # 提取定位器（by和value）
                        by = _get_node_value__(find_element_in_select.args[0]) if len(find_element_in_select.args) > 0 else ''
                        value = _get_node_value__(find_element_in_select.args[1]) if len(find_element_in_select.args) > 1 else ''
                        # 提取Select的方法（如select_by_visible_text）
                        select_method = func.attr
                        # 提取方法参数（如选择的值）
                        method_arg = _get_node_value__(call_node.args[0]) if call_node.args else ''
                        result.append({'line': stmt.lineno, 'statement': ElementStatement(None, Locator(by, value), select_method, method_arg)})
                        continue
    return result


def _get_node_value__(node):
    """辅助函数：提取AST节点的值（处理字符串、数字、变量等）"""
    if isinstance(node, ast.Str):
        return node.s
    elif isinstance(node, ast.Num):
        return node.n
    else:
        result = ast.unparse(node)
        if result.startswith('By.'):
            d = {
                'By.ID': 'id',
                'By.XPATH': 'xpath',
                'By.LINK_TEXT': 'link text',
                'By.PARTIAL_LINK_TEXT': 'partial link text',
                'By.NAME': 'name',
                'By.TAG_NAME': 'tag name',
                'By.CLASS_NAME': 'class name',
                'By.CSS_SELECTOR': 'css selector'
            }
            result = d[result]
        return result


def _parse_driver_chain__(func_node):
    """解析driver相关的属性链（如driver.switch_to.alert.accept → ['driver', 'switch_to', 'alert', 'accept']）"""
    chain = []
    current = func_node
    # 从最内层向外提取属性链
    while isinstance(current, ast.Attribute):
        chain.insert(0, current.attr)  # 插入到链头
        current = current.value
    # 最内层应为驱动名（如driver'）
    if isinstance(current, ast.Name):
        chain.insert(0, current.id)
    return chain

def _get_operator__(op):
    """将比较运算符节点转换为字符串（如ast.Eq → '=='）"""
    if isinstance(op, ast.Eq):
        return '=='
    elif isinstance(op, ast.NotEq):
        return '!='
    elif isinstance(op, ast.Lt):
        return '<'
    elif isinstance(op, ast.Gt):
        return '>'
    elif isinstance(op, ast.LtE):
        return '<='
    elif isinstance(op, ast.GtE):
        return '>='
    else:
        return ast.unparse(op)  # 其他运算符直接转为字符串
