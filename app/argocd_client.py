import subprocess
import time
from app.logger import LoggerFactory

class ArgoCDCLient:
    def sync_cluster(self, cluster_name):
        logger.info(f"Syncing all apps for cluster {cluster_name}")

        # Pass as a list of arguments
        cmd = [
            "argocd", "app", "sync", 
            "--selector", f"cluster={cluster_name}",
            "--prune", # SRE Best Practice: Remove old resources
            "--timeout", "300"
        ]

        try:
            # capture_output=True lets you log the error message if it fails
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("ArgoCD Sync triggered successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"ArgoCD Sync failed! Error: {e.stderr}")
            # Since this is a Blue-Green strategy, we MUST stop if this fails
            raise Exception(f"Aborting upgrade: Sync failed for {cluster_name}")

    def register_cluster(self, cluster_name, labels):

        label_args = []
        for k, v in labels.items():
            label_args.append(f"--label {k}={v}")

        cmd = f"argocd cluster add {cluster_name} {' '.join(label_args)}"
        subprocess.run(cmd, shell=True, check=True)

    def wait_for_apps_healthy(self, cluster_name):

        logger.info(f"Waiting for apps healthy on {cluster_name}")

        # Placeholder
        # In production use argocd API to check health
        time.sleep(30)
        return True