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

            if "运输" in node:
                df1.loc[idx, '新-延误量'] = cond.loc[:, "干线运输延误量"].iat[0]
                df1.loc[idx, "新-延误占比"] = cond.loc[:, "干线运输延误占比"].iat[0]
                
            if "交件" in node:
                df1.loc[idx, '新-延误量'] = cond.loc[:, "网点交件延误量"].iat[0]
                df1.loc[idx, "新-延误占比"] = cond.loc[:, "网点交件延误占比"].iat[0]
            
            if "派签" in node:
                df1.loc[idx, '新-延误量'] = cond.loc[:, "网点派签延误量"].iat[0]
                df1.loc[idx, "新-延误占比"] = cond.loc[:, "网点派签延误占比"].iat[0]
                
            if "进港" in node:
                df1.loc[idx, '新-延误量'] = cond.loc[:, "中心进港操作延误量"].iat[0]
                df1.loc[idx, "新-延误占比"] = cond.loc[:, "中心进港操作延误占比"].iat[0]
                
            if "出港" in node:
                df1.loc[idx, '新-延误量'] = cond.loc[:, "中心出港操作延误量"].iat[0]
                df1.loc[idx, "新-延误占比"] = cond.loc[:, "中心出港操作延误占比"].iat[0]
        
        single_dict = {
                "日期": "GPT展示日期",
                "城市线路": "城市线路名称",
                "与第一差值(%)": "复盘-与第一差值",
                "线路未达成量": "复盘-未达成量"
            }
        single_gpt = single_gpt.rename(columns=single_dict)
        single_gpt['GPT展示日期'] = pd.to_datetime(single_gpt["GPT展示日期"], format='mixed').dt.date
        single_gpt1 = single_gpt.loc[:, col_need]
        df2 = pd.merge(df1, single_gpt1, how="left", on=["GPT展示日期", "城市线路名称"])
        
        df2['复盘-延误量'] = None
        df2['复盘-延误占比'] = None
        
        for row in df2.itertuples():
            idx = row.Index
            route = row.城市线路名称
            node = str(row.核心影响环节)
            
            mask = single_gpt['城市线路名称'] == route
            cond = single_gpt.loc[mask, :]
            
            if cond.empty:
                continue

            if "路由" in node:
                df2.loc[idx, '复盘-延误量'] = cond.loc[:, "路由延误量"].iat[0]
                df2.loc[idx, "复盘-延误占比"] = cond.loc[:, "路由延误占比"].iat[0]

            if "运输" in node:
                df2.loc[idx, '复盘-延误量'] = cond.loc[:, "干线运输延误量"].iat[0]
                df2.loc[idx, "复盘-延误占比"] = cond.loc[:, "干线运输延误占比"].iat[0]
                
            if "交件" in node:
                df2.loc[idx, '复盘-延误量'] = cond.loc[:, "网点交件延误量"].iat[0]
                df2.loc[idx, "复盘-延误占比"] = cond.loc[:, "网点交件延误占比"].iat[0]
            
            if "派签" in node:
                df2.loc[idx, '复盘-延误量'] = cond.loc[:, "网点派签延误量"].iat[0]
                df2.loc[idx, "复盘-延误占比"] = cond.loc[:, "网点派签延误占比"].iat[0]
                
            if "进港" in node:
                df2.loc[idx, '复盘-延误量'] = cond.loc[:, "中心进港操作延误量"].iat[0]
                df2.loc[idx, "复盘-延误占比"] = cond.loc[:, "中心进港操作延误占比"].iat[0]
                
            if "出港" in node:
                df2.loc[idx, '复盘-延误量'] = cond.loc[:, "中心出港操作延误量"].iat[0]
                df2.loc[idx, "复盘-延误占比"] = cond.loc[:, "中心出港操作延误占比"].iat[0]
        
        set_mask = set(self.report['列顺序']) - set(list(df2.columns))
        if set_mask:
            summary_report: pd.DataFrame = df2.loc[:, self.report['列顺序']]
            return summary_report
        else:
            self.logger.error(f"报表缺失列: {set_mask}, 请检查代码逻辑")
            raise ValueError(f"报表缺失列: {set_mask}, 请检查代码逻辑")        


    def run(self) -> None:
        """该类的主运行方法
        """
        self.logger.info("-"*50)
        self.logger.info(f"功能主流程-开始")
        
        if self.number == 1:
            gpt: pd.DataFrame = self.gpt_production(self.number)
            self.data_export(gpt, "日")

        elif self.number == 2:
            gpt: pd.DataFrame = self.gpt_production(self.number)
            self.data_export(gpt, "周/月")
        
        elif self.number == 3:
            single_gpt: pd.DataFrame = self.gpt_production(1)
            multi_gpt: pd.DataFrame = self.gpt_production(2)
            summary_report: pd.DataFrame = self.report_production(single_gpt, multi_gpt)
            
            file_path: Path = self.output_path / f"省区汇总表.xlsx"
            with pd.ExcelWriter(str(file_path.resolve()), engine='openpyxl', mode="w") as writer:
                summary_report.to_excel(writer, sheet_name="省区汇总", index=False)
                single_gpt.to_excel(writer, sheet_name="单日GPT", index=False)
                multi_gpt.to_excel(writer, sheet_name="周/月GPT", index=False)
        
        self.logger.info(f"功能主流程-结束")
        self.logger.info("-"*50)