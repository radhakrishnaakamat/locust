import os
import requests
from flask import jsonify, request
from kubernetes import client, config
import datetime


def update_kubernetes_config_and_restart(config_data, other_files):

    config.load_incluster_config()

    kubernetes_deployment_namespace = os.environ.get("KUBERNETES_DEPLOYMENT_NAMESPACE")
    kubernetes_worker_deployment_name = os.environ.get("KUBERNETES_WORKER_DEPLOYMENT_NAME")
    kubernetes_config_name = os.environ.get("KUBERNETES_CONFIG_NAME")

    config_api = client.CoreV1Api()
    existing_config = config_api.read_namespaced_config_map(kubernetes_config_name, kubernetes_deployment_namespace)
    existing_config.data = {"main.py": config_data}

    for x in range(len(other_files)):
        existing_config.data[other_files[x]["file_name"]] = other_files[x]["content"]
    config_api.patch_namespaced_config_map(kubernetes_config_name, kubernetes_deployment_namespace, existing_config)
    _restart_kubernates_deployment(kubernetes_deployment_namespace, kubernetes_worker_deployment_name)

    return jsonify({"success": True, "message": "Updated & restart in progress"})


def _restart_kubernates_deployment(kubernetes_deployment_namespace, kubernetes_worker_deployment_name):
    api = client.AppsV1Api()

    now = datetime.datetime.utcnow()
    now = str(now.isoformat("T") + "Z")
    if (
        kubernetes_worker_deployment_name is not None
        and kubernetes_worker_deployment_name != ""
        and kubernetes_worker_deployment_name.strip() != "-"
    ):
        deployment = api.read_namespaced_deployment(kubernetes_worker_deployment_name, kubernetes_deployment_namespace)
        deployment.spec.template.metadata.annotations = {"kubectl.kubernetes.io/restartedAt": now}
        api.patch_namespaced_deployment(
            name=kubernetes_worker_deployment_name, namespace=kubernetes_deployment_namespace, body=deployment
        )
