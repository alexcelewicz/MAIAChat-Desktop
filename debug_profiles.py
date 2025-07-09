#!/usr/bin/env python3
"""
MAIAChat Desktop - Profile System Diagnostic Tool

Created by Aleksander Celewicz
Website: MAIAChat.com

This diagnostic tool helps verify the profile system is working correctly
and displays available example profiles for new users.

Usage: python debug_profiles.py
"""

import logging
import sys
from pathlib import Path

def analyze_profiles():
    """Analyze available profiles and their configuration."""
    try:
        from managers.profile_manager import profile_manager

        profiles = profile_manager.get_profile_list()
        print(f"=== PROFILE SYSTEM ANALYSIS ===")
        print(f"Total profiles found: {len(profiles)}")

        if not profiles:
            print("No profiles found. This may indicate:")
            print("- Missing example_profiles directory")
            print("- Profile loading issues")
            print("- First-time setup required")
            return False

        print("\nExample profiles available:")
        example_count = 0
        custom_count = 0

        for name, desc, is_example in profiles:
            if is_example:
                example_count += 1
                print(f"  ✓ {name}")
                if desc:
                    print(f"    Description: {desc[:80]}{'...' if len(desc) > 80 else ''}")
            else:
                custom_count += 1

        print(f"\nProfile summary:")
        print(f"  Example profiles: {example_count}")
        print(f"  Custom profiles: {custom_count}")

        if example_count == 0:
            print("\nWarning: No example profiles found!")
            print("New users may have difficulty getting started.")

        return True

    except ImportError as e:
        print(f"Error importing profile manager: {e}")
        print("This may indicate missing dependencies or incorrect installation.")
        return False
    except Exception as e:
        print(f"Error analyzing profiles: {e}")
        return False

def main():
    """Run profile system diagnostics."""
    print("MAIAChat Desktop - Profile System Diagnostics")
    print("=" * 50)

    success = analyze_profiles()

    print("\n" + "=" * 50)
    if success:
        print("✓ Profile system appears to be working correctly")
    else:
        print("✗ Profile system issues detected")
        print("Check the error messages above for troubleshooting guidance")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
