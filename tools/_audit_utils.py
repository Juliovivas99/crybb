"""
Audit utilities for repo analysis.
AST parsing, import graph, env scanning, and file analysis helpers.
"""
import ast
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional


def get_file_hash(filepath: Path) -> str:
    """Get SHA256 hash of file content."""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return ""


def parse_python_imports(filepath: Path) -> Tuple[List[str], List[str], List[str]]:
    """Parse Python file for imports. Returns (imports, from_imports, local_imports)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(filepath))
        
        imports = []
        from_imports = []
        local_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    from_imports.append(node.module)
                    # Check if it's a local import
                    if node.level > 0 or (node.module and not node.module.startswith('.')):
                        # Check if it's likely local by checking if it exists in src/
                        if node.module.startswith('src.') or '.' in node.module:
                            local_imports.append(node.module)
        
        return imports, from_imports, local_imports
    except Exception:
        return [], [], []


def extract_env_vars_from_file(filepath: Path) -> Set[str]:
    """Extract environment variable names from Python file."""
    env_vars = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for os.getenv() calls
        pattern = r'os\.getenv\(["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)
        env_vars.update(matches)
        
        # Look for os.environ.get() calls
        pattern = r'os\.environ\.get\(["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)
        env_vars.update(matches)
        
        # Look for os.environ[...] access
        pattern = r'os\.environ\[["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)
        env_vars.update(matches)
        
    except Exception:
        pass
    
    return env_vars


def parse_requirements(filepath: Path) -> Dict[str, str]:
    """Parse requirements.txt into package -> version mapping."""
    requirements = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '==' in line:
                        pkg, version = line.split('==', 1)
                        requirements[pkg.strip()] = version.strip()
                    else:
                        requirements[line] = ""
    except Exception:
        pass
    return requirements


def parse_makefile_targets(filepath: Path) -> List[str]:
    """Parse Makefile for targets."""
    targets = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and ':' in line and not line.startswith('\t'):
                    target = line.split(':')[0].strip()
                    if target:
                        targets.append(target)
    except Exception:
        pass
    return targets


def parse_dockerfile(filepath: Path) -> Dict[str, Any]:
    """Parse Dockerfile for analysis."""
    docker_info = {
        'copy_paths': [],
        'cmd': [],
        'entrypoint': [],
        'workdir': None,
        'expose': []
    }
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip().upper()
                if line.startswith('COPY '):
                    # Extract source paths from COPY
                    parts = line.split()
                    if len(parts) >= 3:
                        src = parts[1]
                        docker_info['copy_paths'].append(src)
                elif line.startswith('CMD '):
                    docker_info['cmd'] = line[4:].split()
                elif line.startswith('ENTRYPOINT '):
                    docker_info['entrypoint'] = line[11:].split()
                elif line.startswith('WORKDIR '):
                    docker_info['workdir'] = line[8:]
                elif line.startswith('EXPOSE '):
                    docker_info['expose'].extend(line[7:].split())
    except Exception:
        pass
    
    return docker_info


def get_file_purpose(filepath: Path, content: str = None) -> str:
    """Infer file purpose from path and content."""
    if content is None:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            content = ""
    
    path_str = str(filepath)
    
    # Check for docstring or top comment
    lines = content.split('\n')[:10]
    docstring = ""
    for line in lines:
        if '"""' in line or "'''" in line:
            docstring = line.strip()
            break
        elif line.strip().startswith('#'):
            docstring = line.strip()
            break
    
    # Heuristics based on path
    if 'src/ai/' in path_str:
        return "AI pipeline module"
    elif 'src/pipeline/' in path_str:
        return "Image processing orchestration"
    elif 'src/twitter_' in path_str:
        return "Twitter/X API client"
    elif 'src/server.py' in path_str:
        return "Health/metrics server"
    elif 'tools/' in path_str:
        return "Development tool/diagnostics"
    elif 'tests/' in path_str:
        return "Test module"
    elif 'assets/' in path_str:
        return "Asset file"
    elif 'fixtures/' in path_str:
        return "Test fixture"
    elif filepath.name == 'main.py':
        return "Main application entry point"
    elif filepath.name == 'config.py':
        return "Configuration management"
    elif filepath.name == 'requirements.txt':
        return "Python dependencies"
    elif filepath.name == 'Dockerfile':
        return "Docker container definition"
    elif filepath.name == 'Makefile':
        return "Build automation"
    elif filepath.name == 'README.md':
        return "Project documentation"
    elif filepath.suffix == '.md':
        return "Documentation"
    elif filepath.suffix == '.json':
        return "JSON data/config"
    elif filepath.suffix in ['.jpg', '.jpeg', '.png', '.gif']:
        return "Image asset"
    else:
        return docstring or "Unknown purpose"


def get_file_role(filepath: Path) -> str:
    """Determine file role: runtime, dev-tool, test, asset, docs."""
    path_str = str(filepath)
    
    if 'src/' in path_str and filepath.suffix == '.py':
        return "runtime"
    elif 'tools/' in path_str:
        return "dev-tool"
    elif 'tests/' in path_str:
        return "test"
    elif 'assets/' in path_str or 'fixtures/' in path_str:
        return "asset"
    elif filepath.suffix == '.md':
        return "docs"
    elif filepath.name in ['requirements.txt', 'Dockerfile', 'Makefile', '.env.example']:
        return "config"
    else:
        return "unknown"


def is_entrypoint(filepath: Path, makefile_targets: List[str] = None) -> bool:
    """Check if file is an entrypoint."""
    if makefile_targets is None:
        makefile_targets = []
    
    # Check if it's main.py
    if filepath.name == 'main.py' and 'src/' in str(filepath):
        return True
    
    # Check for __main__ guard
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'if __name__ == "__main__":' in content:
            return True
    except Exception:
        pass
    
    # Check if referenced in Makefile
    file_str = str(filepath)
    for target in makefile_targets:
        if filepath.name in target or file_str in target:
            return True
    
    return False


def find_duplicate_files(file_infos: List[Dict]) -> Dict[str, List[str]]:
    """Find files with identical content (by hash)."""
    hash_to_files = {}
    for info in file_infos:
        if info.get('hash'):
            hash_val = info['hash']
            if hash_val not in hash_to_files:
                hash_to_files[hash_val] = []
            hash_to_files[hash_val].append(info['path'])
    
    return {h: files for h, files in hash_to_files.items() if len(files) > 1}


def build_import_graph(file_infos: List[Dict]) -> Dict[str, Set[str]]:
    """Build import dependency graph."""
    graph = {}
    
    for info in file_infos:
        if info.get('type') == 'py' and info.get('imports'):
            module_name = info['path'].replace('/', '.').replace('\\', '.')
            if module_name.endswith('.py'):
                module_name = module_name[:-3]
            
            dependencies = set()
            for imp in info['imports']:
                # Convert relative imports to absolute
                if imp.startswith('.'):
                    # This is a relative import, skip for now
                    continue
                dependencies.add(imp)
            
            graph[module_name] = dependencies
    
    return graph


def find_unused_modules(graph: Dict[str, Set[str]], entrypoints: Set[str]) -> Set[str]:
    """Find modules that are never imported."""
    all_modules = set(graph.keys())
    imported_modules = set()
    
    for deps in graph.values():
        imported_modules.update(deps)
    
    # Add entrypoints as "used"
    imported_modules.update(entrypoints)
    
    return all_modules - imported_modules
