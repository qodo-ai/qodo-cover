import io
import os
import tarfile

from enum import Enum
from typing import Any, Iterable

import docker

from docker.errors import APIError, BuildError, DockerException
from docker.models.containers import Container
from rich.progress import Progress, TextColumn

from cover_agent.custom_logger import CustomLogger
from cover_agent.settings.config_loader import get_settings
from cover_agent.utils import truncate_hash


logger = CustomLogger.get_logger(__name__)


settings = get_settings().get("default")
HASH_DISPLAY_LENGTH = settings.docker_hash_display_length


class DockerUtilityError(Exception):
    """Raised when a Docker operation fails."""


class DockerStatus(Enum):
    """
    Enum representing various statuses during Docker operations.
    """

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
    ("Pull complete", DockerStatus.PULL_COMPLETE),
    ("Waiting", DockerStatus.WAITING),
]


def get_docker_image(
    client: docker.DockerClient, dockerfile: str | None, docker_image: str, platform: str = "linux/amd64"
) -> str:
    """
    Retrieves a Docker image by either building it from a Dockerfile or pulling it from a registry.

    Args:
        client (docker.DockerClient): Docker client instance.
        dockerfile (str | None): Path to the Dockerfile. If None, the image will be pulled.
        docker_image (str): Name of the Docker image to pull.
        platform (str): Target platform for the image. Defaults to "linux/amd64".

    Returns:
        str: The tag of the obtained Docker image.

    Raises:
        DockerUtilityError: If the image build or pull operation fails.
    """
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
        raise DockerUtilityError("Failed to build or pull Docker image.") from e

    logger.info(f"Successfully obtained the Docker image {image_tag}.")
    return image_tag


def build_docker_image(
    client: docker.DockerClient, dockerfile: str, image_tag: str, platform: str = "linux/amd64"
) -> None:
    """
    Builds a Docker image from the specified Dockerfile.
    Force build for x86_64 architecture (`linux/amd64`) even for Apple Silicon currently.

    Args:
        client (docker.DockerClient): Docker client instance.
        dockerfile (str): Path to the Dockerfile.
        image_tag (str): Tag to assign to the built image.
        platform (str): Target platform for the image. Defaults to "linux/amd64".

    Raises:
        DockerUtilityError: If the build operation fails.
    """
    logger.info(f"Starting to build the Docker image {image_tag} using Dockerfile {dockerfile} on platform {platform}.")
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
    """
    Creates a tar archive of the build context directory.

    This function takes a directory path as input, iterates through all files
    within the directory (and its subdirectories), and adds them to a tar archive.
    The resulting tar archive is returned as an in-memory byte stream.

    Args:
        build_dir (str): The path to the directory to be archived.

    Returns:
        io.BytesIO: An in-memory byte stream containing the tar archive.

    Raises:
        OSError: If there is an issue accessing files in the directory.

    Example:
        tar_stream = create_build_context("/path/to/build_dir")
        with open("build_context.tar", "wb") as f:
             f.write(tar_stream.read())
    """
    logger.info(f"Creating build context for directory: {build_dir}")
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
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
    """
    Pulls a Docker image from a registry and tags it with a specified tag.

    This function first pulls the specified Docker image from the registry using the provided
    Docker client. After successfully pulling the image, it tags the image with the given tag.

    Args:
        client (docker.DockerClient): The Docker client instance used to interact with the Docker API.
        docker_image (str): The name of the Docker image to pull from the registry.
        image_tag (str): The tag to assign to the pulled Docker image.

    Raises:
        DockerUtilityError: If the image pull or tagging operation fails.

    Example:
        pull_and_tag_docker_image(client, "python:3.11", "my-python-image")
    """
    logger.info(f"Pulling the Docker image {docker_image} ...")

    try:
        stream = client.api.pull(docker_image, stream=True, decode=True)
        stream_docker_pull_output(stream)
    except docker.errors.APIError as e:
        logger.error(f"Failed to pull image {docker_image}: {e}")
        raise DockerUtilityError(f"Pull failed for image {docker_image}") from e

    try:
        logger.info(f"Tagging the Docker image {docker_image} ...")
        image = client.images.get(docker_image)
        image.tag(image_tag)
        logger.info(f"Tagged the Docker image {docker_image} as {image_tag}")
    except docker.errors.ImageNotFound as e:
        logger.error(f"Pulled Docker image {docker_image} could not be found for tagging.")
        raise DockerUtilityError("Image tagging failed: image not found") from e


def get_docker_image_workdir(client: docker.DockerClient, image_tag: str) -> str:
    """
    Get the WORKDIR of a Docker image.

    Args:
        client (docker.DockerClient): Docker client instance.
        image_tag (str): Tag of the Docker image to inspect.

    Returns:
        str: The WORKDIR of the image. Defaults to "/" if not set.

    Raises:
        DockerUtilityError: If the image inspection fails.
    """
    try:
        image = client.images.get(image_tag)
        workdir = image.attrs.get("Config", {}).get("WorkingDir", "/")
        logger.info(f"Working directory for image {image_tag}: {workdir}")

        return workdir
    except docker.errors.ImageNotFound as e:
        logger.error(f"Docker image {image_tag} not found")
        raise DockerUtilityError(f"Failed to inspect Docker image {image_tag}") from e
    except docker.errors.APIError as e:
        logger.error(f"Docker API error while inspecting image {image_tag}: {e}")
        raise DockerUtilityError(f"Failed to inspect Docker image {image_tag}") from e
    except AttributeError as e:
        msg = f"Docker image attribute error for {image_tag}"
        logger.error(f"{msg}: {e}")
        raise DockerUtilityError(msg) from e


