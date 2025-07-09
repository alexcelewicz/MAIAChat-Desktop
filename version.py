#!/usr/bin/env python3
"""
MAIAChat Desktop - Version Management
Centralized version information for the application.
Created by Aleksander Celewicz
"""

# Application Version Information
__version__ = "1.0.0"
__version_info__ = (1, 0, 0)

# Release Information
RELEASE_NAME = "Genesis"
RELEASE_DATE = "2025-01-30"
RELEASE_TYPE = "stable"  # stable, beta, alpha, rc

# Build Information
BUILD_NUMBER = "001"
BUILD_DATE = "2025-01-30"

# Application Metadata
APP_NAME = "MAIAChat"
APP_TITLE = "MAIAChat Desktop"
APP_DESCRIPTION = "Multi-Agent AI Assistant Desktop Application"
APP_AUTHOR = "Aleksander Celewicz"
APP_COMPANY = "MAIAChat.com"
APP_COPYRIGHT = "© 2025 Aleksander Celewicz"
APP_LICENSE = "MIT License"

# Social Media & Channel Information
YOUTUBE_CHANNEL = "https://www.youtube.com/@AIexTheAIWorkbench"
YOUTUBE_CHANNEL_NAME = "AIex The AI Workbench"
WEBSITE_URL = "https://maiachat.com"
GITHUB_URL = "https://github.com/alexcelewicz/MAIAChat-Desktop"

# Version Display Formats
def get_version_string():
    """Get the full version string."""
    return f"{__version__}"

def get_version_with_build():
    """Get version with build number."""
    return f"{__version__}.{BUILD_NUMBER}"

def get_full_version_info():
    """Get comprehensive version information."""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "release_name": RELEASE_NAME,
        "release_date": RELEASE_DATE,
        "release_type": RELEASE_TYPE,
        "build_number": BUILD_NUMBER,
        "build_date": BUILD_DATE,
        "app_name": APP_NAME,
        "app_title": APP_TITLE,
        "description": APP_DESCRIPTION,
        "author": APP_AUTHOR,
        "company": APP_COMPANY,
        "copyright": APP_COPYRIGHT,
        "license": APP_LICENSE
    }

def get_version_display():
    """Get formatted version for UI display."""
    return f"Version {__version__} ({RELEASE_NAME})"

def get_about_text():
    """Get formatted text for About dialog."""
    return f"""
{APP_TITLE}
Version {__version__} - {RELEASE_NAME}
Released: {RELEASE_DATE}

{APP_DESCRIPTION}

Created by {APP_AUTHOR}
{APP_COPYRIGHT}
Licensed under {APP_LICENSE}

🌐 Website: {WEBSITE_URL}
📺 YouTube: {YOUTUBE_CHANNEL_NAME}
🔗 GitHub: {GITHUB_URL}
    """.strip()

def get_social_links():
    """Get social media and channel links."""
    return {
        "website": WEBSITE_URL,
        "youtube": YOUTUBE_CHANNEL,
        "youtube_name": YOUTUBE_CHANNEL_NAME,
        "github": GITHUB_URL
    }

# Version Comparison Utilities
def parse_version(version_string):
    """Parse version string into tuple for comparison."""
    try:
        parts = version_string.split('.')
        return tuple(int(part) for part in parts[:3])
    except (ValueError, IndexError):
        return (0, 0, 0)

def compare_versions(version1, version2):
    """Compare two version strings. Returns -1, 0, or 1."""
    v1 = parse_version(version1)
    v2 = parse_version(version2)
    
    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0

def is_newer_version(current, new):
    """Check if new version is newer than current."""
    return compare_versions(current, new) < 0

# Git Tag Format
def get_git_tag():
    """Get the git tag format for this version."""
    return f"v{__version__}"

# Changelog Entry Format
def get_changelog_header():
    """Get changelog header for this version."""
    return f"## [{__version__}] - {RELEASE_DATE} - {RELEASE_NAME}"

if __name__ == "__main__":
    # Print version information when run directly
    print("MAIAChat Desktop Version Information")
    print("=" * 40)
    
    info = get_full_version_info()
    for key, value in info.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("\nFormatted Displays:")
    print(f"Version String: {get_version_string()}")
    print(f"Version with Build: {get_version_with_build()}")
    print(f"Version Display: {get_version_display()}")
    print(f"Git Tag: {get_git_tag()}")
    print(f"Changelog Header: {get_changelog_header()}")
