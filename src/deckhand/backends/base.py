"""Backend 基类。所有发版后端继承此接口。"""

from abc import ABC, abstractmethod


class Backend(ABC):
    """发版自动化后端接口。"""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """人类可读的后端名称。"""

    @abstractmethod
    def generate(self, config) -> dict[str, str]:
        """生成配置文件。返回 {相对路径: 文件内容} 的字典。"""
