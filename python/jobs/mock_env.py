# Create a Deployment for the Mock Environment, and monitoring progress of the Mock Application

import asyncio
import os
import sys
import traceback
from .functions.deployment import main as create_deployment
from .functions.helpers import get_timestamp


async def main(**kwargs):
    """Creates the mock environment deployment, watched for mock application completion, return status"""
    job_name = os.getenv("MOCK_ENV_NAME", "mock-env")
    try:
        rendered_name = job_name + "-" + os.getenv("NAME_APPEND").split("/", 1)[1]
        rendered_namespace = os.getenv("MOCK_ENV_NAMESPACE", "default")
        if os.getenv("COMPLETION_JOB_NAME") == job_name:
            os.environ["COMPLETION_JOB_NAME"] = rendered_name
            os.environ["COMPLETION_JOB_NAMESPACE"] = rendered_namespace
        
        name, status = await create_deployment(
            monitor=kwargs.get("monitor", False),
            job_name=os.getenv("MOCK_ENV_JOB_NAME", "mock-env"),
            
            name=rendered_name,
            namespace=rendered_namespace,
            
            replicas=os.getenv("MOCK_ENV_REPLICAS", 1),
            progress_deadline_seconds=os.getenv("MOCK_ENV_DEPLOY_TIMEOUT", 500),
            
            image=os.getenv("MOCK_ENV_IMAGE", "busybox"),
            container_name=os.getenv("MOCK_ENV_CONTAINER_NAME", "sleep-container"),
            command=os.getenv("MOCK_ENV_COMMAND", '["sleep", "150"]'),
            cpu_limit=os.getenv("MOCK_ENV_CPU_LIMIT", "100m"),
            memory_limit=os.getenv("MOCK_ENV_MEMORY_LIMIT", "100Mi"),
            node_selector_key=os.getenv("NODE_SELECTOR_KEY", "kubernetes.io/os"),
            node_selector_value=os.getenv("NODE_SELECTOR_VALUE", "linux"),
            
            set_ready=os.getenv("MOCK_ENV_READY_VAR", "MOCK_ENV_READY"),
            wait_for_ready=os.getenv("MOCK_ENV_WAIT_FOR_BOOL", "False").lower()
            == "true",
            wait_for_ready_var=os.getenv("MOCK_ENV_WAIT_FOR_VAR", None),
            wait_description=os.getenv("MOCK_ENV_WAIT_FOR_DESC", None),

            log_name=os.getenv("MOCK_ENV_LOG_NAME", "MockEnv"),
            log_description=os.getenv("MOCK_ENV_LOG_DESC", "Mock Environment"),
            cleanup_object=os.getenv("MOCK_ENV_CLEANUP_RESOURCE", "True").lower()
            == "true",
        )
        return name, status

    except Exception as e:
        print(f"[{get_timestamp()}] Unexpected Error: ", e)
        traceback.print_exc(file=sys.stdout)
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
