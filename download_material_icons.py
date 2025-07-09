import os
import requests
from pathlib import Path

# Create icons directory if it doesn't exist
icons_dir = Path("icons")
icons_dir.mkdir(exist_ok=True)

# Dictionary of icon names and their URLs (using Material Design Icons)
icons = {
    "file.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/file/upload_file/materialicons/24px.svg",
    "database.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/file/folder/materialicons/24px.svg",
    "send.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/content/send/materialicons/24px.svg",
    "chat.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/communication/chat/materialicons/24px.svg",
    "stop.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/content/block/materialicons/24px.svg",
    "clear.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/content/clear/materialicons/24px.svg",
    "pdf.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/file/download/materialicons/24px.svg",
    "refresh.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/navigation/refresh/materialicons/24px.svg",
    "delete_all.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/action/delete/materialicons/24px.svg",
    "save.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/content/save/materialicons/24px.svg",
    "load.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/file/folder_open/materialicons/24px.svg",
    "profile.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/social/people/materialicons/24px.svg",
    "expand.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/navigation/expand_more/materialicons/24px.svg",
    "collapse.svg": "https://raw.githubusercontent.com/google/material-design-icons/master/src/navigation/expand_less/materialicons/24px.svg"
}

# Download each icon
for icon_name, url in icons.items():
    response = requests.get(url)
    if response.status_code == 200:
        icon_path = icons_dir / icon_name
        with open(icon_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded {icon_name}")
    else:
        print(f"Failed to download {icon_name}")
