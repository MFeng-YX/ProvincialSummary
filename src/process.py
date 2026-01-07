import pandas as pd
import logging

from pathlib import Path

from config.config import Config
from src.dataprocess.dataprocess import DataProcess
from src.report.mainprocess import MainProcess


class Process():
    """全流程逻辑
    """
    
    logger: logging.Logger = logging.getLogger(f'ProvincialSummary.{__name__}')
    config: Config = Config.from_json()
    
    def __init__(self, number: int, need: int = 1):
        """初始化 Process 类实例

        Args:
            number (int): 功能数字编号
            need (int): 是否需要转换csv文件, 1为需要/0为不需要. Defaults to 1.
        """
        
        self.number: int = number
        self.need: int = need
    
    
    def run(self) -> None:
        """该类的主运行方法
        """
        
        dataprocess: DataProcess = DataProcess(self.number, self.need)
        path_list: list[Path] = dataprocess.run()
        
        mainprocess: MainProcess = MainProcess(self.number, path_list)
        mainprocess.run()