def run_docker_container(
    client: docker.DockerClient,
    image: str,
    volumes: dict[str, Any],
    command: str = "/bin/sh -c 'tail -f /dev/null'",  # Keeps container alive
    container_env: dict[str, Any] | None = None,
    remove: bool = False,
) -> Container:
    """
    Runs a Docker container with the specified configuration.

    This function starts a Docker container using the provided image, volumes, and command.
    It also allows setting environment variables and optionally removes the container after it stops.

    Args:
        client (docker.DockerClient): The Docker client instance used to interact with the Docker API.
        image (str): The name of the Docker image to use for the container.
        volumes (dict[str, Any]): A dictionary mapping host paths to container paths for volume mounting.
        command (str): The command to run inside the container. Defaults to keeping the container alive.
        container_env (dict[str, Any] | None): Environment variables to set inside the container. Defaults to None.
        remove (bool): Whether to automatically remove the container after it stops. Defaults to False.

    Returns:
        Container: The Docker container instance.

    Raises:
        DockerUtilityError: If the container fails to start or encounters an error.

    Example:
        container = run_docker_container(
            client=docker_client,
            image="python:3.9",
            volumes={"/host/path": {"bind": "/container/path", "mode": "rw"}},
            command="python script.py",
            container_env={"ENV_VAR": "value"},
            remove=True,
        )
    """
    if container_env is None:
        container_env = {}

    try:
        logger.info(f"Running the Docker container for the Docker image {image}...")
        container = client.containers.run(
            image=image,
            command=command,
            volumes=volumes,
            detach=True,  # Run in the background
            tty=True,
            environment=container_env,
            remove=remove,
        )

        container_info = {
            "Started container ID": truncate_hash(container.id, HASH_DISPLAY_LENGTH),
            "Container image": container.attrs.get("Config", {}).get("Image"),
            "Container name": container.attrs.get("Name")[1:],
            "Container created at": container.attrs.get("Created"),
            "Cmd": container.attrs.get("Config", {}).get("Cmd"),
        }
        log_multiple_lines(container_info)

    except DockerException as e:
        logger.error(f"Error running the Docker container: {e}")
        if "container" in locals():
            logger.info(f"Removing the Docker container {container.name}...")
            container.remove(force=True)
        raise DockerUtilityError("Failed to run Docker container") from e

    return container


def copy_file_to_docker_container(container: Container, src_path: str, dest_path: str) -> None:
    """
    Copies a file from the host system to a specified path inside a Docker container.

    This function reads the file from the host system, creates a tar archive containing the file,
    and transfers the archive to the specified destination path inside the Docker container.

    Args:
        container (Container): The Docker container instance where the file will be copied.
        src_path (str): The path to the source file on the host system.
        dest_path (str): The destination path inside the Docker container.

    Raises:
        FileNotFoundError: If the source file does not exist.
        OSError: If there is an issue reading the source file or creating the tar archive.

    Example:
        copy_file_to_docker_container(container, "/host/path/file.txt", "/container/path/file.txt")
    """
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
    """
    Executes a command inside a running Docker container.

    This function creates an execution environment within the specified Docker container,
    runs the provided command, and streams the output (stdout and stderr). If the command
    fails (non-zero exit code), the container is cleaned up, and an exception is raised.

    Args:
        container (Container): The Docker container instance where the command will be executed.
        command (list[str]): The command to execute inside the container, provided as a list of strings.
        exec_env (dict[str, Any]): Environment variables to set for the command execution.

    Raises:
        DockerUtilityError: If the command execution fails or the exit code is non-zero.
        DockerException: If there is an error interacting with the Docker API.

    Example:
        run_command_in_docker_container(
            container=my_container,
            command=["python", "script.py"],
            exec_env={"ENV_VAR": "value"},
        )
    """
    try:
        joined_command = " ".join(command)
        logger.info(f"Running the command in the Docker container: {joined_command}")

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
            clean_up_docker_container(container)  # Force clean-up container on failure
            raise DockerUtilityError(f"Test command failed with exit code {exit_code}")

        logger.info("Done.")
    except DockerException as e:
        logger.error(f"Failed to execute the command in the Docker container {container.name}: {e}")
        raise DockerUtilityError("Execution inside Docker container failed") from e


