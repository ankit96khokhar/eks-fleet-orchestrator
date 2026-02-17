from app.logger import LoggerFactory
from app.exceptions import ConfigurationError

logger = LoggerFactory.get_logger("models")


class Cluster:

    def __init__(self, name: str, fleet: str, version: str,
                 is_canary: bool, tenant: str, env: str, region: str):

        self.name = name
        self.fleet = fleet
        self.version = version
        self.is_canary = is_canary
        self.tenant = tenant
        self.env = env
        self.region = region

    def identifier(self) -> str:
        return f"{self.tenant}-{self.env}-{self.name}"

    def __repr__(self):
        return f"<Cluster name={self.name} fleet={self.fleet} canary={self.is_canary}>"
    
    def green_name(self):
        return f"{self.name}-green-v{self.version.replace('.', '-')}"

