# Supporting deployments

import asyncio
import json
import os
import sys
import traceback
from kubernetes_asyncio import client, watch
from .helpers import get_timestamp


async def main(**kwargs):
    try:
        if kwargs.get("monitor", False):
            status = await deployment(**kwargs)
            return status
        else:
            name, status = await deployment(**kwargs)
            return name, status

    except Exception as e:
        print(f"[{get_timestamp()}] Unexpected Error: ", e)
        traceback.print_exc(file=sys.stdout)
        exit(1)


async def deployment(**kwargs):
    try:
        # Setting variables
        monitor = kwargs["monitor"]
        completion_job_name = os.getenv("COMPLETION_JOB_NAME")
        completion_job_namespace = os.getenv("COMPLETION_JOB_NAMESPACE")

        name = kwargs["name"]
        namespace = kwargs["namespace"]

        replicas = kwargs.get("replicas", 1)
        progress_deadline_seconds = kwargs.get("progress_deadline_seconds")

        image = kwargs["image"]
        container_name = kwargs["container_name"]
        command = json.loads(kwargs["command"])
        cpu_limit = kwargs.get("cpu_limit")
        memory_limit = kwargs.get("memory_limit")
        node_selector_key = kwargs.get("node_selector_key")
        node_selector_value = kwargs.get("node_selector_value")

        set_ready = kwargs["set_ready"]
        wait_for_ready = kwargs["wait_for_ready"]
        wait_for_ready_var = kwargs["wait_for_ready_var"]
        wait_description = kwargs["wait_description"]
        main_job_description = kwargs.get("main_job_description", "GitHub Action Job")

        log_name = kwargs["log_name"]
        log_description = kwargs["log_description"]
        cleanup_object = kwargs["cleanup_object"]

        # Initialize Kubernetes client
        api_client = client.ApiClient()
        apps_api = client.AppsV1Api(api_client=api_client)
        rest_client = api_client.rest_client

        # Create if not monitoring
        if not monitor:
            try:

                creation_proceed = True
                if wait_for_ready:
                    creation_proceed = False
                    print(
                        f"[{get_timestamp()}][{log_name}] Waiting for {wait_description} to be ready.."
                    )
                    # Check if the designated env var is marked as ready before proceeding, timeout after 10 minutes max
                    for _ in range(0, 120):
                        if os.getenv(f"{wait_for_ready_var}", "False").lower() == "true":
                            creation_proceed = True
                            break
                        # Sleep for 5 seconds before the next env check
                        await asyncio.sleep(5)

                if creation_proceed:
                    print(
                        f"[{get_timestamp()}][{log_name}] Setting up {log_description}"
                    )
                    body = client.V1Deployment(
                        api_version="apps/v1",
                        kind="Deployment",
                        metadata=client.V1ObjectMeta(name=name),
                        spec=client.V1DeploymentSpec(
                            replicas=replicas,
                            progress_deadline_seconds=progress_deadline_seconds,
                            selector=client.V1LabelSelector(match_labels={"app": name}),
                            template=client.V1PodTemplateSpec(
                                metadata=client.V1ObjectMeta(labels={"app": name}),
                                spec=client.V1PodSpec(
                                    containers=[
                                        client.V1Container(
                                            name=container_name,
                                            image=image,
                                            command=command,
                                            resources=client.V1ResourceRequirements(
                                                        requests={
                                                            "cpu": cpu_limit,
                                                            "memory": memory_limit,
                                                        },
                                                        limits={
                                                            "cpu": cpu_limit,
                                                            "memory": memory_limit,
                                                        }
                                                        ),
                                        ),
                                    ],
                                    node_selector={node_selector_key: node_selector_value},
                                    tolerations=[
                                        client.V1Toleration(
                                            key=node_selector_key,
                                            operator="Equal",
                                            value=node_selector_value,
                                            effect="NoSchedule",
                                        )
                                    ],
                                ),
                            ),
                        ),
                    )

                    await apps_api.create_namespaced_deployment(
                        namespace=namespace, body=body
                    )
                else:
                    raise Exception(
                        f'{wait_description} is not ready, timed out after 10 minutes waiting for "{wait_for_ready_var}"'
                    )

            except Exception as e:
                print(
                    f"[{get_timestamp()}][{log_name}] Error creating {log_description}: ",
                    e,
                )
                exit(1)

        # Watch for the job to complete
        w = watch.Watch()
        async for event in w.stream(
            apps_api.list_namespaced_deployment,
            namespace=namespace,
            field_selector=f"metadata.name={name}",
            pretty="true",
            timeout_seconds=600,
        ):

            deployment = event["object"]
            status = {
                "name": deployment.metadata.name if deployment.metadata.name else None,
                "available_replicas": deployment.status.available_replicas if deployment.status.available_replicas else None,
                "message": deployment.status.conditions[0].message if deployment.status.conditions and deployment.status.conditions[0] else None,
                "reason": deployment.status.conditions[0].reason if deployment.status.conditions and deployment.status.conditions[0] else None,
                "status": deployment.status.conditions[0].status if deployment.status.conditions and deployment.status.conditions[0] else None,
                "type": deployment.status.conditions[0].type if deployment.status.conditions and deployment.status.conditions[0] else None,
            }
            if status is not None:
                if monitor:
                    # Check if the pod is running, and report status to monitoring environment
                    if (
                        status["status"] == "False"
                        and status["reason"]
                        == "ProgressDeadlineExceeded"
                    ):
                        await w.close()
                        return log_name, "Failed"
                    if (
                        status["available_replicas"] == replicas
                        and status["status"] == "True"
                    ):
                        await w.close()
                        return log_name, "Ready"

                else:
                    print(f"[{get_timestamp()}][{log_name}][Watch] {status}")

                    # Check if the pod has failed
                    if (
                        status["status"] == "False"
                        and status["reason"]
                        == "ProgressDeadlineExceeded"
                    ):
                        await w.close()
                        job_status = "Failed"
                        break

                    # Continue when pods are running
                    if (
                        status["available_replicas"] == replicas
                        and status["status"] == "True"
                    ):
                        # Monitor the Completion job
                        print(
                            f"[{get_timestamp()}][{log_name}][Watch] {log_description} is running, monitoring {main_job_description}.."
                        )
                        os.environ[set_ready] = "True"
                        
                        wC = watch.Watch()
                        async for event in w.stream(
                                apps_api.list_namespaced_deployment,
                                namespace=completion_job_namespace,
                                field_selector=f"metadata.name={completion_job_name}",
                                pretty="true",
                                timeout_seconds=600,
                        ):
                                
                            deploymentC = event["object"]
                            statusC = {
                                "name": deploymentC.metadata.name if deploymentC.metadata.name else None,
                                "available_replicas": deploymentC.status.available_replicas if deploymentC.status.available_replicas else None,
                                "message": deploymentC.status.conditions[0].message if deploymentC.status.conditions and deploymentC.status.conditions[0] else None,
                                "reason": deploymentC.status.conditions[0].reason if deploymentC.status.conditions and deploymentC.status.conditions[0] else None,
                                "status": deploymentC.status.conditions[0].status if deploymentC.status.conditions and deploymentC.status.conditions[0] else None,
                                "type": deploymentC.status.conditions[0].type if deploymentC.status.conditions and deploymentC.status.conditions[0] else None,
                            }
                            
                            if statusC is not None:
                                if name == completion_job_name:
                                    print(f"[{get_timestamp()}][{log_name}][Watch] Monitoring main job status..\n {status}")
                                
                                if (
                                    statusC["available_replicas"] == replicas
                                    and statusC["status"] == "True"
                                ):
                                    # Sleep for 15 seconds to simulate application run
                                    await asyncio.sleep(15)
                                    await wC.close()
                                    break
                                
                                else:
                                    # Sleep for 10 seconds before the next watch request
                                    await asyncio.sleep(10)
                                
                        await w.close()
                        job_status = "Completed"
                        break

            # Sleep for 10 seconds before the next watch request
            await asyncio.sleep(10)

        return log_name, job_status

    except Exception as e:
        print(f"[{get_timestamp()}] Unexpected Error: ", e)
        traceback.print_exc(file=sys.stdout)
        exit(1)

    finally:
        # Clean up the job resources
        if cleanup_object and not monitor:
            try:
                await apps_api.delete_namespaced_deployment(
                    namespace=namespace, name=name
                )
                print(
                    f"[{get_timestamp()}][{log_name}] {log_description} has been cleaned up."
                )

            except Exception as e:
                print(
                    f"[{get_timestamp()}][{log_name}] Error deleting {log_description}: ",
                    e,
                )

        # Clean up unclosed sessions
        if rest_client is not None:
            await rest_client.pool_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