def clean_up_docker_container(container: Container) -> None:
    """
    Cleans up a Docker container by stopping and optionally removing it.

    This function stops the specified Docker container and, if `force_remove` is True,
    removes the container from the Docker host.

    Args:
        container (Container): The Docker container instance to clean up.

    Returns:
        None

    Example:
        clean_up_docker_container(container=my_container, force_remove=True)
    """
    logger.info("Cleaning up...")
    logger.info(f"Stop the Docker container {truncate_hash(container.id, HASH_DISPLAY_LENGTH)}.")
    container.stop()

    logger.info(f"Remove the Docker container {truncate_hash(container.id, HASH_DISPLAY_LENGTH)}.")
    container.remove()


def normalize_status(raw_status: str) -> DockerStatus:
    """
    Normalizes a raw Docker status string to a corresponding DockerStatus enum value.

    This function trims the input status string, checks if it matches the "PULL_COMPLETE" status,
    and iterates through a predefined mapping of status prefixes to determine the appropriate
    DockerStatus enum value. If no match is found, it returns DockerStatus.UNKNOWN.

    Args:
        raw_status (str): The raw status string to normalize.

    Returns:
        DockerStatus: The corresponding DockerStatus enum value.

    Example:
        normalize_status("Pulling fs layer")

        DockerStatus.PULLING_FS_LAYER
    """
    raw_status = raw_status.strip()
    if raw_status == DockerStatus.PULL_COMPLETE.value:
        return DockerStatus.PULL_COMPLETE

    for prefix, status in _STATUS_PREFIX_MAP:
        if raw_status.startswith(prefix):
            return status

    return DockerStatus.UNKNOWN


def stream_docker_build_output(stream: Iterable[dict]) -> None:
    """
    Streams and processes the output of a Docker build operation.

    This function iterates through the provided stream of dictionaries, which represent
    the output of a Docker build process. It handles and logs different types of messages
    such as build progress, errors, and error details.

    Args:
        stream (Iterable[dict]): An iterable of dictionaries containing Docker build output.

    Example:
        stream_docker_build_output(build_stream)
    """
    for line in stream:
        if "stream" in line:
            print(line["stream"], end="")  # line already has a newline
        elif "error" in line:
            logger.error(line["error"])
        elif "errorDetail" in line:
            logger.error(line["errorDetail"].get("message", "Unknown error"))


def stream_docker_pull_output(stream: Iterable[dict]) -> None:
    """
    Streams and processes the output of a Docker pull operation.

    This function uses a progress bar to display the status of each layer being pulled.
    It iterates through the provided stream of dictionaries, which represent the output
    of a Docker pull process, and updates the progress bar accordingly.

    Args:
        stream (Iterable[dict]): An iterable of dictionaries containing Docker pull output.

    Example:
        stream_docker_pull_output(pull_stream)
    """
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
    """
    Streams and processes the output of a command executed inside a Docker container.

    This function iterates through the provided iterable of tuples, where each tuple contains
    the stdout and stderr output of the command execution. It decodes and prints the output
    to the console in real-time.

    Args:
        exec_start (Iterable[tuple[bytes, bytes]]): An iterable of tuples containing the
        stdout and stderr output as byte strings.

    Example:
        exec_start = [(b'output line 1\\n', b''), (b'', b'error line 1\\n')]
        stream_docker_run_command_output(exec_start)
        output line 1
        error line 1
    """
    for data in exec_start:
        stdout, stderr = data
        if stdout:
            print(stdout.decode(), end="")
        if stderr:
            print(stderr.decode(), end="")


def show_progress(line: dict, progress: Progress, id_to_task: dict[str, int] | None = None) -> None:
    """
    Updates or creates progress tasks for Docker layer operations.

    This function processes a line of Docker pull or build output, normalizes the status,
    and updates the progress bar for the corresponding layer. If the layer does not already
    have a task, a new one is created.

    Args:
        line (dict): A dictionary containing information about the Docker operation, such as
                     layer ID, status, and progress.
        progress (Progress): A `rich.progress.Progress` instance used to display progress bars.
        id_to_task (dict[str, int] | None): A mapping of layer IDs to task IDs in the progress bar.
                                            Defaults to None, in which case a new dictionary is created.

    Returns:
        None
    """
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
    """
    Logs multiple lines of key-value pairs.

    This function iterates through a dictionary of key-value pairs and logs each pair
    as an informational message.

    Args:
        lines (dict[str, Any]): A dictionary where keys are labels (str) and values are the corresponding data (Any).

    Returns:
        None

    Example:
        log_multiple_lines({"Key1": "Value1", "Key2": "Value2"})
        # Logs:
        # Key1: Value1
        # Key2: Value2
    """
    for label, value in lines.items():
        logger.info(f"{label}: {value}")


def get_short_docker_image_name(image_name: str) -> str:
    """
    Extracts the short name of a Docker image from its full name.

    This function takes a Docker image name (which may include a repository path and a tag)
    and returns only the short name of the image (the last part of the repository path).

    Args:
        image_name (str): The full name of the Docker image, including the repository path
                          and optionally a tag (e.g., "repository/path/image:tag").

    Returns:
        str: The short name of the Docker image (e.g., "image").
    """
    repository = image_name.split(":")[0]  # Remove the tag if present
    return repository.split("/")[-1]  # Extract the last part of the repository path
