#!/usr/bin/env python3
"""
Repository audit tool for CryBB project.
Analyzes project structure, dependencies, imports, and provides lean-down recommendations.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

# Add tools directory to path
tools_dir = Path(__file__).parent
sys.path.insert(0, str(tools_dir))

from _audit_utils import (
    build_import_graph,
    extract_env_vars_from_file,
    find_duplicate_files,
    find_unused_modules,
    get_file_hash,
    get_file_purpose,
    get_file_role,
    is_entrypoint,
    parse_dockerfile,
    parse_makefile_targets,
    parse_python_imports,
    parse_requirements,
)


class RepoAuditor:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.reports_dir = repo_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # Ignore patterns
        self.ignore_patterns = {
            '.git', '.venv', '__pycache__', 'reports', 'outbox', '.data',
            'fixtures/images', 'node_modules', '.pytest_cache', '.mypy_cache'
        }
        
        self.file_infos = []
        self.import_graph = {}
        self.requirements = {}
        self.env_vars = set()
        self.makefile_targets = []
        self.docker_info = {}
        
    def scan_repo(self):
        """Scan the entire repository."""
        print("Scanning repository...")
        
        # Parse key files first
        self._parse_key_files()
        
        # Walk directory tree
        for root, dirs, files in os.walk(self.repo_root):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_patterns]
            
            for file in files:
                filepath = Path(root) / file
                if self._should_ignore_file(filepath):
                    continue
                
                self._analyze_file(filepath)
        
        # Post-process analysis
        self._build_graphs()
        self._find_issues()
        
    def _should_ignore_file(self, filepath: Path) -> bool:
        """Check if file should be ignored."""
        # Check ignore patterns
        for pattern in self.ignore_patterns:
            if pattern in str(filepath):
                return True
        
        # Check file extensions
        ignore_extensions = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe'}
        if filepath.suffix.lower() in ignore_extensions:
            return True
        
        return False
    
    def _parse_key_files(self):
        """Parse key configuration files."""
        # Requirements
        req_file = self.repo_root / "requirements.txt"
        if req_file.exists():
            self.requirements = parse_requirements(req_file)
        
        # Makefile
        makefile = self.repo_root / "Makefile"
        if makefile.exists():
            self.makefile_targets = parse_makefile_targets(makefile)
        
        # Dockerfile
        dockerfile = self.repo_root / "Dockerfile"
        if dockerfile.exists():
            self.docker_info = parse_dockerfile(dockerfile)
        
        # Environment variables from config
        config_file = self.repo_root / "src" / "config.py"
        if config_file.exists():
            self.env_vars = extract_env_vars_from_file(config_file)
        
        # .env.example
        env_example = self.repo_root / ".env.example"
        if env_example.exists():
            env_vars_from_example = extract_env_vars_from_file(env_example)
            self.env_vars.update(env_vars_from_example)
    
    def _analyze_file(self, filepath: Path):
        """Analyze a single file."""
        try:
            stat = filepath.stat()
            size_kb = stat.st_size / 1024
            modified_time = stat.st_mtime
            
            # Get file type
            file_type = filepath.suffix[1:] if filepath.suffix else 'unknown'
            
            # Get purpose and role
            purpose = get_file_purpose(filepath)
            role = get_file_role(filepath)
            
            # Get hash for duplicate detection
            file_hash = get_file_hash(filepath) if size_kb < 10 * 1024 else ""  # Skip large files
            
            # Parse Python imports
            imports = []
            if file_type == 'py':
                imports, from_imports, local_imports = parse_python_imports(filepath)
                imports.extend(from_imports)
            
            # Check if entrypoint
            is_entry = is_entrypoint(filepath, self.makefile_targets)
            
            # Check if large asset
            is_large = size_kb > 1024  # > 1MB
            
            file_info = {
                'path': str(filepath.relative_to(self.repo_root)),
                'size_kb': round(size_kb, 2),
                'modified_time': modified_time,
                'type': file_type,
                'purpose': purpose,
                'role': role,
                'hash': file_hash,
                'imports': imports,
                'is_entrypoint': is_entry,
                'is_large_asset': is_large,
                'is_dead': False,  # Will be determined later
                'is_duplicate': False,  # Will be determined later
            }
            
            self.file_infos.append(file_info)
            
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
    
    def _build_graphs(self):
        """Build dependency graphs and find issues."""
        # Build import graph
        self.import_graph = build_import_graph(self.file_infos)
        
        # Find entrypoints
        entrypoints = {info['path'] for info in self.file_infos if info['is_entrypoint']}
        
        # Find unused modules
        unused_modules = find_unused_modules(self.import_graph, entrypoints)
        
        # Mark dead files
        for info in self.file_infos:
            if info['type'] == 'py':
                module_path = info['path'].replace('/', '.').replace('\\', '.')
                if module_path.endswith('.py'):
                    module_path = module_path[:-3]
                
                if module_path in unused_modules and not info['is_entrypoint']:
                    info['is_dead'] = True
        
        # Find duplicates
        duplicates = find_duplicate_files(self.file_infos)
        for hash_val, files in duplicates.items():
            for file_info in self.file_infos:
                if file_info['path'] in files:
                    file_info['is_duplicate'] = True
    
    def _find_issues(self):
        """Find various issues and opportunities for cleanup."""
        # This will be expanded with more analysis
        pass
    
    def generate_reports(self, write_min_files: bool = False):
        """Generate Markdown and JSON reports."""
        print("Generating reports...")
        
        # Generate JSON report
        json_data = self._generate_json_report()
        json_path = self.reports_dir / "repo_inventory.json"
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        # Generate Markdown report
        md_content = self._generate_markdown_report()
        md_path = self.reports_dir / "repo_inventory.md"
        with open(md_path, 'w') as f:
            f.write(md_content)
        
        # Write minimal files if requested
        if write_min_files:
            self._write_minimal_files()
        
        print(f"Reports generated:")
        print(f"  - {json_path}")
        print(f"  - {md_path}")
    
    def _generate_json_report(self) -> Dict[str, Any]:
        """Generate structured JSON report."""
        return {
            'timestamp': str(Path().cwd()),
            'project_overview': self._get_project_overview(),
            'files': self.file_infos,
            'import_graph': {k: list(v) for k, v in self.import_graph.items()},
            'requirements': self.requirements,
            'environment_variables': list(self.env_vars),
            'makefile_targets': self.makefile_targets,
            'docker_info': self.docker_info,
            'analysis': self._get_analysis_summary(),
            'recommendations': self._get_recommendations()
        }
    
    def _generate_markdown_report(self) -> str:
        """Generate human-readable Markdown report."""
        content = []
        
        # Header
        content.append("# Repository Inventory & Lean-Down Plan")
        content.append("")
        content.append(f"Generated: {Path().cwd()}")
        content.append("")
        
        # Project Overview
        content.append("## Project Overview")
        overview = self._get_project_overview()
        content.append(f"- **Python Version**: {overview.get('python_version', 'Unknown')}")
        content.append(f"- **Package Layout**: {overview.get('package_layout', 'Unknown')}")
        content.append(f"- **Runtime Modes**: {', '.join(overview.get('runtime_modes', []))}")
        content.append(f"- **Image Pipeline**: {overview.get('image_pipeline', 'Unknown')}")
        content.append("")
        
        # File Inventory
        content.append("## File Inventory")
        content.append("")
        content.append("| Path | Size (KB) | Type | Purpose | Role | Flags |")
        content.append("|------|-----------|------|---------|------|-------|")
        
        for info in sorted(self.file_infos, key=lambda x: x['path']):
            flags = []
            if info['is_dead']:
                flags.append("DEAD")
            if info['is_duplicate']:
                flags.append("DUPLICATE")
            if info['is_large_asset']:
                flags.append("LARGE")
            if info['is_entrypoint']:
                flags.append("ENTRYPOINT")
            
            flags_str = ", ".join(flags) if flags else "-"
            
            content.append(f"| {info['path']} | {info['size_kb']} | {info['type']} | {info['purpose']} | {info['role']} | {flags_str} |")
        
        content.append("")
        
        # Dependencies Analysis
        content.append("## Dependencies Analysis")
        content.append("")
        
        # Find unused dependencies
        used_packages = set()
        for info in self.file_infos:
            if info['type'] == 'py':
                for imp in info['imports']:
                    # Extract package name
                    pkg = imp.split('.')[0]
                    used_packages.add(pkg)
        
        unused_deps = set(self.requirements.keys()) - used_packages
        if unused_deps:
            content.append("### Unused Dependencies")
            content.append("")
            for dep in sorted(unused_deps):
                content.append(f"- {dep}")
            content.append("")
        
        # Environment Variables
        content.append("## Environment Variables")
        content.append("")
        content.append("### Used Variables")
        for var in sorted(self.env_vars):
            content.append(f"- {var}")
        content.append("")
        
        # Lean-Down Proposal
        content.append("## Lean-Down Proposal")
        content.append("")
        content.append("| Action | Path | Reason |")
        content.append("|--------|------|--------|")
        
        recommendations = self._get_recommendations()
        for rec in recommendations:
            content.append(f"| {rec['action']} | {rec['path']} | {rec['reason']} |")
        
        content.append("")
        
        # Next Actions
        content.append("## Next Actions")
        content.append("")
        content.append("### Commands to Execute")
        content.append("")
        
        for rec in recommendations:
            if rec['action'] == 'Remove':
                content.append(f"```bash")
                content.append(f"git rm {rec['path']}")
                content.append(f"```")
                content.append("")
        
        return "\n".join(content)
    
    def _get_project_overview(self) -> Dict[str, Any]:
        """Get project overview information."""
        return {
            'python_version': '3.8+',  # Could detect from code
            'package_layout': 'src/ + tools/ + tests/',
            'runtime_modes': ['mock', 'dryrun', 'live'],
            'image_pipeline': 'ai (with placeholder fallback)',
            'has_dockerfile': (self.repo_root / "Dockerfile").exists(),
            'has_makefile': (self.repo_root / "Makefile").exists(),
        }
    
    def _get_analysis_summary(self) -> Dict[str, Any]:
        """Get analysis summary."""
        total_files = len(self.file_infos)
        dead_files = sum(1 for f in self.file_infos if f['is_dead'])
        duplicate_files = sum(1 for f in self.file_infos if f['is_duplicate'])
        large_files = sum(1 for f in self.file_infos if f['is_large_asset'])
        
        return {
            'total_files': total_files,
            'dead_files': dead_files,
            'duplicate_files': duplicate_files,
            'large_files': large_files,
            'total_size_kb': sum(f['size_kb'] for f in self.file_infos),
        }
    
    def _get_recommendations(self) -> List[Dict[str, str]]:
        """Get lean-down recommendations."""
        recommendations = []
        
        for info in self.file_infos:
            if info['is_dead'] and info['role'] != 'config':
                recommendations.append({
                    'action': 'Remove',
                    'path': info['path'],
                    'reason': 'Unused module - no imports or entrypoint'
                })
            elif info['is_duplicate']:
                recommendations.append({
                    'action': 'Remove',
                    'path': info['path'],
                    'reason': 'Duplicate file - identical content exists'
                })
            elif info['is_large_asset'] and info['role'] == 'asset':
                recommendations.append({
                    'action': 'Defer',
                    'path': info['path'],
                    'reason': 'Large asset - consider external hosting'
                })
        
        return recommendations
    
    def _write_minimal_files(self):
        """Write minimal configuration files."""
        print("Writing minimal files...")
        
        # Write requirements.min.txt
        used_packages = set()
        for info in self.file_infos:
            if info['type'] == 'py':
                for imp in info['imports']:
                    pkg = imp.split('.')[0]
                    used_packages.add(pkg)
        
        min_requirements = {pkg: ver for pkg, ver in self.requirements.items() if pkg in used_packages}
        
        req_min_path = self.repo_root / "requirements.min.txt"
        with open(req_min_path, 'w') as f:
            for pkg, ver in sorted(min_requirements.items()):
                if ver:
                    f.write(f"{pkg}=={ver}\n")
                else:
                    f.write(f"{pkg}\n")
        
        # Write .env.example.min
        env_min_path = self.repo_root / ".env.example.min"
        with open(env_min_path, 'w') as f:
            for var in sorted(self.env_vars):
                f.write(f"{var}=\n")
        
        # Write .dockerignore.suggested
        dockerignore_path = self.repo_root / ".dockerignore.suggested"
        with open(dockerignore_path, 'w') as f:
            f.write("# Suggested .dockerignore\n")
            f.write("tests/\n")
            f.write("reports/\n")
            f.write("fixtures/images/\n")
            f.write("outbox/\n")
            f.write(".data/\n")
            f.write("*.md\n")
            f.write(".git/\n")
            f.write(".venv/\n")
            f.write("__pycache__/\n")
        
        print(f"Minimal files written:")
        print(f"  - {req_min_path}")
        print(f"  - {env_min_path}")
        print(f"  - {dockerignore_path}")


def main():
    parser = argparse.ArgumentParser(description="Repository audit tool")
    parser.add_argument("--write-min-files", action="store_true", 
                       help="Write minimal configuration files")
    
    args = parser.parse_args()
    
    repo_root = Path.cwd()
    auditor = RepoAuditor(repo_root)
    
    try:
        auditor.scan_repo()
        auditor.generate_reports(write_min_files=args.write_min_files)
        print("Audit completed successfully!")
    except Exception as e:
        print(f"Audit failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
