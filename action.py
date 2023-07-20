"""
This module contains functions for interacting with Elastic Beanstalk environments.
"""

import os
import sys
import time
from dataclasses import dataclass
from boto3.session import Session


READY_STATUS = "Ready"


@dataclass
class EnvironmentStatus:
    """
    Dataclass for storing environment status"""
    version_label: str
    status: str
    health_status: str

    def __str__(self) -> str:
        return f"""EnvironmentStatus(version_label={self.version_label},
                 status={self.status}, health_status={self.health_status})"""


def get_environment_version(env_name, client) -> EnvironmentStatus:
    """
    Get environment version from Elastic Beanstalk"""
    response = client.describe_environments(
        EnvironmentNames=[
            env_name,
        ]
    )
    if len(response.get("Environments")) == 0:
        print(f"Environment {env_name} not found")
        sys.exit(1)
    version_label = response.get("Environments")[0].get("VersionLabel")
    status = response.get("Environments")[0].get("Status")
    health_status = response.get("Environments")[0].get("HealthStatus")
    env_status = EnvironmentStatus(version_label, status, health_status)
    print(str(env_status))
    return env_status


def is_env_ready(env_status: EnvironmentStatus, app_version_label: str) -> bool:
    """
    Check if environment is ready"""
    version_is_ok = env_status.version_label == app_version_label and app_version_label is not None
    if app_version_label is None:
        version_is_ok = True    # no version check required
    status_is_ok = env_status.status == READY_STATUS
    return version_is_ok and status_is_ok


def main():
    """
    Main function for action"""
    region = os.environ['INPUT_REGION']
    timeout = int(os.environ.get('INPUT_TIMEOUT', '60'))
    env_name = os.environ['INPUT_ENV_NAME']
    app_version_label = os.environ['INPUT_APP_VERSION_LABEL']
    timeout = int(timeout)
    start = time.time()

    session = Session(region_name=region)
    client = session.client('elasticbeanstalk')

    env_status = get_environment_version(env_name, client)
    while is_env_ready(env_status, app_version_label) is False and (time.time() - start) < timeout:
        time.sleep(5)
        env_status = get_environment_version(env_name, region)

    print(f'::set-output name=health-status::{env_status.health_status}')
    print(f'::set-output name=version-label::{env_status.version_label}')
    print(f'::set-output name=status::{env_status.status}')

    if is_env_ready(env_status, app_version_label) is False:
        print(f"""Fail. Expected version {app_version_label}
               but got {env_status.version_label}. Status: {env_status.status}""")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()