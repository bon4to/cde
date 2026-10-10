import re


CDE_TAG_PATTERN = re.compile(r">[ \t]*CDE(?!\w)", re.IGNORECASE)


def extract_cde_observation(value, show_untagged=True):
    """Return tagged CDE sections, or full observation when no tag exists."""
    if value is None:
        return ""

    observation = str(value)
    sections = CDE_TAG_PATTERN.split(observation)

    tag_count = len(sections) - 1
    if tag_count == 0:
        return observation if show_untagged else ""
    if tag_count % 2:
        return observation

    tagged_sections = [
        sections[index].strip()
        for index in range(1, len(sections) - 1, 2)
        if sections[index].strip()
    ]
    return "\n".join(tagged_sections)
