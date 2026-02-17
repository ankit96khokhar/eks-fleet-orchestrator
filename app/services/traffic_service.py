import time
from app.logger import LoggerFactory

logger = LoggerFactory.get_logger("traffic-service")


class TrafficService:

    def switch_to_green(self, cluster):
        logger.info(f"Switching traffic to GREEN for {cluster.name}")
        time.sleep(2)
        logger.info("Traffic switched to GREEN")

    def switch_to_blue(self, cluster):
        logger.info(f"Switching traffic back to BLUE for {cluster.name}")
        time.sleep(2)
        logger.info("Traffic switched back to BLUE")
