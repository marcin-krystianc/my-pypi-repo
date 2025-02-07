import os
import sys
import logging
from pathlib import Path
from github import Github
from typing import List, Dict
import itertools

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
                        'url': asset.browser_download_url,
                        'size': asset.size,
                        'upload_time': asset.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    })

    def generate_index_html(self):
        # Generate main index
        package_list = self.packages.keys()
        main_index = HTML_TEMPLATE.format(
            package_name="Simple Package Index",
            package_links="\n".join(package_list)
        )

        with open(self.output_dir / "index.html", "w") as f:
            f.write(main_index)
 
        for package, assets in self.packages.items():

            # Generate package-specific index.html
            file_links = []
            assets = sorted(assets, key=lambda x: x["filename"])
            for filename, items in itertools.groupby(assets, key=lambda x: x["filename"]):
                file_links.append(next(items)['url'])

            package_index = HTML_TEMPLATE.format(
                package_name=package,
                package_links="\n".join(file_links)
            )

            package_dist_dir = self.output_dir / package
            package_dist_dir.mkdir(exist_ok=True)
            with open(package_dist_dir / "index.html", "w") as f:
                f.write(package_index)

    def build(self):
        """Main build process"""
        try:
            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Collect and generate
            self.collect_packages()
            self.generate_index_html()

            logger.info(f"Package index built successfully in {self.output_dir}")

        except Exception as e:
            logger.error(f"Error building package index: {e}")
            raise

def main():
    # Get environment variables
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    print (repo)
    output_dir = os.environ.get("OUTPUT_DIR", "dist")
    
    if not all([token, repo]):
        logger.error("Missing required environment variables")
        sys.exit(1)

    try:
        builder = PackageIndexBuilder(token, repo, output_dir)
        builder.build()
    except Exception as e:
        logger.error(f"Failed to build package index: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
