import json
import logging
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    yaml = None


def _repo_slug(repo_url):
    parsed = urlparse(repo_url)
    repo_name = parsed.path.rstrip("/").split("/")[-1] or "workspace"
    return "".join(char.lower() if char.isalnum() else "-" for char in repo_name).strip("-") or "workspace"


def _service_name(devcontainer_config, repo_url):
    raw_name = devcontainer_config.get("name") or _repo_slug(repo_url)
    name = "".join(char.lower() if char.isalnum() else "-" for char in raw_name).strip("-")
    return name or "devcontainer"


def _load_devcontainer_config(devcontainer_json):
    try:
        return json.loads(devcontainer_json)
    except (TypeError, json.JSONDecodeError) as e:
        logging.warning(f"Unable to parse devcontainer.json for compose generation: {e}")
        return {}


def _normalize_compose_env(container_env):
    if not isinstance(container_env, dict):
        return None

    environment = {}
    for key, value in container_env.items():
        if isinstance(value, str) and value.startswith("${localEnv:") and value.endswith("}"):
            environment[key] = "${" + value[len("${localEnv:"):-1] + "}"
        else:
            environment[key] = value
    return environment or None


def _normalize_compose_ports(forward_ports):
    if not isinstance(forward_ports, list):
        return None

    ports = []
    for port in forward_ports:
        if isinstance(port, int):
            ports.append(f"{port}:{port}")
        elif isinstance(port, str) and port.strip():
            cleaned_port = port.strip()
            ports.append(cleaned_port if ":" in cleaned_port else f"{cleaned_port}:{cleaned_port}")
    return ports or None


def _dump_yaml(data, indent=0):
    lines = []
    prefix = " " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.extend(_dump_yaml(value, indent + 2))
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                lines.append(f"{prefix}  - {json.dumps(item)}")
        else:
            lines.append(f"{prefix}{key}: {json.dumps(value)}")
    return lines


def generate_docker_compose_yml(devcontainer_json, repo_url):
    devcontainer_config = _load_devcontainer_config(devcontainer_json)
    workspace_name = _repo_slug(repo_url)
    service = {
        "image": devcontainer_config.get("image", "mcr.microsoft.com/devcontainers/base:ubuntu"),
        "volumes": [f".:/workspaces/{workspace_name}:cached"],
        "working_dir": f"/workspaces/{workspace_name}",
        "command": "sleep infinity",
    }

    if isinstance(devcontainer_config.get("build"), dict):
        service.pop("image", None)
        service["build"] = {
            "context": devcontainer_config["build"].get("context", "."),
        }
        dockerfile = devcontainer_config["build"].get("dockerfile") or devcontainer_config["build"].get("dockerFile")
        if dockerfile:
            service["build"]["dockerfile"] = dockerfile
    elif devcontainer_config.get("dockerFile") or devcontainer_config.get("dockerfile"):
        service.pop("image", None)
        service["build"] = {
            "context": devcontainer_config.get("context", "."),
            "dockerfile": devcontainer_config.get("dockerFile") or devcontainer_config.get("dockerfile"),
        }

    ports = _normalize_compose_ports(devcontainer_config.get("forwardPorts"))
    if ports:
        service["ports"] = ports

    environment = _normalize_compose_env(devcontainer_config.get("containerEnv"))
    if environment:
        service["environment"] = environment

    compose = {
        "services": {
            _service_name(devcontainer_config, repo_url): service
        }
    }
    if yaml:
        return yaml.safe_dump(compose, sort_keys=False)
    return "\n".join(_dump_yaml(compose)) + "\n"
