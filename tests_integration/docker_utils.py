import io
import os
import sys
import tarfile

from enum import Enum
from typing import Any, Iterable

import docker
from docker.errors import APIError, BuildError, DockerException
from docker.models.containers import Container
from rich.progress import Progress, TextColumn

from cover_agent.CustomLogger import CustomLogger


logger = CustomLogger.get_logger(__name__)


class DockerStatus(Enum):
    PULLING_FS_LAYER = "Pulling fs layer"
    DOWNLOADING = "Downloading"
    DOWNLOAD_COMPLETE = "Download complete"
    EXTRACTING = "Extracting"
    VERIFYING_CHECKSUM = "Verifying checksum"
    PULL_COMPLETE = "Pull complete"
    WAITING = "Waiting"
    UNKNOWN = "Unknown"


_STATUS_PREFIX_MAP: list[tuple[str, DockerStatus]] = [
    ("Pulling fs layer", DockerStatus.PULLING_FS_LAYER),
    ("Download complete", DockerStatus.DOWNLOAD_COMPLETE),
    ("Download", DockerStatus.DOWNLOADING),
    ("Extract", DockerStatus.EXTRACTING),
    ("Verifying checksum", DockerStatus.VERIFYING_CHECKSUM),
    ("Waiting", DockerStatus.WAITING),
]


def get_docker_image(
    client: docker.DockerClient, dockerfile: str | None, docker_image: str, platform: str = "linux/amd64"
) -> str:
    """Get the Docker image by either building or pulling it."""
    logger.info(f"Starting to get the Docker image {docker_image} with platform {platform}...")
    image_tag = "cover-agent-image"

    try:
        if dockerfile:
            logger.info(f"Building Docker image using Dockerfile {dockerfile}...")
            build_docker_image(client, dockerfile, image_tag, platform)
        else:
            logger.info(f"Pulling and tagging Docker image {docker_image}...")
            pull_and_tag_docker_image(client, docker_image, image_tag)
    except (BuildError, APIError) as e:
        logger.error(f"Docker error: {e}")
        sys.exit(1)

    logger.info(f"Successfully obtained the Docker image {image_tag}.")
    return image_tag


def build_docker_image(
        client: docker.DockerClient, dockerfile: str, image_tag: str, platform: str = "linux/amd64"
) -> None:
    """
    Builds a Docker image from the specified Dockerfile.
    Force build for x86_64 architecture (`linux/amd64`) even for Apple Silicon currently.
    """
    logger.info(
        f"Starting to build the Docker image {image_tag} using Dockerfile {dockerfile} on platform {platform}."
    )
    dockerfile_dir = os.path.dirname(dockerfile) or "."
    dockerfile_name = os.path.basename(dockerfile)

    logger.debug(f"Creating build context from directory {dockerfile_dir}...")
    context_tar = create_build_context(dockerfile_dir)

    logger.info(f"Initiating Docker build for image {image_tag}...")
    build_stream = client.api.build(
        fileobj=context_tar,
        custom_context=True,
        dockerfile=dockerfile_name,
        tag=image_tag,
        rm=True,
        decode=True,
        platform=platform,
    )
    stream_docker_build_output(build_stream)
    logger.info(f"Successfully built the Docker image: {image_tag}")


def create_build_context(build_dir: str) -> io.BytesIO:
    """Creates a tar archive of the build context directory."""
    logger.info(f"Creating build context for directory: {build_dir}")
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        for root, _, files in os.walk(build_dir):
            for file in files:
                fullpath = os.path.join(root, file)
                arcname = os.path.relpath(fullpath, start=build_dir)
                logger.debug(f"Adding file to tar: {fullpath} as {arcname}")
                tar.add(fullpath, arcname=arcname)

    tar_stream.seek(0)
    logger.info("Build context creation completed.")
    return tar_stream


def pull_and_tag_docker_image(client: docker.DockerClient, docker_image: str, image_tag: str) -> None:
    """Pulls a Docker image and tags it."""
    logger.info(f"Pulling the Docker image {docker_image} ...")

    try:
        stream = client.api.pull(docker_image, stream=True, decode=True)
        stream_docker_pull_output(stream)
    except docker.errors.APIError as e:
        logger.error(f"Failed to pull image {docker_image}: {e}")
        sys.exit(1)

    try:
        logger.info(f"Tagging the Docker image {docker_image} ...")
        image = client.images.get(docker_image)
        image.tag(image_tag)
        logger.info(f"Tagged the Docker image {docker_image} as {image_tag}")
    except docker.errors.ImageNotFound:
        logger.error(f"Pulled Docker image {docker_image} could not be found for tagging.")
        sys.exit(1)


def run_docker_container(
        client: docker.DockerClient,
        image: str,
        volumes: dict[str, Any],
        command: str="/bin/sh -c 'tail -f /dev/null'",  # Keeps container alive
        container_env: dict[str, Any] | None = None,
        remove: bool=False,
) -> Container:
    if container_env is None:
        container_env = {}

    try:
        logger.info(f"Running the Docker container for the Docker image {image}...")
        container = client.containers.run(
            image=image,
            command=command,
            volumes=volumes,
            detach=True,  # Run in background
            tty=True,
            environment=container_env,
            remove=remove,
        )

        container_info = {
            "Started container": container.id,
            "Container image": container.attrs.get("Config", {}).get("Image"),
            "Container name": container.attrs.get("Name")[1:],
            "Container ID": container.attrs.get("Id"),
            "Container created at": container.attrs.get("Created"),
            "Cmd": container.attrs.get("Config", {}).get("Cmd"),
        }
        log_multiple_lines(container_info)

    except DockerException as e:
        logger.error(f"Error running the Docker container: {e}")
        if "container" in locals():
            logger.debug(f"Removing the Docker container {container.name}...")
            container.remove(force=True)
        sys.exit(1)

    return container


