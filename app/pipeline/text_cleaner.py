import json


def raw_cleaned_func(raw_text):
    """Flatten the nested scraped JSON into a plain multi-line string for the LLM."""
    data    = json.loads(raw_text)
    title   = data.get("title", "")
    section = data.get("data", {})

    lines = [title]

    def flatten(item):
        if isinstance(item, str):
            return [item] if item else []
        if isinstance(item, list):
            result = []
            for sub in item:
                result.extend(flatten(sub))
            return result
        if isinstance(item, dict):
            result = []
            for heading, value in item.items():
                result.append(heading)
                result.extend(flatten(value))
            return result
        return []

    if isinstance(section, dict):
        for heading, groups in section.items():
            lines.append(heading)
            lines.extend(flatten(groups))
    elif isinstance(section, list):
        lines.extend(flatten(section))

    return "\n".join(lines)
