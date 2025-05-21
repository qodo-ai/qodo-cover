import pytest

from tests_integration.docker_utils import get_short_docker_image_name


@pytest.mark.parametrize(
    "image_name, expected_short_name",
    [
        ("repository/path/image:tag", "image"),  # Full image name with repository and tag
        ("repository/path/image", "image"),  # Full image name with repository, no tag
        ("image:tag", "image"),  # Image name with tag, no repository
        ("image", "image"),  # Image name only
        ("repository/image:tag", "image"),  # Repository and image name with tag
        ("repository/image", "image"),  # Repository and image name, no tag
        ("", ""),  # Empty image name
        (":tag", ""),  # Only tag, no image name
        ("/:tag", ""),  # Slash and tag, no image name
    ],
)
def test_get_short_docker_image_name_extracts_short_name_from_full_image_name(image_name, expected_short_name):
    """
    Tests the `get_short_docker_image_name` function to ensure it correctly extracts
    the short name of a Docker image from its full name.

    Args:
        image_name (str): The full name of the Docker image, including repository path
                          and optionally a tag.
        expected_short_name (str): The expected short name of the Docker image.

    Asserts:
        The function `get_short_docker_image_name` returns the correct short name
        for the given `image_name`.
    """
    assert get_short_docker_image_name(image_name) == expected_short_name
