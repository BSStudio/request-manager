import json

import yaml
from yaml.dumper import SafeDumper
from yaml.loader import SafeLoader
from yaml.nodes import ScalarNode

DEPENDENCIES_TO_IGNORE = [
    "@openapitools/openapi-generator-cli",
    "@tailwindcss/vite",
    "@tanstack/react-query-devtools",
    "@types/node",
    "@types/react",
    "@types/react-dom",
    "@vite-pwa/assets-generator",
    "@vitejs/plugin-basic-ssl",
    "@vitejs/plugin-react",
    "autoprefixer",
    "cssnano",
    "source-map-explorer",
    "postcss",
    "tailwindcss",
    "vite",
    "vite-plugin-pwa",
    "workbox-window",
]
REPOS_TO_CHECK = ["eslint"]


class Dumper(SafeDumper):
    def increase_indent(self, flow=False, *args, **kwargs):
        # Have indentation just like the existing
        return super().increase_indent(flow=flow, indentless=False)

    def serialize_node(self, node, parent, index):
        # Have the args as json like formatted array and string between ' symbols
        if isinstance(index, ScalarNode) and index.value in [
            "args",
            "autoupdate_branch",
            "name",
        ]:
            node.style = "'"
            node.flow_style = True
        return super().serialize_node(node=node, parent=parent, index=index)


def main():
    data_changed = False

    with open(".pre-commit-config.yaml") as f:
        data = yaml.load(f, Loader=SafeLoader)

        for repo_name in REPOS_TO_CHECK:
            repo = next(
                (
                    item
                    for item in data.get("repos", [])
                    if item.get("repo", "").endswith(repo_name)
                ),
                {},
            )

            for hook in repo.get("hooks", []):
                files = hook.get("files", "")
                folder = files[1 : files.index("/")]
                additional_dependencies_list = hook.get("additional_dependencies", [])

                with open(f"{folder}/package.json") as package_json:
                    package_json_data = json.load(package_json)
                    dev_dependencies = package_json_data.get("devDependencies", {})

                    for dependency in DEPENDENCIES_TO_IGNORE:
                        dev_dependencies.pop(dependency, None)

                    dev_dependencies_list = [
                        f"{key}@{value}" for key, value in dev_dependencies.items()
                    ]

                    additional_dependencies_list.sort()
                    dev_dependencies_list.sort()

                    if additional_dependencies_list != dev_dependencies_list:
                        hook["additional_dependencies"] = dev_dependencies_list
                        repo["hooks"] = [
                            hook if item.get("files", "") == files else item
                            for item in repo["hooks"]
                        ]
                        data["repos"] = [
                            repo if item.get("repo", "") == repo["repo"] else item
                            for item in data["repos"]
                        ]

                        print(
                            f"Additional dependencies are out of sync with package.json in /{folder}"
                        )
                        print(".pre-commit-config.yaml:")
                        print(
                            set(additional_dependencies_list)
                            - set(dev_dependencies_list)
                        )
                        print("package.json:")
                        print(
                            set(dev_dependencies_list)
                            - set(additional_dependencies_list),
                            end="\n\n",
                        )

                        data_changed = True

    if data_changed:
        with open(".pre-commit-config.yaml", "w") as f:
            yaml.dump(data, f, Dumper=Dumper, sort_keys=False)

        print("Pre-commit config has been updated.")
        return 1

    return 0


if __name__ == "__main__":
    main()
