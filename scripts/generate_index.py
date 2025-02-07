import os
import glob
import shutil
from pathlib import Path
from github import Github

# Get token from environment variable
github_token = os.environ.get("GITHUB_TOKEN")
if not github_token:
    raise ValueError("GITHUB_TOKEN environment variable is not set")

# Initialize GitHub client
g = Github(github_token)


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>{package_name}</title>
</head>
<body>
    <h1>{package_name}</h1>
    {package_links}
</body>
</html>
"""

def normalize_package_name(name):
    return name.replace("_", "-")

def generate_package_index():
    packages_dir = Path("packages")
    dist_dir = Path("dist")
    
    # Clean and create dist directory
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(exist_ok=True)

    # Generate main index
    package_list = []
    for package_dir in packages_dir.glob("*"):
        if package_dir.is_dir():
            package_name = package_dir.name
            package_list.append(
                f'<a href="{package_name}/">{package_name}</a><br/>'
            )

    main_index = HTML_TEMPLATE.format(
        package_name="Simple Package Index",
        package_links="\n".join(package_list)
    )
    
    with open(dist_dir / "index.html", "w") as f:
        f.write(main_index)

    # Generate package-specific pages and copy package files
    for package_dir in packages_dir.glob("*"):
        if package_dir.is_dir():
            package_name = package_dir.name
            package_dist_dir = dist_dir / package_name
            package_dist_dir.mkdir(exist_ok=True)
            
            # Copy all package files
            package_files = []
            for ext in ["*.tar.gz", "*.whl"]:
                for src_file in package_dir.glob(ext):
                    dst_file = package_dist_dir / src_file.name
                    shutil.copy2(src_file, dst_file)
                    package_files.append(src_file.name)
            
            # Generate package-specific index.html
            file_links = []
            for filename in package_files:
                file_links.append(
                    f'<a href="{filename}">{filename}</a><br/>'
                )

            package_index = HTML_TEMPLATE.format(
                package_name=package_name,
                package_links="\n".join(file_links)
            )
            
            with open(package_dist_dir / "index.html", "w") as f:
                f.write(package_index)

def query_releases():
    try:
        repo = g.get_repo("marcin-krystianc/my-pypi-repo")
        
        # Get all releases
        releases = repo.get_releases()

        # Process release assets
        for release in releases:
            for asset in release.get_assets():
                print({
                    "name": asset.name,
                    "size": asset.size,
                    "download_count": asset.download_count,
                    "download_url": asset.browser_download_url,
                    "created_at": asset.created_at
                })
            
    except Exception as e:
        print(f"Error querying releases: {e}")

if __name__ == "__main__":
    query_releases()    
    generate_package_index()
