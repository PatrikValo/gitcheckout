import json
import sys

from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_output, CalledProcessError, STDOUT
from typing import List, Tuple

PLUGIN_NAME = "checkouts_cache_plugin"
CHECKOUTS_FILE = "checkouts.db"
BRANCHES_FILE = "branches.db"
CHECKOUTS_LIMIT = 10


class Cache:
    def __init__(self) -> None:
        self._path = self._get_root_config_dir()
        self._checkouts_path = self._create_checkouts_path()
        self._branches_path = self._create_branches_path()

    def _get_root_config_dir(self) -> Path:
        root = check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()
        path = Path(root) / ".git" / PLUGIN_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _create_checkouts_path(self) -> Path:
        path = self._path / CHECKOUTS_FILE
        path.touch()
        return path

    def _create_branches_path(self) -> Path:
        path = self._path / BRANCHES_FILE
        path.touch()
        return path

    def _write(self, path: Path, elems: List[str]) -> None:
        path.write_text("\n".join(elems))

    def _read(self, path: Path) -> List[str]:
        text = path.read_text()
        if text.strip() == "":
            return []
        return text.split("\n")

    def _write_checkouts(self, checkouts: List[str]) -> None:
        self._write(self._checkouts_path, checkouts)

    def _write_branches(self, branches: List[str]) -> None:
        self._write(self._branches_path, branches)

    def _read_checkouts(self) -> List[str]:
        return self._read(self._checkouts_path)

    def _read_branches(self) -> List[str]:
        return self._read(self._branches_path)

    def add_checkout(self, branch: str) -> None:
        checkouts = [b for b in self._read_checkouts() if b != branch]
        checkouts.insert(0, branch)
        self._write_checkouts(checkouts)

    def add_branch(self, name: str, description: str) -> None:
        branches = self._read_branches()
        branches.insert(0, json.dumps({"name": name, "description": description}))
        self._write_branches(branches)

    def get_checkouts(self) -> List[str]:
        return self._read_checkouts()

    def get_branches(self) -> List[Tuple[str, str]]:
        result = []
        for line in self._read_branches():
            obj = json.loads(line)
            result.append((obj["name"], obj["description"]))
        return result


def git_exists() -> bool:
    try:
        check_output(["which", "git"], stderr=STDOUT)
    except CalledProcessError:
        return False
    return True


def git_repo_exists() -> bool:
    try:
        check_output(["git", "rev-parse", "--show-toplevel"], stderr=STDOUT)
    except CalledProcessError:
        return False
    return True


def create_checkout(name: str) -> None:
    try:
        check_output(["git", "checkout", name])
        Cache().add_checkout(name)
    except CalledProcessError:
        sys.exit(1)


def create_n_checkout(n: int) -> None:
    checkouts = Cache().get_checkouts()
    if len(checkouts) <= n:
        return
    name = checkouts[n]
    try:
        check_output(["git", "checkout", name])
        Cache().add_checkout(name)
    except CalledProcessError:
        sys.exit(1)


def create_branch(name: str, description: str) -> None:
    try:
        check_output(["git", "checkout", "-b", name])
        Cache().add_branch(name, description)
        Cache().add_checkout(name)
    except CalledProcessError:
        sys.exit(1)


def print_checkouts() -> None:
    cache = Cache()
    branches = {name: description for name, description in cache.get_branches()}
    checkouts = cache.get_checkouts()[0:CHECKOUTS_LIMIT]
    if not checkouts:
        return
    print("+", "---", "+", 30 * "-", "+", 40 * "-", "+")
    print("| {:^3} | {:<30} | {:<40} |".format("n", "name", "description"))
    print("+", "---", "+", 30 * "-", "+", 40 * "-", "+")
    for i, checkout in enumerate(checkouts):
        print(
            "| {:^3} | {:<30} | {:<40} |".format(
                i, checkout[0:30], branches.get(checkout, "")[0:40]
            )
        )
    print("+", "---", "+", 30 * "-", "+", 40 * "-", "+")


def main() -> None:
    if not git_exists():
        print("git not found", file=sys.stderr)
        sys.exit(1)

    if not git_repo_exists():
        print("not in active git repo", file=sys.stderr)
        sys.exit(1)

    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("branch", nargs="?", default=None, help="checkout to branch")
    group.add_argument(
        "-b", nargs=2, metavar=("<branch>", "<desc>"), help="create a branch"
    )
    group.add_argument("-n", metavar="<number>", type=int, help="checkout to branch")
    group.add_argument("-l", "--list", action="store_true", help="list all checkouts")
    args = parser.parse_args()

    if args.branch:
        if args.branch == "-":
            create_n_checkout(1)
        else:
            create_checkout(args.branch)
    elif args.b:
        create_branch(args.b[0], args.b[1])
    elif args.n:
        create_n_checkout(args.n)
    elif args.list:
        print_checkouts()


if __name__ == "__main__":
    main()
