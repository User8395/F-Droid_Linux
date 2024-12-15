from tqdm import tqdm
import requests
import os
import sys
import json

# F-Droid Index URL (do not include the index filename)
index_url = "https://f-droid.org/repo/"


if len(sys.argv) == 1:
    print("usage: fdroid.py <command>")
    print("missing argument: <command>")
    exit(1)

command = sys.argv[1]

class FDroidLinux:
    index = {}

    def __init__(self):
        # Check if Waydroid is installed and initalized
        if os.popen("waydroid status").read() == "ERROR: WayDroid is not initialized, run \"waydroid init\"":
            print("Waydroid needs to be installed and initalized")
            exit(1)

        # Check if the Waydroid session is running
        if "RUNNING" not in os.popen("waydroid status").read():
            print("Waydroid is not running")
            exit(1)

        # If the index hasn't been downloaded, download it
        if not os.path.isfile("index.json"):
            self.update()
        
        self.index = json.loads(open("index.json", "r").read())
            

    def update(self):
        with requests.get(index_url + "index-v2.json", stream=True) as r:
            with open("index.json", "wb") as f, tqdm(total=len(r.content), unit='iB', unit_scale=True, desc="Downloading F-Droid index") as progress:
                for chunk in r.iter_content():
                    size = f.write(chunk)
                    progress.update(size)
                    

        self.index = json.loads(open("index.json", "r").read())
    
    def search(self, packages):
        if packages == 0:
            print("usage: fdroid.py search <search_term>")
            print("missing argument: <search_term>")
            exit(1)

        for term in packages:
            for package in self.index["packages"]:
                if term in package:
                    metadata = self.index["packages"][package]["metadata"]
                    print(metadata["name"]["en-US"] + " (" + '\033[1m' + package + '\033[0m' + "): " + metadata["summary"]["en-US"])
                else:
                    pass
    
    def install(self, packages):
        if len(packages) == 0:
            print("usage: fdroid.py install <packages>")
            print("missing argument: <packages>")
            exit(1)

        needtoexit = False

        for package in packages:
            if package not in self.index["packages"]:
                print("Target not found: " + package)
                del package
                needtoexit = True

        if needtoexit:
            exit(1)

        print("Summary:")
        print()
        print("To install:")
        for package in packages:
            print(package)

        print()
        installnow = input("Continue? [Y/n]: ")
        if installnow.casefold() == "n":
            exit(0)
        else:
            # Clear temp folder
            try:
                for file in os.listdir("temp"):
                    os.remove(file)
                os.rmdir("temp")
            except FileNotFoundError:
                pass
            try: 
                os.mkdir("temp")
            except FileExistsError:
                pass

            filename = ""

            # Download files
            for i, package in enumerate(packages):
                lastUpdated = self.index["packages"][package]["metadata"]["lastUpdated"]
                for version in self.index["packages"][package]["versions"]:
                    if self.index["packages"][package]["versions"][version]["added"] == lastUpdated:
                        filename = self.index["packages"][package]["versions"][version]["file"]["name"].split("/")[-1]
                        with requests.get("https://f-droid.org/repo/" + filename, stream=True) as r:
                            with open("temp/" + filename, "wb") as f, tqdm(total=len(r.content), unit='iB', unit_scale=True, desc=f"Downloading {filename} ({i + 1}/{len(packages)})") as progress:
                                for chunk in r.iter_content():
                                    size = f.write(chunk)
                                    progress.update(size)
            # Install to Waydroid
            for i, apk in enumerate(os.listdir("temp")):
                print("Installing " + apk + f" ({i + 1}/{len(os.listdir("temp"))})")
                os.system("waydroid app install temp/" + apk)
            
                        

fdroidlinux = FDroidLinux()

if command == "update":
    fdroidlinux.update()

# Search for an app
if command == "search":
    fdroidlinux.search(sys.argv[2:])

# Install an app
if command == "install":
    fdroidlinux.install(sys.argv[2:])