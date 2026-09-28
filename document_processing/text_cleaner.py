import re


def clean_text(text):
    """
    Clean extracted PDF text so it is ready for embeddings.
    """

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove null characters
    text = text.replace("\x00", "")

    # Replace non-breaking spaces
    text = text.replace("\u00a0", " ")

    # Replace form-feed characters
    text = text.replace("\x0c", "\n")

    # Join words broken by PDF line wrapping
    # Example: infor-\nmation -> information
    text = re.sub(
        r"(\w)-\n(\w)",
        r"\1\2",
        text
    )

    # Collapse multiple spaces/tabs
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # Remove spaces around newlines
    text = re.sub(
        r" *\n *",
        "\n",
        text
    )

    # Remove excessive blank lines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()