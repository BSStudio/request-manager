import json
import re
import sys

import yaml

CONFIG = ".pre-commit-config.yaml"
ESLINT_REPO = "https://github.com/pre-commit/mirrors-eslint"
# What eslint.config.cjs loads. The hook's isolated environment cannot give
# ESLint the app's types anyway, so other packages would only slow it down.
DEPENDENCIES_TO_SYNC = [
    "@eslint/js",
    "@tanstack/eslint-plugin-query",
    "eslint",
    "eslint-config-prettier",
    "eslint-import-resolver-typescript",
    "eslint-plugin-import-x",
    "eslint-plugin-prettier",
    "eslint-plugin-react",
    "eslint-plugin-react-hooks",
    "globals",
    "prettier",
    "typescript",
    "typescript-eslint",
]


def main():
    with open(CONFIG, newline="") as f:
        text = f.read()

    repo = next(r for r in yaml.safe_load(text)["repos"] if r["repo"] == ESLINT_REPO)
    hook = repo["hooks"][0]
    folder = hook["files"].strip("^/")
    with open(f"{folder}/package.json") as f:
        dev_dependencies = json.load(f)["devDependencies"]

    expected = sorted(
        f"{name}@{dev_dependencies[name]}"
        for name in DEPENDENCIES_TO_SYNC
        if name in dev_dependencies
    )
    current = sorted(hook.get("additional_dependencies", []))
    if current == expected:
        return 0

    # Only the list is rewritten, so the rest of the file keeps its comments.
    newline = "\r\n" if "\r\n" in text else "\n"
    match = re.compile(
        r"^( *)additional_dependencies:\r?\n((?:\1  - .*\r?\n)+)", re.MULTILINE
    ).search(text, text.index(ESLINT_REPO))
    indent = match.group(1) + "  "
    items = "".join(
        (
            f"{indent}- '{dependency}'{newline}"
            if dependency.startswith("@")
            else f"{indent}- {dependency}{newline}"
        )
        for dependency in expected
    )
    with open(CONFIG, "w", newline="") as f:
        f.write(text[: match.start(2)] + items + text[match.end(2) :])

    print(
        f"Synced the ESLint hook's additional_dependencies with {folder}/package.json"
    )
    print("Removed:", set(current) - set(expected))
    print("Added:", set(expected) - set(current))
    return 1


if __name__ == "__main__":
    sys.exit(main())
