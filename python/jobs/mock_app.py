# Create a Deployment for the Mock Application

import asyncio
import os
import sys
import traceback
from .functions.deployment import main as create_deployment
from .functions.helpers import get_timestamp


async def main(**kwargs):
    """Creates the mock application deployment, wait for mock environment to be ready, simulate an app run, return status"""
    job_name = os.getenv("MOCK_APP_NAME", "mock-app")
    try:
        rendered_name = job_name + "-" + os.getenv("NAME_APPEND").split("/", 1)[1]
        rendered_namespace = os.getenv("MOCK_APP_NAMESPACE", "default")
        if os.getenv("COMPLETION_JOB_NAME") == job_name:
            os.environ["COMPLETION_JOB_NAME"] = rendered_name
            os.environ["COMPLETION_JOB_NAMESPACE"] = rendered_namespace
        
        name, status = await create_deployment(
            monitor=kwargs.get("monitor", False),
            
            name=rendered_name,
            namespace=rendered_namespace,
            
            replicas=os.getenv("MOCK_APP_REPLICAS", 1),
            progress_deadline_seconds=os.getenv("MOCK_APP_DEPLOY_TIMEOUT", 500),
            
            image=os.getenv("MOCK_APP_IMAGE", "busybox"),
            container_name=os.getenv("MOCK_APP_CONTAINER_NAME", "sleep-container"),
            command=os.getenv("MOCK_APP_COMMAND", '["sleep", "60"]'),
            cpu_limit=os.getenv("MOCK_APP_CPU_LIMIT", "100m"),
            memory_limit=os.getenv("MOCK_APP_MEMORY_LIMIT", "100Mi"),
            node_selector_key=os.getenv("NODE_SELECTOR_KEY", "kubernetes.io/os"),
            node_selector_value=os.getenv("NODE_SELECTOR_VALUE", "linux"),

            set_ready=os.getenv("MOCK_APP_READY_VAR", "MOCK_APP_READY"),
            wait_for_ready=os.getenv("MOCK_APP_WAIT_FOR_BOOL", "True").lower()
            == "true",
            wait_for_ready_var=os.getenv("MOCK_APP_WAIT_FOR_VAR", "MOCK_ENV_READY"),
            wait_description=os.getenv("MOCK_APP_WAIT_FOR_DESC", "Mock Environment"),
            
            log_name=os.getenv("MOCK_APP_LOG_NAME", "MockApp"),
            log_description=os.getenv("MOCK_APP_LOG_DESC", "Mock Application"),
            cleanup_object=os.getenv("MOCK_APP_CLEANUP_RESOURCE", "True").lower()
            == "true",
        )
        return name, status

    except Exception as e:
        print(f"[{get_timestamp()}] Unexpected Error: ", e)
        traceback.print_exc(file=sys.stdout)
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
