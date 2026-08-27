import os
import json
import requests
import re

# CONFIGURATION
TARGET_REPO = "gunnerkidBT/TwitchAdBlock"
JSON_FILENAME = "TwitchAdBlock.json"
APP_ICON_URL = "https://is1-ssl.mzstatic.com/image/thumb/PurpleSource221/v4/19/2e/1e/192e1ed8-7939-14eb-17e3-037a18e02548/Placeholder.mill/200x200bb-75.webp"

def get_latest_release():
    url = f"https://api.github.com/repos/{TARGET_REPO}/releases/latest"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error connecting to GitHub API: {response.status_code}")
        return None
        
    return response.json()

def clean_variant_name(filename, base_common_prefix):
    # Remove .ipa extension
    name_without_ext = filename[:-4]
    
    # Remove common prefix to isolate the variant difference
    variant = name_without_ext.replace(base_common_prefix, "").strip("-")
    
    if not variant:
        return "Standard"
        
    # Replace dashes with spaces
    variant = variant.replace("-", " ")
    return variant

def generate_source_json(release):
    if not release:
        return
        
    tag_name = release.get("tag_name", "v0.0.0")
    version = tag_name.lstrip("v")
    release_notes = release.get("body", "No release notes provided.")
    published_date = release.get("published_at", "")
    
    # Filter assets ending with .ipa
    ipa_assets = [asset for asset in release.get("assets", []) if asset["name"].endswith(".ipa")]
    
    if not ipa_assets:
        print("No .ipa files found in the latest release.")
        return

    # Find exact common prefix among all ipas to clean up variant names
    filenames = [asset["name"] for asset in ipa_assets]
    common_prefix = os.path.commonprefix(filenames)
    common_prefix = re.sub(r'[-_]+$', '', common_prefix)

    apps_list = []

    for index, asset in enumerate(ipa_assets):
        filename = asset["name"]
        ipa_url = asset["browser_download_url"]
        ipa_size = asset["size"]
        
        # Extract variant description
        variant_desc = clean_variant_name(filename, common_prefix)
        
        # Build clean name and identifiers
        if variant_desc.lower() == "standard" or not variant_desc:
            app_name = "TwitchAdBlock"
            subtitle = "Adblock + Extra features"
            identifier_suffix = "standard"
        else:
            app_name = f"TwitchAdBlock ({variant_desc})"
            subtitle = f"Variant: {variant_desc}"
            identifier_suffix = variant_desc.lower().replace(" ", "-")

        app_entry = {
            "name": app_name,
            "bundleIdentifier": f"tv.twitch",
            "developer": "gunnerkidBT",
            "subtitle": subtitle,
            "localizedDescription": release_notes,
            "iconURL": APP_ICON_URL,
            "versions": [
                {
                    "version": version,
                    "date": published_date,
                    "localizedDescription": release_notes,
                    "downloadURL": ipa_url,
                    "size": ipa_size
                }
            ]
        }
        apps_list.append(app_entry)

    # LiveContainer source structure JSON format
    repo_data = {
        "name": "TwitchAdBlock Source",
        "identifier": "com.twitchadblock.autoupdate.source",
        "description": "Automatically updated TwitchAdBlock source from GitHub.",
        "tintColor": "9146FF",
        "iconURL": APP_ICON_URL,
        "apps": apps_list
    }

    with open(JSON_FILENAME, "w", encoding="utf-8") as f:
        json.dump(repo_data, f, indent=4)
    print(f"File {JSON_FILENAME} successfully updated with {len(apps_list)} variants for version {version}.")

if __name__ == "__main__":
    release_info = get_latest_release()
    if release_info:
        generate_source_json(release_info)
