import pandas as pd
import logging

from pathlib import Path

from config.config import Config
from src.report.GPT import GPT


class MainProcess():
    """功能主流程
    """

    config: Config = Config.from_json()
    logger: logging.Logger = logging.getLogger(f"ProvincialSummary.{__name__}")

    def __init__(self, number: int, path_list: list[Path]):
        """初始化 MainProcess 类实例

        Args:
            number (int): 功能数字编码
            path_list (list[Path]): 数据文件路径
        """

        self.number: int = number
        self.path_list: list[Path] = path_list
        self.report: dict[str, list[str]] = self.config.report
        self.output_path: Path = Path(self.config.output_path)

    
    def gpt_production(self, number: int) -> pd.DataFrame:
        """制作GPT表格

        Args:
            number (int): 功能数字编码

        Returns:
            pd.DataFrame: GPT表格
        """

        Gpt: GPT = GPT(number, self.path_list)
        gpt: pd.DataFrame = Gpt.run()

        return gpt
    

    def data_export(self, df: pd.DataFrame, prefix: str) -> None:
        """输出报表

        Args:
            df (pd.DataFrame): 需输出的表格
            prefix (str): 输出表格的前缀
        """

        file_path: Path = self.output_path / f"{prefix}-GPT报表.xlsx"
        df.to_excel(file_path, index=False)

        self.logger.info(f"{file_path.name}已经成功保存.")

        return None
    

    def report_production(self, single_gpt: pd.DataFrame, multi_gpt: pd.DataFrame) -> pd.DataFrame:
        """制作省区汇总报表

        Args:
            single_gpt (pd.DataFrame): 单日GPT报表
            multi_gpt (pd.DataFrame): 周/月GPT报表

        Returns:
            pd.DataFrame: 省区汇总表
        """

        for p in self.path_list:
            if "省区" in p.name:
                provincial: pd.DataFrame = pd.read_excel(p, skiprows=[0])
        provincial = provincial.copy().fillna(method="ffill")

        col_need = ["日期", "城市线路", "与第一差值(%)", "线路未达成量"]
        name_dict = {
                "日期": "GPT展示日期",
                "城市线路": "城市线路名称",
                "与第一差值(%)": "新-与第一差值",
                "线路未达成量": "新-未达成量"
            }

        multi_gpt = multi_gpt.rename(columns=name_dict)

        provincial["GPT展示日期"] = pd.to_datetime(provincial["GPT展示日期"], format="mixed").dt.date
        multi_gpt["GPT展示日期"] = pd.to_datetime(multi_gpt["GPT展示日期"], format="mixed").dt.date

        multi_gpt1 = multi_gpt.loc[:, col_need]
        df1 = pd.merge(provincial, multi_gpt1, how="left", on=["GPT展示日期", "城市线路名称"])
        df1["新-延误量"] = None
        df1["新-延误占比"] = None

        for row in df1.itertuples():
            idx = row.Index
            route = row.城市线路名称
            date_ = row.GPT展示日期
            node = str(row.核心影响环节)

            mask = (multi_gpt['GPT展示日期'] == date_) & (multi_gpt['城市线路名称'] == route)
            cond = multi_gpt.loc[mask, :]

            if cond.empty:
                continue

            if "路由" in node:
                df1.loc[idx, '新-延误量'] = cond.loc[:, "路由延误量"].iat[0]
                df1.loc[idx, "新-延误占比"] = cond.loc[:, "路由延误占比"].iat[0]



    def run(self) -> None:
        """该类的主运行方法
        """

        if self.number == 1:
            gpt: pd.DataFrame = self.gpt_production(self.number)
            self.data_export(gpt, "日")

        elif self.number == 2:
            gpt: pd.DataFrame = self.gpt_production(self.number)
            self.data_export(gpt, "周/月")
        
        elif self.number == 3:
            single_gpt: pd.DataFrame = self.gpt_production(1)
            multi_gpt: pd.DataFrame = self.gpt_production(2)
