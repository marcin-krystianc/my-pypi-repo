import os
import sys
import logging
from pathlib import Path
from github import Github
from typing import List, Dict
import shutil
import html

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
        """Collect all wheel and tar.gz files from releases"""
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
        """Generate the main index.html file"""
        logger.info("Generating index.html...")
        
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Python Package Index</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2em; }
        .package { margin-bottom: 1em; padding: 1em; border: 1px solid #ddd; }
        .package h2 { margin-top: 0; }
        .file { margin-left: 2em; }
    </style>
</head>
<body>
    <h1>Python Package Index</h1>
"""

        for package_name, files in sorted(self.packages.items()):
            html_content += f'<div class="package">\n'
            html_content += f'    <h2>{html.escape(package_name)}</h2>\n'
            
            for file_info in files:
                html_content += f'    <div class="file">\n'
                html_content += f'        <a href="{file_info["url"]}">{html.escape(file_info["filename"])}</a>\n'
                html_content += f'        ({file_info["size"]} bytes, uploaded {file_info["upload_time"]})\n'
                html_content += f'    </div>\n'
            
            html_content += '</div>\n'

        html_content += """
</body>
</html>
"""

        index_path = self.output_dir / 'index.html'
        index_path.write_text(html_content)

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
