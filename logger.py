import logging
import sys
import os

class Logger:
    def __init__(self, name: str = "MCPLogger", log_file: str = "app.log", log_level: str = "INFO"):
        # logディレクトリをlogger.pyのある場所に作成
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(base_dir, "log")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, log_file)

        self.logger = logging.getLogger(name)
        self.log_level = log_level.upper()  # log_level属性を追加
        
        if not self.logger.hasHandlers():
            level = getattr(logging, log_level.upper(), logging.INFO)
            self.logger.setLevel(level)
            formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')

            # Console handler - MCPサーバー実行時はstderrに出力してstdoutのJSON通信を妨げない
            ch = logging.StreamHandler(sys.stderr)
            ch.setLevel(level)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

            # File handler
            fh = logging.FileHandler(log_path)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg) 
    
    def warning(self, msg):
        self.logger.warning(msg)
    
    def error(self, msg):
        self.logger.error(msg)
    
    def critical(self, msg):
        self.logger.critical(msg) 
