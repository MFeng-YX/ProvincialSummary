import logging
import json

from pathlib import Path
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler

@dataclass
class Config():
    
    gpt: dict[str, list[str]] = field(default_factory=dict)
    report: dict[str, list[str]] = field(default_factory=dict)    
    day_datapath: str = field(default='./data/day')
    week_datapath: str = field(default='./data/week')
    report_datapath: str = field(default='./data/report')
  
    log_config: dict[str, any] = field(default_factory=lambda: {
        "log_file": "./logs/app.log",
        "level": "INFO",
        "max_bytes": 512 * 1024,  # 0.5MB
        "backup_count": 10
    })
    
    @classmethod
    def from_json(cls, json_path: str | Path = './config/config.json') -> 'Config':
        """读取json文件中的配置信息, 并加载到默认类中

        Args:
            json_path (str | Path, optional): json文件的文件路径. Defaults to './config/config.json'.

        Returns:
            Config: Config类实例对象
            
        Raises:
        (ValueError, TypeError): 文件路径不符合规范
        FileNotFoundError: JSON文件不存在
        json.JSONDecodeError: JSON格式错误
        """
        
        try:
            json_path = Path(json_path)
        except (ValueError, TypeError) as e:
            raise e("输入的文件路径不符合规范")
        
        if not json_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {json_path.absolute()}")
        
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Json文件格式错误: {e}", e.doc, e.pos)
        
        # required_field: set = {}       
        # missing_field = required_field - set(data.keys())
        # if missing_field:
        #     raise ValueError("Json文件缺少必要的字段")
        
        return cls(**data)
    
    
    def setup_logger(self) -> logging.Logger:
        """为项目初始化配置日志处理器

        Returns:
            logging.Logger: 日志处理器
        """
        
        log_file = self.log_config["log_file"]
        try:
            log_file = Path(log_file)
        except (ValueError, TypeError) as e:
            raise e("配置文件中的的文件路径不符合规范")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger = logging.getLogger("ProvincialSummary")
        level = getattr(logging, self.log_config['level'].upper())
        logger.setLevel(level)
        
        # 如果已经配置过，直接返回
        if logger.handlers:
            return logger
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.log_config["max_bytes"],
            backupCount=self.log_config["backup_count"],
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 重要：不要关闭传播（默认就是 True）
        # app_logger.propagate = True  # 这是默认值
        
        return logger