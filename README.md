# k8s-action-runner
Python module leveraging the Asyncio Kubernetes Client API to automate Kubernetes tasks triggered by GitHub Actions. It's designed to run within a self-hosted GitHub runner managed by Actions Runner Controller (ARC) inside your Kubernetes cluster

**Note** this is not intended to be a complete guide on how to accomplish the above from scratch, rather this is a working example from my own use case that you can modify as needed. I provide the GitHub Actions workflow file, as well the Python [UV package manager](https://github.com/astral-sh/uv) configurations with the modules, with details on how to utilize them in the subfolder [python/README.md](README)

## Features

* **Asynchronous Operations:** Efficiently manage Kubernetes resources using [Kubernetes asyncio client.](https://github.com/tomplus/kubernetes_asyncio)
* **GitHub Actions Integration:** Trigger Kubernetes actions directly from your GitHub workflows, with support for reading environment variables from the GitHub job.
* **Customizable:** Modify the Python module to suit your needs.
* **ARC Compatibility:** Seamlessly integrates with [Actions Runner Controller](https://github.com/actions/actions-runner-controller) for self-hosted runners.
* **Example Use Cases:** Create Pods, Deployments, Service, etc required to run in your cluster as part of a GitHub Pipeline (Only Pods deployed as Deployments is provided as an example.)

## Getting Started

1. **Prerequisites:**
   * A Kubernetes cluster
   * [Actions Runner Controller (ARC)](https://github.com/actions/actions-runner-controller) deployed and configured
   * Knowledge of Python, Kubernetes, and GitHub Actions

2. **Installation:**
   - Download this repository as a ZIP, or see releases. See [./python/README.md](README) for how to use
   - The [./python](python) folder contains the Python module, ready for you to modify and use in your workflows
   - The [./.github/workflows/deploy.yaml](deploy) file contains a sample GitHub Actions workflow file to get you started on executing the Python module in your CI pipeline

## Notes

- The default behavior is two create two pods via deployments (Mock Environment and Mock Application) and then delete them. This is just an example, you can modify the Python module to suit your needs. Originally, they were monitoring a CR, but I have simplified it as a working example of how to deploy pods in a cluster. I would advise reviewing the [Kubernetes asyncio client](https://github.com/tomplus/kubernetes_asyncio) documentation for how to adjust this for you own use cases.

- The Kubernetes Client is configured to be ran from within a Pod, so you must configure your ARC runners with these [example configurations](https://github.com/kubernetes-client/python/blob/master/examples/in_cluster_config.py):

```yaml
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: pods-manager
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["list", "get", "create", "delete"]

---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: pods-manager
subjects:
- kind: ServiceAccount
  name: default
  namespace: default
roleRef:
  kind: ClusterRole
  name: pods-manager
  apiGroup: rbac.authorization.k8s.io
```
- Documentation: https://kubernetes.io/docs/reference/access-authn-authz/rbac/

If you run with the local option, then instead your local `~/.kube/config` file will be used to authenticate with your cluster. See the [./python/README.md](README) for more information on local development.

## Contributing

While this is only a working example designed to get you started in automation K8s actions in your CI workflows and clusters, contributions are welcome. You free to open issues or submit pull requests, and of course fork for you own personal or commercial use, but again this is for the most part a one-off project and not intended to be a full-fledged resource.

## License

This project is licensed under the MIT License.