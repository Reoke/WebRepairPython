import os
import sys

def get_resource_path(relative_path):
    """获取打包后资源的真实路径（兼容开发/打包环境）"""
    if getattr(sys, 'frozen', False):
        # 打包后运行：资源在临时解压目录 sys._MEIPASS
        base_path = sys._MEIPASS
    else:
        # 开发环境运行：资源在项目根目录（repair的上级目录）
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.join(base_path, relative_path)
