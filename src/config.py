"""User preferences for job search."""

from dataclasses import dataclass

DEFAULT_ROLE = "Android Developer"
DEFAULT_LOCATION = ""


@dataclass
class SearchPreferences:
    """User-provided search criteria."""

    role: str
    location: str


def collect_preferences() -> SearchPreferences:
    """Prompt user for role and location, with defaults. Empty location means any location."""
    role_input = input(f"Role [{DEFAULT_ROLE}]: ").strip() or DEFAULT_ROLE
    location_input = input(
        f"Location (leave empty for any) [{DEFAULT_LOCATION}]: "
    ).strip()
    return SearchPreferences(role=role_input, location=location_input)
