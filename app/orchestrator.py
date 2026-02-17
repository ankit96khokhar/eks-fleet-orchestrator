from collections import defaultdict
from app.logger import LoggerFactory
from app.models import Cluster
from app.exceptions import ConfigurationError
from app.state_manager import StateManager
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.strategies.blue_green_strategy import BlueGreenUpgradeStrategy
from app.strategies.in_place_strategy import InPlaceStrategy
from app.exceptions import StateLockError


logger = LoggerFactory.get_logger("orchestrator")


class FleetOrchestrator:

    def __init__(self, config: dict):

        self.config = config
        self.tenant = config["tenant"]
        self.env = config["env"]
        self.region = config["region"]

        # Environment-based rollout config
        if self.env == "prod":
            self.wave_percent = 10
            self.bake_seconds = 30
            self.lock_timeout_seconds = 300 # 30 minutes
            self.max_parallel = 2
        elif self.env == "test":
            self.wave_percent = 25
            self.bake_seconds = 10
            self.lock_timeout_seconds = 300   # 15 minutes
            self.max_parallel = 3
        else:  # dev
            self.wave_percent = 50
            self.bake_seconds = 5
            self.lock_timeout_seconds = 300   # 5 minutes
            self.max_parallel = 5


        # 🔥 PASS timeout to StateManager
        self.state = StateManager(
            region=self.region,
            lock_timeout_seconds=self.lock_timeout_seconds
        )

        self.clusters = self._build_clusters()

    def _build_clusters(self):

        logger.info("Building cluster objects from config")

        eks_service = self.config["services"].get("eks", {})

        if not eks_service.get("enabled", False):
            raise ConfigurationError("EKS service is not enabled")

        eks_config = eks_service.get("config", {})


        clusters = []

        for name, cfg in eks_config.items():

            fleet = cfg.get("fleet")
            version = cfg.get("version")
            is_canary = cfg.get("is_canary", False)

            if not fleet:
                raise ConfigurationError(f"Cluster {name} missing fleet")

            if not version:
                raise ConfigurationError(f"Cluster {name} missing version")

            cluster = Cluster(
                name=name,
                fleet=fleet,
                version=version,
                is_canary=is_canary,
                tenant=self.tenant,
                env=self.env,
                region=self.region
            )

            clusters.append(cluster)

        logger.info(f"Total clusters loaded: {len(clusters)}")
        return clusters

    def _group_by_fleet(self):

        logger.info("Grouping clusters by fleet")

        fleets = defaultdict(list)

        for cluster in self.clusters:
            fleets[cluster.fleet].append(cluster)

        for fleet_name, fleet_clusters in fleets.items():
            logger.info(f"Fleet '{fleet_name}' has {len(fleet_clusters)} clusters")

        return fleets

    def run(self):

        logger.info(f"Starting fleet upgrade orchestration for env={self.env}")

        fleets = self._group_by_fleet()

        for fleet_name, fleet_clusters in fleets.items():
            logger.info(f"Processing fleet: {fleet_name}")
            self._run_fleet(fleet_name, fleet_clusters)

    def _run_fleet(self, fleet_name: str, clusters: list):

        canaries = [c for c in clusters if c.is_canary]
        regular = [c for c in clusters if not c.is_canary]

        if len(canaries) != 1:
            raise Exception(f"Fleet '{fleet_name}' must have exactly 1 canary cluster")

        canary = canaries[0]

        # -------------------------
        # 1️⃣ Canary
        # -------------------------
        logger.info(f"Starting Canary Upgrade: {canary.name}")

        self._upgrade_cluster(canary)

        self._bake("canary")

        # -------------------------
        # 2️⃣ Waves
        # -------------------------
        waves = self._chunk_clusters(regular)

        for wave_number, wave in enumerate(waves, start=1):

            logger.info(f"Starting Wave {wave_number}")
            logger.info(f"Running up to {self.max_parallel} clusters in parallel")

            with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:

                future_to_cluster = {
                    executor.submit(self._upgrade_cluster, cluster): cluster
                    for cluster in wave
                }

                for future in as_completed(future_to_cluster):
                    cluster = future_to_cluster[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(
                            f"Wave {wave_number} failed on cluster {cluster.name}"
                        )
                        logger.error("Stopping further rollout")
                        raise

            self._bake(f"wave {wave_number}")


        logger.info(f"Fleet '{fleet_name}' completed successfully")


    def _upgrade_cluster(self, cluster):
        # time.sleep(3)

        if self.state.already_upgraded(cluster):
            logger.info(f"Skipping {cluster.name} (already upgraded)")
            return

        try:
            self.state.lock(cluster)

            logger.info(f"Upgrading cluster {cluster.name}")
            if cluster.env in ["dev"]:
                strategy = InPlaceStrategy(self.config)
            else:
                strategy = BlueGreenUpgradeStrategy(self.config)

            strategy.upgrade(cluster)

            self.state.mark_success(cluster)

        except StateLockError as e:
            logger.warning(f"Lock not acquired for {cluster.name}: {e}")
            raise

        except Exception as e:
            logger.error(f"Upgrade failed for {cluster.name}")
            self.state.mark_failure(cluster, str(e))
            raise

    def _chunk_clusters(self, clusters: list):

        if not clusters:
            return []

        total = len(clusters)
        wave_size = max(1, int(total * self.wave_percent / 100))

        waves = [
            clusters[i:i + wave_size]
            for i in range(0, total, wave_size)
        ]

        logger.info(f"Total clusters: {total}")
        logger.info(f"Wave size: {wave_size}")
        logger.info(f"Total waves: {len(waves)}")

        return waves

    def _bake(self, stage: str):
        logger.info(f"Baking after {stage} for {self.bake_seconds} seconds...")
        # time.sleep(self.bake_seconds)
        logger.info("Bake complete")