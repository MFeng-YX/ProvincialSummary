import pandas as pd
import logging
import chardet

from pathlib import Path

from config.config import Config


class GPT():
    """制作报表'GPT'的类
    """
    
    config: Config = Config.from_json()
    logger: logging.Logger = logging.getLogger(f"ProvincialSummary.{__name__}")
    
    def __init__(self, number: int, path: list[Path]):
        """初始化GPT类实例

        Args:
            number (int): 功能数字编码
            path (list[Path]): GPT涉及表格的路径列表
        """
        
        self.number: int = number
        self.path: list[Path] = path
        self.gpt: dict[str, list[str]] = self.config.gpt
    
    
    def data_read(self) -> list[pd.DataFrame]:
        """读取需要的文件数据

        Returns:
            list[pd.DataFrame]: 读取的文件数据列表
        """

        delay_list: list[pd.DataFrame] = list()
        city_list: list[pd.DataFrame] = list()

        if self.number == 1:
            path = [p for p in self.path if len(p.name) < 15]
        
        if self.number == 2:
            path = [p for p in self.path if len(p.name) >= 15]

        for p in path:
            print(p.name)
            if "延误量" in p.name:
                df_delay: pd.DataFrame = pd.read_csv(p, encoding='utf-8-sig')
                delay_list.append(df_delay)
                
            if "城市线路" in p.name:
                df_city: pd.DataFrame = pd.read_csv(p, encoding='utf-8-sig')
                city_list.append(df_city)
        
        delay_quantity: pd.DataFrame = pd.concat(delay_list, axis=0)
        city_route: pd.DataFrame = pd.concat(city_list, axis=0)
        self.logger.info(f"延误量表格 总行数: {len(delay_quantity)}")
        self.logger.info(f"城市线路表格 总行数: {len(city_route)}")
        
        dq_columns = self.gpt['各环节延误量'] + self.gpt['计算列']      
        delay_quantity = delay_quantity.loc[:, dq_columns]
        
        city_route = city_route.loc[:, self.gpt['城市线路']]
        
        self.logger.info("GPT报表所需数据读取完成.")
        
        return [delay_quantity, city_route]
    
    
    def report_production(self, df_list: list[pd.DataFrame]) -> pd.DataFrame:
        """制作GPT报表

        Args:
            df_list (list[pd.DataFrame]): 表格数据

        Returns:
            pd.DataFrame: GPT报表
        """
        
        delay_quantity, city_route = df_list

        df = pd.merge(
            city_route, delay_quantity, 
            how='left', 
            left_on=['日期', '城市线路名称'], right_on=['日期', '城市线路名称']
        ).rename(columns={"城市线路名称": "城市线路"})
        
        df_cal = df.loc[:, self.gpt['计算列']]
        df_cal["sum"] = df_cal.sum(axis=1)
        
        cal_cols: list[str] = list()
        for col in self.gpt["计算列"]:
            new_col = col[:-3] + "占比"
            df_cal[new_col] = df_cal[col] / df_cal['sum']
            df_cal[new_col] = df_cal[new_col].apply(lambda x: f"{x: .2%}")
            cal_cols.append(col)
            cal_cols.append(new_col)
        
        df_cal = df_cal.loc[:, cal_cols]
        calc_cols = set(self.gpt['计算列'])  # 转为集合，O(1)查找
        column_need = [col for col in df.columns if col not in calc_cols]
        df_name = df.loc[:, column_need]
        result = pd.concat([df_name, df_cal], axis=1)
        
        result = result.rename(columns={"标准": "标准时效"})
        cols = result.columns.tolist()
        cols.insert(4, cols.pop(cols.index("延误量最大3环节")))
        result = result.loc[:, cols]
        
        result['达成率(%)'] = result['达成率(%)'].apply(lambda x: f"{x: .2f}%")
        result['与第一差值(%)'] = result['与第一差值(%)'].apply(lambda x: f"{x: .2f}%")
    
        self.logger.info("GPT报表制作完成.")
        
        return result
    
    
    def run(self) -> pd.DataFrame:
        """该类的主运行方法

        Returns:
            pd.DataFrame: GPT报表
        """
        self.logger.info("-"*50)
        self.logger.info(f"功能-{self.number}: GPT报表制作流程-开始")
        
        df_list = self.data_read()
        delay_quantity, city_route = df_list
        delay_quantity['日期'] = pd.to_datetime(delay_quantity['日期'], format='mixed').dt.date
        city_route['日期'] = pd.to_datetime(city_route['日期'], format="mixed").dt.date

        if self.number == 1:
            gpt = self.report_production([delay_quantity, city_route])

        elif self.number == 2:
            date_set = set(delay_quantity['日期'].unique()).intersection(set(city_route['日期'].unique()))
            gpt_list: list[pd.DataFrame] = list()
            for date_ in list(date_set):
                delay_df = delay_quantity.loc[delay_quantity['日期'] == date_, :]
                city_df = city_route.loc[city_route['日期'] == date_]
                result = self.report_production([delay_df, city_df])
                gpt_list.append(result)
            
            gpt = pd.concat(gpt_list, axis=0)
            gpt.sort_values(by=['日期', "城市线路"], inplace=True)
        
        self.logger.info(f"功能-{self.number}: GPT报表制作流程-结束")
        self.logger.info("-"*50)
        
        return gpt