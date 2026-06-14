import unittest

import helpers.docker_compose_helpers as docker_compose_helpers


class DockerComposeGenerationTest(unittest.TestCase):
    def setUp(self):
        self.original_yaml = docker_compose_helpers.yaml
        docker_compose_helpers.yaml = None

    def tearDown(self):
        docker_compose_helpers.yaml = self.original_yaml

    def test_generates_compose_from_image_devcontainer(self):
        compose_yml = docker_compose_helpers.generate_docker_compose_yml(
            """
            {
              "name": "Python API",
              "image": "mcr.microsoft.com/devcontainers/python:3.12-bookworm",
              "forwardPorts": [8000, "5173"],
              "containerEnv": {
                "API_KEY": "${localEnv:API_KEY}",
                "ENVIRONMENT": "development"
              }
            }
            """,
            "https://github.com/example/python-api",
        )

        self.assertIn("python-api:", compose_yml)
        self.assertIn('image: "mcr.microsoft.com/devcontainers/python:3.12-bookworm"', compose_yml)
        self.assertIn(".:/workspaces/python-api:cached", compose_yml)
        self.assertIn('working_dir: "/workspaces/python-api"', compose_yml)
        self.assertIn("8000:8000", compose_yml)
        self.assertIn("5173:5173", compose_yml)
        self.assertIn('API_KEY: "${API_KEY}"', compose_yml)
        self.assertIn('ENVIRONMENT: "development"', compose_yml)

    def test_generates_compose_build_from_dockerfile_devcontainer(self):
        compose_yml = docker_compose_helpers.generate_docker_compose_yml(
            """
            {
              "name": "Dockerfile App",
              "build": {
                "context": ".devcontainer",
                "dockerfile": "Dockerfile"
              }
            }
            """,
            "https://github.com/example/dockerfile-app",
        )

        self.assertIn("dockerfile-app:", compose_yml)
        self.assertNotIn("image:", compose_yml)
        self.assertIn("build:", compose_yml)
        self.assertIn('context: ".devcontainer"', compose_yml)
        self.assertIn('dockerfile: "Dockerfile"', compose_yml)

    def test_invalid_devcontainer_json_still_produces_usable_compose(self):
        with self.assertLogs(level="WARNING"):
            compose_yml = docker_compose_helpers.generate_docker_compose_yml(
                "{ not json }",
                "https://github.com/example/fallback-app",
            )

        self.assertIn("fallback-app:", compose_yml)
        self.assertIn('image: "mcr.microsoft.com/devcontainers/base:ubuntu"', compose_yml)
        self.assertIn(".:/workspaces/fallback-app:cached", compose_yml)


if __name__ == "__main__":
    unittest.main()
