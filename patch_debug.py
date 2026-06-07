# This script will modify downloader.py to dump debug info to a file!
import os

with open('src/core/downloader.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the download_image block
target = """            if is_scrambled:
                headers["Origin"] = "https://comix.to"
            elif "wowpic" in clean_url and "Origin" in headers:
                del headers["Origin"]

            response = requests.get(clean_url, headers=headers, timeout=30, stream=True)"""

replacement = """            if is_scrambled:
                headers["Origin"] = "https://comix.to"
            elif "wowpic" in clean_url and "Origin" in headers:
                del headers["Origin"]

            # DEBUG LOG
            with open("debug_download.txt", "a") as f:
                f.write(f"Image {index}: url={url}, clean={clean_url}, is_scrambled={is_scrambled}\\n")
                f.write(f"Headers sent: {headers}\\n")

            response = requests.get(clean_url, headers=headers, timeout=30, stream=True)
            
            with open("debug_download.txt", "a") as f:
                f.write(f"Image {index} response headers: {dict(response.headers)}\\n")
"""

if target in code:
    code = code.replace(target, replacement)
    with open('src/core/downloader.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Patched downloader.py")
else:
    print("Could not find target in downloader.py")
