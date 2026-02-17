import time
import boto3
from botocore.exceptions import ClientError
from app.logger import LoggerFactory
from app.exceptions import StateLockError

logger = LoggerFactory.get_logger("state-manager")


class StateManager:

    def __init__(self, table_name="eks_fleet_upgrade", region=None, lock_timeout_seconds=600):
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)
        self.lock_timeout_seconds = lock_timeout_seconds


    def _key(self, cluster):
        return {
            "tenant_env": f"{cluster.tenant}#{cluster.env}",
            "cluster_name": cluster.name
        }

    def already_upgraded(self, cluster):

        response = self.table.get_item(Key=self._key(cluster))
        item = response.get("Item")

        if not item:
            return False

        return (
            item.get("status") == "SUCCESS" and
            item.get("target_version") == cluster.version
        )

    def lock(self, cluster):

        key = self._key(cluster)
        now = int(time.time())

        logger.info(f"Attempting to lock cluster {cluster.identifier()}")

        # Step 1: Check existing item
        response = self.table.get_item(Key=key)
        item = response.get("Item")

        if item:
            status = item.get("status")
            started_at = item.get("started_at", 0)

            if status == "IN_PROGRESS":
                age = now - started_at

                if age < self.lock_timeout_seconds:
                    logger.warning(
                        f"Cluster locked and not expired (age={age}s)"
                    )
                    raise StateLockError("Cluster already locked")

                else:
                    logger.warning(
                        f"Stale lock detected (age={age}s). Overriding lock."
                    )

        # Step 2: Acquire lock
        self.table.put_item(
            Item={
                **key,
                "status": "IN_PROGRESS",
                "target_version": cluster.version,
                "started_at": now
            }
        )

        logger.info("Lock acquired")

    def mark_success(self, cluster):

        logger.info(f"Marking {cluster.identifier()} as SUCCESS")

        self.table.update_item(
            Key=self._key(cluster),
            UpdateExpression="SET #s = :success, completed_at = :ts",
            ExpressionAttributeNames={
                "#s": "status"
            },
            ExpressionAttributeValues={
                ":success": "SUCCESS",
                ":ts": int(time.time())
            }
        )

    def mark_failure(self, cluster, error_message):

        key = self._key(cluster)

        logger.error(f"Marking {cluster.identifier()} as FAILED")

        self.table.update_item(
            Key=key,
            UpdateExpression="SET #s = :status, #err = :error_msg",
            ExpressionAttributeNames={
                "#s": "status",
                "#err": "error"
            },
            ExpressionAttributeValues={
                ":status": "FAILED",
                ":error_msg": error_message
            }
        )

    def update_status(self, cluster, status, extra=None):

        key = self._key(cluster)

        update_expression = "SET #s = :status"
        expression_values = {
            ":status": status
        }

        if extra:
            for k, v in extra.items():
                update_expression += f", {k} = :{k}"
                expression_values[f":{k}"] = v

        self.table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues=expression_values
        )
