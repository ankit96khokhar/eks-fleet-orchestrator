import requests
import time
from app.logger import LoggerFactory

logger = LoggerFactory.get_logger("jenkins")

class JenkinsClient:
    def __init__(self, base_url: str, user, token):
        self.base_url = base_url
        self.auth = (user, token)

    def trigger_job(self, job_name, params):
        url = f"{self.base_url}/job/{job_name}/buildWithParameters"
        logger.info(f"Triggering Jenkins job: {job_name}")

        response = requests.post(url, params=params, auth=self.auth)

        if response.status_code not in [200, 201]:
            raise Exception("Failed to trigger Jenkins job")
        
        return response.headers["Location"]

    def wait_for_completion(self, queue_url):

        # Fix internal Jenkins URL issue
        queue_url = queue_url.replace("http://jenkins:8080", self.base_url)

        logger.info("Waiting for Jenkins build to start")

        build_url = None

        while not build_url:
            queue_info = requests.get(
                f"{queue_url}api/json",
                auth=self.auth
            ).json()

            executable = queue_info.get("executable")

            if executable:
                build_url = executable["url"]
                build_url = build_url.replace("http://jenkins:8080", self.base_url)

            time.sleep(5)

        logger.info("Monitoring build")

        while True:
            build_info = requests.get(
                f"{build_url}api/json",
                auth=self.auth
            ).json()

            if build_info["result"]:
                return build_info["result"]

            time.sleep(10)
