import yaml
import os
class Config:
    def __init__(self):
        self.c = self.load_config()
        self.self_id = self.c.get('bot',{}).get('self_id', 0)
        self.ws_host = self.c.get('ws',{}).get('host', '127.0.0.1')
        self.ws_port = self.c.get('ws',{}).get('port', 3001)

    def load_config(self):
        try:
            with open(f'{os.getcwd()}/config/config.yml', 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}