# 工具使用说明

## 测试用例编写规则

本工具支持修复Python编写的Selenium测试用例，支持以下模式编写的测试用例语句：

- 驱动操作：

  - URL访问：`driver.get('xxx')`
  - 退出浏览器：`driver.quit()`
  - 刷新页面：`driver.refresh()`
  - 弹出框：`driver.switch_to.alert.accept()`、`driver.switch_to.alert.dismiss()`

- 元素操作：

  - 文本输入：`driver.find_element(By.xx, "xx").send_keys("xx")`
  - 点击：`driver.find_element(By.xx, "xx").click()`
  - 文本清除：`driver.find_element(By.xx, "xx").clear()`

- 下拉框单选操作：

  - 根据可见文本选择：`Select(driver.find_element(By.xx, "xx")).select_by_visible_text('xx')`
  - 根据值选择：`Select(driver.find_element(By.xx, "xx")).select_by_value('xx')`
  - 根据索引选择：`Select(driver.find_element(By.xx, "xx")).select_by_index(xx)`

- 文本断言：`assert driver.find_element(By.xx, "xx").text == 'xx'`

- 线程睡眠：`time.sleep()`

## 程序入口说明

使用如下命令执行trace：

```sh
./repair.exe
--mode trace  # 运行模式，固定值
--repair-mode yourRepairMode  # trace算法，context：收集元素及其上下文信息；no_context：仅收集元素本身的信息
--testcase-path yourTestcasePath   # 测试用例文件路径
--trace-path yourTracePath  # trace信息保存路径，默认为测试用例路径加上.trace后缀
--driver-type yourDriverType  # 浏览器驱动类型：chrome、edge、safari或firefox
--driver-path yourDriverPath  # 浏览器驱动路径
```

使用如下命令执行修复：
```sh
./repair.exe
--mode repair  # 运行模式，固定值
--repair-mode yourRepairMode  # trace算法，context：收集元素及其上下文信息；no_context：仅收集元素本身的信息
--testcase-path yourTestcasePath   # 测试用例文件路径
--trace-path yourTracePath  # trace信息保存路径，默认为测试用例路径加上.trace后缀
--repair-path  # 修复后的测试用例保存路径，默认为测试用例路径加上.repair后缀
--driver-type yourDriverType  # 浏览器驱动类型：chrome、edge、safari或firefox
--driver-path yourDriverPath  # 浏览器驱动路径
--url-replacer find1 replace1 find2 replace2 ...  # 正则替换表达式，用于将旧版本URL替换为新版本URL
```

## 示例

给定测试用例如下：
```python
driver.get("http://localhost/opencart/opencart-v38-free/upload/admin/")
driver.find_element(By.ID, "input-username").send_keys("admin")
driver.find_element(By.ID, "input-password").send_keys("admin")
driver.find_element(By.CSS_SELECTOR, ".btn").click()
time.sleep(1)
assert driver.find_element(By.CSS_SELECTOR, ".dropdown-toggle > .hidden-xs").text == 'John'
driver.find_element(By.CSS_SELECTOR, ".hidden-sm").click()
time.sleep(1)
driver.quit()
```

对测试用例执行trace：

```sh
./repair.exe
--mode trace
--repair-mode context
--testcase-path testcase/login3_8.py
--trace-path trace/login3_8.trace
--driver-type edge
--driver-path driver/msedgedriver.exe
```

根据trace结果，对测试用例执行修复：

```sh
./repair.exe
--mode repair 
--repair-mode context
--testcase-path testcase/login3_8.py
--trace-path trace/login3_8.trace 
--repair-path repair/login3_8.repair 
--driver-type edge
--driver-path driver/msedgedriver.exe 
--url-replacer "http://localhost/opencart/opencart-v38-free/" "http://localhost/opencart/opencart-v41-ifree/"
```

修复后的结果如下：

```python
driver.get('http://localhost/opencart/opencart-v41-ifree/upload/admin/')
driver.find_element('id','input-username').send_keys('admin')
driver.find_element('id','input-password').send_keys('admin')
driver.find_element('css selector','.btn').click()
time.sleep(1)
assert driver.find_element('css selector','span.d-lg-inline').text = '   John Doe'
driver.find_element('xpath','/html[1]/body[1]/div[1]/header[1]/div[1]/ul[1]/li[4]/a[1]/span[1]').click()
time.sleep(1)
driver.quit()
```