import json
import sys

from argparse import ArgumentParser, Namespace
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

    def remove_checkout(self, branch: str) -> None:
        checkouts = [b for b in self._read_checkouts() if b != branch]
        self._write_checkouts(checkouts)

    def add_branch(self, name: str, description: str) -> None:
        branches = self._read_branches()
        branches.insert(0, json.dumps({"name": name, "description": description}))
        self._write_branches(branches)

    def change_description_of_branch(self, name: str, description: str) -> None:
        branches = [
            json.dumps({"name": b, "description": d})
            for b, d in self.get_branches()
            if b != name
        ]
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


class CheckoutManager:
    def __init__(self) -> None:
        self._cache = Cache()

    def _get_checkout(self, n: int) -> str:
        checkouts = self._cache.get_checkouts()
        assert len(checkouts) > n, f"requested {n} checkout doesn't exist"
        return checkouts[n]

    def _create_time_based_checkout(self, n: int) -> None:
        name = self._get_checkout(n)
        try:
            check_output(["git", "checkout", name])
            self._cache.add_checkout(name)
        except CalledProcessError:
            sys.exit(1)

    def _create_name_based_checkout(self, name: str) -> None:
        if name == "-":
            return self._create_time_based_checkout(1)

        try:
            check_output(["git", "checkout", name])
            self._cache.add_checkout(name)
        except CalledProcessError:
            sys.exit(1)

    def _remove_checkout(self, n: int) -> None:
        checkouts = self._cache.get_checkouts()
        assert len(checkouts) > n, f"requested {n} checkout doesn't exist"
        branch = checkouts[n]
        if n == 0:
            assert len(checkouts) > 1, "we can't delete single checkout"
            self._create_time_based_checkout(1)
        self._cache.remove_checkout(branch)

    def _create_branch(self, name: str, description: str) -> None:
        try:
            check_output(["git", "checkout", "-b", name])
            self._cache.add_branch(name, description)
            self._cache.add_checkout(name)
        except CalledProcessError:
            sys.exit(1)

    def _change_description(self, n: int, description: str) -> None:
        name = self._get_checkout(n)
        self._cache.change_description_of_branch(name, description)

    def _print_checkouts(self) -> None:
        branches = {
            name: description for name, description in self._cache.get_branches()
        }
        checkouts = self._cache.get_checkouts()[0:CHECKOUTS_LIMIT]
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

    def run(self, args: Namespace) -> None:
        if args.branch is not None:
            self._create_name_based_checkout(args.branch)
        elif args.b:
            self._create_branch(args.b[0], args.b[1])
        elif args.n is not None:
            self._create_time_based_checkout(args.n)
        elif args.d is not None:
            self._remove_checkout(args.d)
            self._print_checkouts()
        elif args.c:
            self._change_description(int(args.c[0]), args.c[1])
            self._print_checkouts()
        elif args.list:
            self._print_checkouts()


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
    group.add_argument("-d", metavar="<number>", type=int, help="delete the checkout")
    group.add_argument(
        "-c",
        nargs=2,
        metavar=("<number>", "<desc>"),
        help="change the description of the branch",
    )
    group.add_argument("-l", "--list", action="store_true", help="list all checkouts")
    args = parser.parse_args()

    CheckoutManager().run(args)


if __name__ == "__main__":
    main()
