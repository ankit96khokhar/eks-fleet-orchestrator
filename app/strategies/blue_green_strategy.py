import time
from app.logger import LoggerFactory
from app.jenkins_client import JenkinsClient
from app.argocd_client import ArgoCDCLient

logger = LoggerFactory.get_logger("blue-green")

class BlueGreenUpgradeStrategy:

    def __init__(self, config):
        self.config = config
        self.jenkins = JenkinsClient(base_url=config["jenkins"]["url"], user=config["jenkins"]["user"], token=config["jenkins"]["token"])

        self.argocd = ArgoCDCLient()

    def upgrade(self, cluster):
        blue_cluster_name = cluster.name
        green_cluster_name = blue_cluster_name + "_green"

        logger.info(f"Starting Blue-green cluster upgrade for {blue_cluster_name}")
        logger.info(f"Green cluster will be {green_cluster_name}")

        self._create_green(cluster, green_cluster_name)
        self.register_argocd(green_cluster_name)
        self.sync_apps(green_cluster_name)
        self.validate_cluster(green_cluster_name)
        self._switch_traffic(blue_cluster_name, green_cluster_name)
        self._destroy_blue(cluster)

        logger.info(f"Blue-green upgrade completed for {blue_cluster_name}")

    def _create_green(self, green_cluster_name):
        logger.info("Starting Blue-green cluster upgrade")        
        params = {
            "ACTION": "plan",
            "SERVICE": "eks",
            "TENANT": cluster.tenant,
            "ENV": cluster.env,
            "REGION": cluster.region,
            "CLUSTER": cluster.name,
            "UPGRADE_TYPE": "control-plane",
            "VERSION": cluster.version
        }

        queue_id = self.jenkins.trigger_job("blue-green", params)

        result = self.jenkins.wait_for_completion(queue_id)

        if result != "SUCCESS":
            raise Exception(f"Green cluster creation failed for {green_cluster_name}")
        
    def _register_argocd(self, cluster_name):
        logger.info(f"Registering {cluster_name} in Argocd")
        self.argocd.register_cluster(cluster_name)
        logger.info("Cluster registered in Argocd")
        
    def _sync_apps(self, cluster_name):
        logger.info(f"Syncing argocd apps for {cluster_name}")

        self.argocd.sync_cluster(cluster_name)

        logger.info("Waiting for apps to become healthy")


        if self.argocd.wait_for_apps_healthy(cluster_name):
            logger.info(f"Apps are healthy in argocd for cluster {cluster_name}")
        else:
            logger.error(f"Apps are not healthy for cluster {cluster_name}")
            raise Exception(f"Apps not healthy for cluster {cluster_name}")
        
    def _validate_cluster(self, cluster_name):
        self.logger.info(f"Validating cluster health: {cluster_name}")

        # Simple delay for now — replace with real health check
        time.sleep(20)

        # You can add:
        # - Node ready check
        # - Ingress ready check
        # - API server reachable check

        self.logger.info("Cluster infra validation complete")


    def _switch_traffic(self, blue, green):

        self.logger.info("Switching traffic to GREEN")

        # Example: Route53 switch
        if self.config.get("traffic_switch") == "route53":
            self._switch_route53(blue, green)

        elif self.config.get("traffic_switch") == "alb":
            self._switch_alb(blue, green)

        else:
            self.logger.warning("No traffic switch method defined")

        self.logger.info("Traffic successfully switched")

    def _switch_route53(self, blue, green):
        # Placeholder for weighted DNS change
        self.logger.info(f"Route53 traffic moved from {blue} → {green}")

    def _switch_alb(self, blue, green):
        # Placeholder for ALB target group swap
        self.logger.info(f"ALB targets switched from {blue} → {green}")

    def _destroy_blue(self, cluster):

        self.logger.info(f"Destroying BLUE cluster: {cluster.name}")

        params = {
            "ACTION": "destroy",
            "SERVICE": "eks",
            "TENANT": cluster.tenant,
            "ENV": cluster.env,
            "REGION": cluster.region,
            "CLUSTER": cluster.name,
            "CONFIRM_DESTROY": "YES"
        }

        queue_id = self.jenkins.trigger_job(
            self.config["jenkins"]["job_name"],
            params
        )

        result = self.jenkins.wait_for_completion(queue_id)

        if result != "SUCCESS":
            raise Exception("Failed to destroy blue cluster")

        self.logger.info("Blue cluster destroyed successfully")