import sys
from app.logger import LoggerFactory
from app.config_loader import ConfigLoader
from app.exceptions import FleetUpgradeException
from app.orchestrator import FleetOrchestrator


logger = LoggerFactory.get_logger("main")


def main():

    if len(sys.argv) != 2:
        logger.error("Usage: python -m app.main <config.yaml>")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        config = ConfigLoader.load(config_file)

        logger.info(
            f"Initializing FleetOrchestrator for tenant={config['tenant']} env={config['env']}"
        )

        orchestrator = FleetOrchestrator(config)
        orchestrator.run()

        logger.info("Fleet orchestration completed successfully")

    except FleetUpgradeException as e:
        logger.error(f"Fleet upgrade failed: {e}")
        sys.exit(1)

    except Exception:
        logger.exception("Unexpected error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
