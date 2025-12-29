from astrbot.api import logger
import json,os,re
from astrbot.api.star import StarTools
from typing import Dict, List, Optional
from pathlib import Path

class DataManager:
    def __init__(self, config_file: Path = None):
        if config_file is None:
            plugin_data_dir = StarTools.get_data_dir("mcstatus")
            config_file=plugin_data_dir / "mcstatus.json"
        self.config_file = config_file
        self.config_data = {}  # 使用字典存储多个标识符的配置
        
    
    def load_config(self) -> bool:
        try:
            if not os.path.exists(self.config_file):
                logger.info(f"配置文件 {self.config_file} 不存在，将创建新配置")
                self.save_config()
                return False
            
            with open(self.config_file, 'r', encoding='utf-8') as file:
                loaded_data = json.load(file)
                
            if loaded_data is not None and isinstance(loaded_data, dict):
                self.config_data = loaded_data
                return True
            else:
                logger.error("配置文件格式错误，使用空配置")
                self.config_data = {}
                self.save_config()
                return False
            
        except json.JSONDecodeError as e:
            logger.info(f"JSON解析错误: {e}")
            return False
        except Exception as e:
            logger.error(f"加载配置文件时发生错误: {e}")
            return False
    
    def save_config(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(self.config_data, file, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到 {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件时发生错误: {e}")
            return False
        
    @staticmethod
    def check_server_addr(server_addr: str) -> bool:
        if not server_addr or len(server_addr) > 253:
            return False
        pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*|((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))(:[1-9][0-9]{0,4}|:[1-5][0-9]{4}|:6[0-4][0-9]{3}|:65[0-4][0-9]{2}|:655[0-2][0-9]|:6553[0-5])?$'
        return bool(re.match(pattern, server_addr))

    def get_all_configs(self) -> Dict[str, str]:
        return self.config_data.copy()
    
    def get_server_addr(self, identifier: str) -> Optional[str]:
        return self.config_data.get(identifier)
    
    def add_server_addr(self, identifier: str, server_addr: str) -> bool:
        if not identifier or not server_addr:
            return False
        if not self.check_server_addr(server_addr):
            return False
        self.config_data[identifier] = server_addr
        self.save_config()
        return True
    
    def update_server_addr(self, identifier: str, new_server_addr: str) -> bool:
        if identifier not in self.config_data:
            return False
        if not self.check_server_addr(new_server_addr):
            return False
        self.config_data[identifier] = new_server_addr
        self.save_config()
        return True
    
    def remove_server_addr(self, identifier: str) -> bool:
        if identifier in self.config_data:
            del self.config_data[identifier]
            self.save_config()
            return True
        return False
    
    def clear_all_configs(self) -> bool:
        try:
            self.config_data.clear()
            self.save_config()
            return True
        except Exception as e:
            logger.error(f"清除数据失败，错误原因：{e}")
            return False
    
    def has_identifier(self, identifier: str) -> bool:
        return identifier in self.config_data