def copy_file_to_docker_container(container: Container, src_path: str, dest_path: str) -> None:
    logger.info(f"Copying file from {src_path} to {dest_path} in the Docker container {container.name}...")
    with open(src_path, "rb") as f:
        data = f.read()

    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        tarinfo = tarfile.TarInfo(name=os.path.basename(dest_path))
        tarinfo.size = len(data)
        tarinfo.mode = 0o755  # Make it executable
        logger.debug(f"Adding file {src_path} to tar archive as {dest_path}...")
        tar.addfile(tarinfo, io.BytesIO(data))

    tar_stream.seek(0)
    logger.info(f"Sending tar archive to the Docker container {container.name} at {os.path.dirname(dest_path)}...")
    container.put_archive(path=os.path.dirname(dest_path), data=tar_stream)
    logger.info(f"File {src_path} successfully copied to {dest_path} in the Docker container {container.name}.")


def run_command_in_docker_container(container: Container, command: list[str], exec_env: dict[str, Any]) -> None:
    try:
        joined_command = " ".join(command)
        logger.info(f"Running the cover-agent command: {joined_command}")

        exec_create = container.client.api.exec_create(
            container.id,
            cmd=command,
            environment=exec_env if exec_env else None,
        )
        exec_id = exec_create["Id"]

        exec_start = container.client.api.exec_start(
            exec_id,
            stream=True,
            demux=True,  # separates stdout and stderr
        )
        stream_docker_run_command_output(exec_start)

        exec_inspect = container.client.api.exec_inspect(exec_id)
        exit_code = exec_inspect["ExitCode"]

        logger.debug(f"The command {joined_command} finished with exit code: {exit_code}")
        if exit_code != 0:
            logger.error(f"Error running command {joined_command}.")
            logger.error(f"Test failed with exit code {exit_code}.")
            clean_up_docker_container(container)
            sys.exit(exit_code)

        logger.info("Done.")
    except DockerException as e:
        logger.error(f"Failed to execute the command in the Docker container {container.name}: {e}")
        sys.exit(1)


def clean_up_docker_container(container: Container, force_remove: bool=True) -> None:
    logger.info("Cleaning up...")
    logger.info(f"Stop the Docker container {container.id}...")
    container.stop()

    if force_remove:
        logger.info(f"Remove the Docker container {container.id}...")
        container.remove()


def normalize_status(raw_status: str) -> DockerStatus:
    raw_status = raw_status.strip()
    if raw_status == DockerStatus.PULL_COMPLETE.value:
        return DockerStatus.PULL_COMPLETE

    for prefix, status in _STATUS_PREFIX_MAP:
        if raw_status.startswith(prefix):
            return status

    return DockerStatus.UNKNOWN


def stream_docker_build_output(stream: Iterable[dict]) -> None:
    for line in stream:
        if "stream" in line:
            print(line["stream"], end="")  # line already has newline
        elif "error" in line:
            logger.error(line["error"])
        elif "errorDetail" in line:
            logger.error(line["errorDetail"].get("message", "Unknown error"))


def stream_docker_pull_output(stream: Iterable[dict]) -> None:
    progress = Progress(
        TextColumn("{task.fields[layer_id]}", justify="left"),
        TextColumn("{task.fields[status]}", justify="left"),
        TextColumn("{task.fields[docker_progress]}", justify="right"),
        expand=False,
    )

    id_to_task = {}
    with progress:
        for line in stream:
            show_progress(line, progress, id_to_task)


def stream_docker_run_command_output(exec_start: Iterable[tuple[bytes, bytes]]) -> None:
    for data in exec_start:
        stdout, stderr = data
        if stdout:
            print(stdout.decode(), end="")
        if stderr:
            print(stderr.decode(), end="")


def show_progress(line: dict, progress: Progress, id_to_task: dict[str, int] | None = None) -> None:
    if id_to_task is None:
        id_to_task = {}

    layer_id = line.get("id")
    if not layer_id or layer_id == "latest":
        logger.debug(f"Skipping line with invalid or non-layer ID: {line}")
        return

    docker_progress = line.get("progress", "")
    normalized_status = normalize_status(line.get("status", ""))
    task_fields = {"layer_id": layer_id, "status": normalized_status.value, "docker_progress": docker_progress}

    task_id = id_to_task.get(layer_id)
    if task_id is None:
        logger.debug(f"Creating new task for layer_id {layer_id}: {task_fields}")
        task_id = progress.add_task(
            description=normalized_status.value, total=100, completed=0, visible=True, **task_fields
        )
        id_to_task[layer_id] = task_id
    else:
        logger.debug(f"Updating task {task_id} for layer_id {layer_id}: {task_fields}")
        progress.update(task_id, **task_fields)


def log_multiple_lines(lines: dict[str, Any]) -> None:
    for label, value in lines.items():
        logger.info(f"{label}: {value}")
