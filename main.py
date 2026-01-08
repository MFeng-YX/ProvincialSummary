import pandas as pd
import logging

from pathlib import Path

from config.config import Config
from src.process import Process

import warnings

warnings.filterwarnings(
    "ignore",
    message="Workbook contains no default style, apply openpyxl's default",
    category=UserWarning,
    module="openpyxl.styles.stylesheet"
)

if __name__ == "__main__":
    
    config: Config = Config.from_json()
    config.setup_logger()
    
    logger: logging.Logger = logging.getLogger(f"ProvincialSummary.{__name__}")
    
    logger.info("-"*50)
    logger.info("程序启动")
    
    while True:
        number: str = input("请输入你要进入的功能模块\n\t"
                       "1-单日GPT报表制作\n\t"
                       "2-周/月GPT报表制作\n\t"
                       "3-省区汇总报表制作:\n\t"
                       "4-不要运行直接退出\n\t"
                       "请输入数字(1或2或3或4):\t")
        
        if number not in ['1', '2', '3', '4']:
            logger.info("输入的功能模块编号不正确请重新输入！！！")
            print("输入的功能模块编号不正确请重新输入！！！")
            continue
        
        number: int = int(number)
        if number == 4:
            break
        
        need = input("请问是否需要将excel文件转换为csv文件\n\t"
                     "0-不需要\n\t"
                     "1-需要\t")
        
        if need not in ['0', '1']:
            logger.info("输入的功能模块编号不正确请重新输入！！！")
            print("输入的功能模块编号不正确请重新输入！！！")
            continue
        
        need: int = int(need)
        process: Process = Process(number, need)
        process.run()
        
        break
    

    logger.info("程序结束")
    logger.info("-"*50)