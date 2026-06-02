"""Post-tool hook: remind to run pytest after Python source changes."""

import json
import sys

CODE_EXTENSIONS = (".py", ".sql", ".yaml", ".yml")


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    file_path = str(tool_input.get("file_path", ""))

    if tool in ("Write", "Edit") and any(file_path.endswith(ext) for ext in CODE_EXTENSIONS):
        if "/tests/" not in file_path and "\\.claude\\" not in file_path:
            print(f"[post-tool] Source changed: {file_path} — run pytest before marking task done.")

    sys.exit(0)


if __name__ == "__main__":
    main()
