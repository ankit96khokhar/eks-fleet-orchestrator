import time
from app.logger import LoggerFactory
from app.jenkins_client import JenkinsClient
from app.argocd_client import ArgoCDCLient

logger = LoggerFactory.get_logger("blue-green")

class BlueGreenUpgradeStrategy:

    def __init__(self):
        pass

    def upgrade(self):
        pass

    def _create_green(self):
        pass

    def _destroy_blue(self):
        pass

    def _switch_traffic(self):
        pass
