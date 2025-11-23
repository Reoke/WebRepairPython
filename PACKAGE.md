# 打包说明

1. 安装*pyinstaller*
    ```sh
    pip install pyinstaller
    ```
2. 使用*pyinstaller*打包成exe文件：
    ```sh
    pyinstaller -F --add-data "resources:resources" repair/main/repairer.py  # 打包为单文件，启动时需要将所有内容解压到系统临时目录（默认是 C:\Users\用户名\AppData\Local\Temp\_MEIxxxxxx），比较慢
    pyinstaller -D --add-data "resources:resources" repair/main/repairer.py  # 打包为目录
    ```
3. 使用加密管理工具，加密并设置exe文件的有效期，确保只有在有效期内插入加密狗才能使用（只提供有限的保护）。