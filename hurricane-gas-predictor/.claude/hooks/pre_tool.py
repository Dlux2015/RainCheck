"""Pre-tool hook: block writes that would overwrite a bronze Delta path."""

import json
import sys


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    if tool in ("Write", "Edit"):
        content = str(tool_input.get("content", "")) + str(tool_input.get("new_string", ""))
        if "bronze" in content.lower() and '.mode("overwrite")' in content:
            print(json.dumps({
                "decision": "block",
                "reason": (
                    "Bronze layer is append-only per CLAUDE.md. "
                    "Replace .mode('overwrite') with .mode('append')."
                ),
            }))
            sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
