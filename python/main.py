# This example setup creates two example pods, one for a mock environment and one for a mock application
#  monitors for completion and then cleans up the pods moving on to the next step of the GitHub Action job
# This simulates running a performance test, as example, on your cluster via Deployments
import argparse
import asyncio
import os
import sys
import traceback
import uuid
from .jobs.functions.helpers import get_timestamp, set_summary
from .jobs import mock_env, mock_app
from kubernetes_asyncio import config


async def main():
    try:
        # Parse local argument, and set Kubernetes Authentication
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-l",
            "--local",
        )
        if parser.parse_args().local:
            await config.load_kube_config()
            random_uuid = uuid.uuid4()
            short_uuid = str(random_uuid).split("-")[0]
            os.environ["NAME_APPEND"] = f"dev-local/dev-local-{short_uuid}"
            os.environ["COMPLETION_JOB_NAME"] = "mock-app"
            os.environ["MOCK_ENV_IMAGE"] = "busybox"
            os.environ["MOCK_ENV_CONTAINER_NAME"] = "sleep-container"
            os.environ["MOCK_ENV_COMMAND"] = '["sleep", "150"]'
            os.environ["MOCK_ENV_CPU_LIMIT"] = "100m"
            os.environ["MOCK_ENV_MEMORY_LIMIT"] = "100Mi"
            os.environ["MOCK_APP_IMAGE"] = "busybox"
            os.environ["MOCK_APP_CONTAINER_NAME"] = "sleep-container"
            os.environ["MOCK_APP_COMMAND"] = '["sleep", "60"]'
            os.environ["MOCK_APP_CPU_LIMIT"] = "100m"
            os.environ["MOCK_APP_MEMORY_LIMIT"] = "100Mi"
            os.environ["NODE_SELECTOR_KEY"] = "workerNode"
            os.environ["NODE_SELECTOR_VALUE"] = "true"
            os.environ["PYTHONASYNCIODEBUG"] = "1"

        else:
            config.load_incluster_config()

        # Initiate and run jobs asynchronously
        job_results = await asyncio.gather(
            mock_env.main(),
            mock_app.main(),
        )
        print(f"[{get_timestamp()}] Overall Job Results: {job_results}")

        # Check for failed jobs
        failed_jobs = []
        for job_result in job_results:
            job_name = job_result[0]
            job_status = job_result[1]
            if job_status == "Failed":
                failed_jobs.append(job_name)

        # Exit with the appropriate status post-jobs
        if failed_jobs:
            print(f"[{get_timestamp()}] The following jobs have failed: {failed_jobs}")
            set_summary(f"The follow jobs have failed: {failed_jobs}")
            exit(1)
        else:
            print(f"[{get_timestamp()}] All jobs have completed successfully")

    except Exception as e:
        print(f"[{get_timestamp()}] Unexpected Error: ", e)
        traceback.print_exc(file=sys.stdout)
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
