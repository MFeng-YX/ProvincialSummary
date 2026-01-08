import pandas as pd
import logging

from pathlib import Path
from tqdm import tqdm

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
        """制作省区汇总报表"""
        # ------------------------------------------------------------------
        # 1. 读取省区文件（与您原逻辑完全一致）
        # ------------------------------------------------------------------
        for p in self.path_list:
            if "省区" in p.name:
                provincial: pd.DataFrame = pd.read_csv(p, skiprows=[0], encoding='utf-8-sig')
            
            if "全量线路" in p.name:
                total_route: pd.DataFrame = pd.read_csv(p)
        # 仅此处改成 .ffill() 去掉 FutureWarning
        provincial = provincial.copy().ffill()

        # ------------------------------------------------------------------
        # 2. 重命名 + 日期转换（与您原逻辑完全一致）
        # ------------------------------------------------------------------
        name_dict = {
            "日期": "GPT展示日期",
            "城市线路": "城市线路名称",
            "与第一差值(%)": "与第一差值（核实）",
            "线路未达成量": "未达成量（核实）"
        }
        multi_gpt = multi_gpt.rename(columns=name_dict)
        provincial["GPT展示日期"] = pd.to_datetime(provincial["GPT展示日期"], format="mixed").dt.date
        # multi_gpt["GPT展示日期"] = pd.to_datetime(multi_gpt["GPT展示日期"], format="mixed").dt.date

        # ------------------------------------------------------------------
        # 3. 第一次合并： provincial × multi_gpt（列选取逻辑不变）
        # ------------------------------------------------------------------
        multi_need = ["GPT展示日期", "城市线路名称", "与第一差值（核实）", "未达成量（核实）"]
        multi_gpt1 = multi_gpt.loc[:, multi_need]
        df1 = pd.merge(provincial, multi_gpt1, how="left", on=["GPT展示日期", "城市线路名称"])

        # 新增空列（与原逻辑一致）
        df1["延误量（核实）"] = None
        df1["延误占比（核实）"] = None

        # ====== 向量化填充：用 tqdm 显示进度 ======
        node_map = {
            "路由": ("路由延误量", "路由占比"),
            "运输": ("干线运输延误量", "干线运输占比"),
            "交件": ("网点交件延误量", "网点交件占比"),
            "派签": ("网点派签延误量", "网点派签占比"),
            "进港": ("中心进港操作延误量", "中心进港操作占比"),
            "出港": ("中心出港操作延误量", "中心出港操作占比"),
        }

        for node, (qty_col_src, pct_col_src) in tqdm(node_map.items(), desc="新-映射"):
            mask = df1["核心影响环节"].astype(str).str.contains(node, na=False)
            if mask.sum() == 0:
                continue
            keys = ['GPT展示日期', '城市线路名称']
            temp = (df1.loc[mask, keys]
                    .merge(multi_gpt[keys + [qty_col_src, pct_col_src]],
                        on=keys, how='left')
                    .groupby(keys)                    # 若出现多行，先聚合
                    .first()                           # 取第一行（或.mean()）
                    .reindex(df1.loc[mask, keys])      # 再对齐到 mask 的键顺序
                )

            df1.loc[mask, '延误量（核实）']   = temp[qty_col_src].values
            df1.loc[mask, '延误占比（核实）'] = temp[pct_col_src].values

        # ------------------------------------------------------------------
        # 4. 第二次合并： df1 × single_gpt（列选取逻辑不变）
        # ------------------------------------------------------------------
        single_dict = {
            "日期": "GPT展示日期",
            "城市线路": "结果（复盘）",
            "与第一差值(%)": "与第一差值（复盘）",
            "线路未达成量": "未达成量（复盘）"
        }
        single_gpt = single_gpt.rename(columns=single_dict)
        single_gpt["GPT展示日期"] = pd.to_datetime(single_gpt["GPT展示日期"], format="mixed").dt.date

        single_need = ["结果（复盘）", "与第一差值（复盘）", "未达成量（复盘）"]
        single_gpt1 = single_gpt.loc[:, single_need]
        df2 = pd.merge(df1, single_gpt1, how="left", left_on='城市线路名称', right_on="结果（复盘）")
        df2['结果（复盘）'].fillna("消除", inplace=True)

        # 新增空列（与原逻辑一致）
        df2["延误量（复盘）"] = None
        df2["延误占比（复盘）"] = None


        # ====== 向量化填充：用 tqdm 显示进度 ======
        for node, (qty_col_src, pct_col_src) in tqdm(node_map.items(), desc="复盘-映射"):
            mask = df2["核心影响环节"].astype(str).str.contains(node, na=False)
            if mask.sum() == 0:
                continue
            keys = ['GPT展示日期', '城市线路名称', "结果（复盘）"]          # 本次只用单列做键

            temp = (
                df2.loc[mask, keys]                      # 1. 子集键
                .merge(
                    single_gpt[["结果（复盘）"] + [qty_col_src, pct_col_src]],  # 2. 右表数值
                    how="left",
                    on="结果（复盘）"
                )
                .groupby(keys)                            # 3. 若出现多对多，先聚合到唯一键
                .first()                                  #   取第一行（或 .mean() / .sum()）
                .reindex(df2.loc[mask, keys])             # 4. 对齐到 mask 的键顺序
            )

            # 5. 长度已保证 = mask.sum()，安全赋值
            df2.loc[mask, "延误量（复盘）"]   = temp[qty_col_src].values
            df2.loc[mask, "延误占比（复盘）"] = temp[pct_col_src].values

        # ------------------------------------------------------------------
        # 5. 列顺序校验 & 返回（与原逻辑完全一致）
        # ------------------------------------------------------------------
        
        total_need = ["线路名称", "与第一差值(%)"]
        total_dict = {
            "线路名称": "城市线路名称",
            "与第一差值(%)": "与第一差值（全量）"
        }
        
        total_route = total_route.copy().loc[:, total_need]
        total_route = total_route.rename(columns=total_dict)
        
        result = pd.merge(df2, total_route, on="城市线路名称", how="left")
        diffdata = result['与第一差值（核实）'].copy().astype(str).apply(
            lambda x: float(x[:-1])/100 if any(char.isdigit() for char in x) else 0
        )
        
        result["与第一差值（全量）"] = result["与第一差值（全量）"] / 10000
        result['差值变化'] = result["与第一差值（全量）"] - diffdata
        result['差值变化'] = result['差值变化'].apply(lambda x: f"{x: .2%}")
        result["与第一差值（全量）"] = result["与第一差值（全量）"].apply(lambda x: f"{x: .2%}")
        
        result['与第一差值'] = result['与第一差值'].apply(
            lambda x: float(x) if any(char.isdigit() for char in x) else 0
        )
        result['与第一差值'] = result['与第一差值'].astype(float).apply(
            lambda x: f"{x * 100: .2f}%" 
        )
        # result['延误占比'] = result['延误占比'].apply(
        #     lambda x: float(x) if any(char.isdigit() for char in x) else 0
        # )
        # result['延误占比'] = result['延误占比'].astype(float).apply(
        #     lambda x: f"{x: .2f}%" 
        # )

        set_mask = set(self.report['列顺序']) - set(list(result.columns))
        if set_mask:
            self.logger.error(f"报表缺失列: {set_mask}, 请检查代码逻辑")
            raise ValueError(f"报表缺失列: {set_mask}, 请检查代码逻辑")
        else:
            summary_report: pd.DataFrame = result.loc[:, self.report['列顺序']]
        return summary_report      


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
                single_gpt.to_excel(writer, sheet_name="单日-GPT", index=False)
                multi_gpt.to_excel(writer, sheet_name="周或月-GPT", index=False)
        
        self.logger.info(f"功能主流程-结束")
        self.logger.info("-"*50)