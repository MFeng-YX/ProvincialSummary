import pandas as pd
import logging

from pathlib import Path

from config.config import Config

class DataProcess():
    
    logger = logging.getLogger(f"ProvincialSummary.{__name__}")
    config: Config = Config.from_json()

    def __init__(self, number: int):
        """初始化 DataProcess 类实例

        Args:
            number (int): 功能数字编号
        """
        self.number: int = number
        self.day: str = self.config.day_datapath
        self.week: str = self.config.week_datapath
        self.report: str = self.config.report_datapath

    
    def excel_to_csv(self, path: Path) -> Path:
        """将excel文件转换成csv文件

        Args:
            path (Path): excel文件路径

        Returns:
            Path: csv文件路径
        """


    def path_read(self, path: Path) -> list[Path]:
        """读取文件夹中的文件路径

        Args:
            path (Path): 文件夹路径

        Returns:
            list[Path]: 文件路径列表
        """

        path_list: list[Path] = list()

        for p in path.iterdir():
            path_list.append(p)

        return path_list
    

    def run(self) -> list[Path]:
        """该类的主运行方法

        Returns:
            list[Path]: 生成的文件夹路径列表
        """

        if self.number == 1:
            path: Path = Path(self.day)
        elif self.number == 2:
            path: Path = Path(self.week)
        elif self.number == 3:
            path: Path = Path(self.report)
        else:
            self.logger.error(f"传入的功能数字编号错误: {self.number}, 请核实代码")
            raise ValueError(f"传入的功能数字编号错误: {self.number}")
        
        path_list: list[Path] = self.path_read(path)
        
        return path_list