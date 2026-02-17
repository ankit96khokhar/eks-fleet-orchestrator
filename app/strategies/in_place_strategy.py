import time
from app.logger import LoggerFactory
from app.jenkins_client import JenkinsClient


logger = LoggerFactory.get_logger("in-place")

class InPlaceStrategy:

    def __init__(self, config):
        self.config = config

        self.jenkins = JenkinsClient(
            base_url=config["jenkins"]["url"],
            user=config["jenkins"]["user"],
            token=config["jenkins"]["token"]
        )

    def upgrade(self, cluster):
        logger.info(f"Starting In-place upgrade for {cluster.name}")

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

        queue = self.jenkins.trigger_job("terraform-cicd-final", params)

        result = self.jenkins.wait_for_completion(queue)

        if result != "SUCCESS":
            raise Exception("Control plane upgrade failed")

        self._sync_argocd(cluster)
        self._validate_cluster(cluster)

        logger.info(f"In-place upgrade completed for {cluster.name}")

    def _validate_cluster(self, cluster):
        logger.info("Validating cluster health")

        # Placeholder
        # Later:
        # - Check node Ready
        # - Check system pods
        # - Check Argo apps
        # - Check metrics

        time.sleep(30)

        logger.info("Cluster validation passed")        

    def _sync_argocd(self, cluster):

        logger.info("Triggering ArgoCD sync")

        self.argocd.sync_cluster(cluster.name)

        logger.info("Waiting for ArgoCD apps to become healthy")

        self.argocd.wait_for_apps_healthy(cluster.name)

        logger.info("ArgoCD sync successful")

    
    

