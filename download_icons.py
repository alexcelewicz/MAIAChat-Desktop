import os
import requests
from pathlib import Path

# Create icons directory if it doesn't exist
icons_dir = Path("icons")
icons_dir.mkdir(exist_ok=True)

# Dictionary of icon names and their URLs (using free icons from feathericons.com)
icons = {
    "file.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/file.svg",
    "database.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/database.svg",
    "send.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/send.svg",
    "chat.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/message-circle.svg",
    "stop.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/square.svg",
    "clear.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/trash-2.svg",
    "pdf.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/file-text.svg",
    "refresh.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/refresh-cw.svg",
    "delete_all.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/trash.svg",
    "save.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/save.svg",
    "load.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/folder.svg",
    "profile.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/users.svg",
    "expand.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/chevron-down.svg",
    "collapse.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/chevron-up.svg"
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
