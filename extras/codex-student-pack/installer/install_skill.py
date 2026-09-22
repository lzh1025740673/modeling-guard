#!/usr/bin/env python3
"""Fixed-commit, project-only installer. Standard library; no model calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

REPO = 'https://github.com/XiaoMaColtAI/math-modeling-skill.git'
COMMIT = 'abecb641491932d851a57709ed4e7ea66372281d'
SKILL_HASH = '3cbb7985e91d97ce92fd83da222e1709faa52fe6e1994b78a5b41e1620c25e41'
PACK = Path(__file__).resolve().parents[1]
SKILL = Path('.agents/skills/math-modeling')
MANIFEST = '.math_modeling_install.json'
DIRS = ('data', 'src', 'outputs', 'reports', 'configs', 'templates')
FILES = {
    'AGENTS.md': 'templates/AGENTS.md',
    'TASK_BRIEF.md': 'templates/TASK_BRIEF.md',
    'templates/HUMAN_REVIEW_TEMPLATE.md': 'templates/HUMAN_REVIEW_TEMPLATE.md',
    'templates/STAGE_REPORT_TEMPLATE.md': 'templates/STAGE_REPORT_TEMPLATE.md',
}


class InstallError(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def reject_links(path):
    for part in (path, *path.parents):
        if part.is_symlink() or (part.exists() and getattr(part.lstat(), 'st_file_attributes', 0) & 0x400):
            raise InstallError('Refusing symlink/junction/reparse point: ' + str(part))


def safe_path(root, relative):
    rel = Path(relative)
    if rel.is_absolute() or '..' in rel.parts or ':' in str(rel):
        raise InstallError('Unsafe relative path: ' + str(relative))
    path = root / rel
    reject_links(path)
    if not path.resolve().is_relative_to(root.resolve()):
        raise InstallError('Path leaves project: ' + str(relative))
    return path


def require_runtime():
    if sys.version_info < (3, 10):
        raise InstallError('Python >=3.10 required. Install it manually, then retry.')
    git = shutil.which('git')
    if not git:
        raise InstallError('Git not found. Install Git for Windows manually, reopen terminal, then retry.')
    result = subprocess.run([git, '--version'], capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise InstallError('Git cannot run: ' + result.stderr.strip())
    print('Python ' + sys.version.split()[0] + '; ' + result.stdout.strip())
    return git


def run_git(git, args, cwd, hooks):
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['GIT_LFS_SKIP_SMUDGE'] = '1'
    cmd = [git, '-c', 'core.autocrlf=false', '-c', 'core.hooksPath=' + str(hooks), *args]
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, timeout=180)
    if result.returncode:
        raise InstallError('Git failed (no files overwritten): ' + result.stderr.decode('utf-8', errors='replace').strip())
    return result.stdout


def check_conflicts(project, proposed):
    conflicts = []
    for relative, data in proposed.items():
        path = safe_path(project, relative)
        for parent in path.parents:
            if parent == project.parent:
                break
            if parent.exists() and not parent.is_dir():
                conflicts.append(relative + ' (parent is not a directory)')
                break
        if path.exists() and (not path.is_file() or path.read_bytes() != data):
            conflicts.append(relative)
    for relative in DIRS:
        path = safe_path(project, relative)
        if path.exists() and not path.is_dir():
            conflicts.append(relative + ' (required directory)')
    if conflicts:
        raise InstallError('CONFLICT: stop without overwriting. Choose a new project directory.\n' + '\n'.join(conflicts[:25]))


def verify(project):
    reject_links(project)
    manifest_path = safe_path(project, MANIFEST)
    if not manifest_path.is_file():
        raise InstallError('No successful installation manifest in target project.')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('commit') != COMMIT or manifest.get('repository') != REPO:
        raise InstallError('Version lock or repository mismatch.')
    hashes = manifest.get('immutable_sha256', {})
    if hashes.get((SKILL / 'SKILL.md').as_posix()) != SKILL_HASH or 'AGENTS.md' not in hashes:
        raise InstallError('Incomplete or changed manifest.')
    for relative, expected in hashes.items():
        path = safe_path(project, relative)
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise InstallError('VERIFY_FAILED: ' + relative)
    skill_root = project / SKILL
    extras = [p.relative_to(project).as_posix() for p in skill_root.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'
              and p.relative_to(project).as_posix() not in hashes]
    if extras:
        raise InstallError('Unexpected files in installed Skill: ' + ', '.join(extras[:10]))
    for relative in DIRS:
        if not safe_path(project, relative).is_dir():
            raise InstallError('Missing directory: ' + relative)
    if not safe_path(project, 'TASK_BRIEF.md').is_file():
        raise InstallError('Missing TASK_BRIEF.md')
    text = (skill_root / 'SKILL.md').read_text(encoding='utf-8')
    if 'name: math-modeling' not in text or 'description:' not in text:
        raise InstallError('Skill metadata missing.')
    print('FILES_VERIFIED: commit=' + COMMIT + '; immutable_files=' + str(len(hashes)))
    print('This checks files only. Reopen Codex in the project and run the short SKILL_READY prompt.')


def install(project, git):
    reject_links(project)
    if project.exists() and not project.is_dir():
        raise InstallError('Target exists and is not a directory.')
    proposed = {dest: (PACK / source).read_bytes() for dest, source in FILES.items()}
    check_conflicts(project, proposed)
    project.parent.mkdir(parents=True, exist_ok=True)
    # Only this newly owned temporary directory is automatically removed.
    with tempfile.TemporaryDirectory(prefix='.math-skill-install-', dir=project.parent) as temporary:
        staging = Path(temporary).resolve()
        if not staging.is_relative_to(project.parent.resolve()):
            raise InstallError('Temporary directory escaped intended parent.')
        hooks = staging / 'empty-hooks'
        hooks.mkdir()
        template = staging / 'empty-template'
        template.mkdir()
        source = staging / 'upstream'
        print('Fetching original GitHub repository at locked commit...')
        run_git(git, ['clone', '--no-checkout', '--template=' + str(template), '--', REPO, str(source)], staging, hooks)
        run_git(git, ['checkout', '--detach', COMMIT], source, hooks)
        actual = run_git(git, ['rev-parse', 'HEAD'], source, hooks).decode().strip()
        if actual != COMMIT or run_git(git, ['status', '--porcelain'], source, hooks).strip():
            raise InstallError('Commit mismatch or upstream worktree not clean.')
        tracked = run_git(git, ['ls-files', '-z'], source, hooks).decode('utf-8').split('\0')
        for relative in filter(None, tracked):
            root = relative.split('/')[0]
            if root not in {'SKILL.md', '使用指南.md', 'VERSION', 'README.md', 'references', 'assets', 'tools'}:
                continue
            path = safe_path(source, relative)
            if not path.is_file():
                raise InstallError('Unsupported upstream file: ' + relative)
            proposed[(SKILL / relative).as_posix()] = path.read_bytes()
        if digest(proposed[(SKILL / 'SKILL.md').as_posix()]) != SKILL_HASH:
            raise InstallError('Locked SKILL.md content hash mismatch.')
        # Upstream asks for the guide in the project; copy once without a model call.
        proposed['使用指南.md'] = proposed[(SKILL / '使用指南.md').as_posix()]
        hashes = {p: digest(data) for p, data in proposed.items() if p != 'TASK_BRIEF.md'}
        manifest = {'format': 1, 'repository': REPO, 'commit': COMMIT,
                    'distribution_mode': 'fixed-commit-installer', 'immutable_sha256': hashes}
        proposed[MANIFEST] = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')
        check_conflicts(project, proposed)
        existing_skill = project / SKILL
        if existing_skill.exists():
            unknown = [p.relative_to(project).as_posix() for p in existing_skill.rglob('*')
                       if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'
                       and p.relative_to(project).as_posix() not in proposed]
            if unknown:
                raise InstallError('CONFLICT: existing Skill has unexpected files; use a new target.')
        # Full preflight precedes writes; x mode never overwrites an existing file.
        for relative, data in proposed.items():
            path = safe_path(project, relative)
            if path.exists():
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as output:
                output.write(data)
        for relative in DIRS:
            safe_path(project, relative).mkdir(parents=True, exist_ok=True)
    verify(project)
    print('INSTALL_OK: ' + str(project))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=PACK.parent / 'math_modeling_project')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    project = args.project.absolute()
    try:
        git = require_runtime()
        if args.verify:
            verify(project)
        else:
            install(project, git)
        return 0
    except (InstallError, OSError, ValueError, subprocess.TimeoutExpired, KeyError) as exc:
        print('INSTALL_BLOCKED: ' + str(exc), file=sys.stderr)
        print('No existing file is overwritten. Fix the reported prerequisite or choose an empty target.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
