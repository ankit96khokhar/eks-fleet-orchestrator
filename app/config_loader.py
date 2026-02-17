import yaml
from app.logger import LoggerFactory
from app.exceptions import ConfigurationError


logger = LoggerFactory.get_logger("config-loader")


class ConfigLoader:

    REQUIRED_TOP_LEVEL = [
        "tenant",
        "env",
        "region",
        "account_id",
        "services"
    ]

    @staticmethod
    def load(file_path: str) -> dict:
        logger.info(f"Loading configuration file: {file_path}")

        try:
            with open(file_path, "r") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load YAML: {e}")
            raise ConfigurationError("Invalid YAML file")

        ConfigLoader.validate(config)

        logger.info("Configuration loaded successfully")
        return config

    @staticmethod
    def validate(config: dict):

        if not isinstance(config, dict):
            raise ConfigurationError("Config must be a dictionary")

        for field in ConfigLoader.REQUIRED_TOP_LEVEL:
            if field not in config:
                raise ConfigurationError(f"Missing required field: {field}")

        if not config["services"].get("eks", {}).get("enabled", False):
            raise ConfigurationError("EKS must be enabled in config")

        logger.info("Configuration validation passed")
