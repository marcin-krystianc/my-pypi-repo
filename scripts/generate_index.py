import os
import sys
import logging
from pathlib import Path
from github import Github
from typing import List, Dict
import itertools
import requests

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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PackageIndexBuilder:
    def __init__(self, token: str, repo_name: str, output_dir: str):
        self.github = Github(token)
        self.repo_name = repo_name
        self.output_dir = Path(output_dir)
        self.packages: Dict[str, List[Dict]] = {}
        
        # Set up authenticated session
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/octet-stream",
        })

    def collect_packages(self):

        logger.info("Collecting packages from releases...")
        repo = self.github.get_repo(self.repo_name)

        for release in repo.get_releases():
            for asset in release.get_assets():
                if asset.name.endswith(('.whl', '.tar.gz')):
                    package_name = asset.name.split('-')[0]
                    if package_name not in self.packages:
                        self.packages[package_name] = []

                    self.packages[package_name].append({
                        'filename': asset.name,
                        'url': asset.url,
                        'size': asset.size,
                        'upload_time': asset.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    })

    def generate_index_html(self):
        # Generate main index
        package_list = self.packages.keys()
        main_index = HTML_TEMPLATE.format(
            package_name="Simple Package Index",
            package_links="\n".join([f'<a href="{x}/">{x}</a><br/>' for x in package_list])
        )

        with open(self.output_dir / "index.html", "w") as f:
            f.write(main_index)
 
        for package, assets in self.packages.items():

            package_dir = self.output_dir / package
            package_dir.mkdir(exist_ok=True)

            # Generate package-specific index.html
            file_links = []
            assets = sorted(assets, key=lambda x: x["filename"])
            for filename, items in itertools.groupby(assets, key=lambda x: x["filename"]):
                url = next(items)['url']
                file_links.append(f'<a href="{url}">{filename}</a><br/>')

            package_index = HTML_TEMPLATE.format(
                package_name=package,
                package_links="\n".join(file_links)
            )

            with open(package_dir / "index.html", "w") as f:
                f.write(package_index)

    def build(self):
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Collect and generate
        self.collect_packages()
        self.generate_index_html()

        logger.info(f"Package index built successfully in {self.output_dir}")


def main():
    # Get environment variables
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    print (repo)
    output_dir = os.environ.get("OUTPUT_DIR", "dist")
    
    if not all([token, repo]):
        logger.error("Missing required environment variables")
        sys.exit(1)

    builder = PackageIndexBuilder(token, repo, output_dir)
    builder.build()

if __name__ == "__main__":
    main()
