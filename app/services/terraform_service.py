import subprocess
from app.logger import LoggerFactory

logger = LoggerFactory.get_logger("terraform-service")


class TerraformService:

    def __init__(self, working_dir):
        self.working_dir = working_dir

    def _run(self, command):
        logger.info(f"Running: {' '.join(command)}")

        result = subprocess.run(
            command,
            cwd=self.working_dir,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(result.stderr)
            raise Exception(f"Terraform command failed: {command}")

        logger.info(result.stdout)

    def init(self):
        self._run(["terraform", "init", "-input=false"])

    def plan(self):
        self._run(["terraform", "plan", "-out=tfplan"])

    def apply(self):
        self._run(["terraform", "apply", "-auto-approve", "tfplan"])

    def destroy(self, target=None):
        cmd = ["terraform", "destroy", "-auto-approve"]
        if target:
            cmd.extend(["-target", target])
        self._run(cmd)
