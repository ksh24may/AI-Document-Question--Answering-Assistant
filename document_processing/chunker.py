def chunk_text(text, chunk_size=1000, overlap=200):
    """
    Split text into overlapping chunks.

    Chunks try to end at spaces/newlines so words
    are not unnecessarily cut in half.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be >= 0 and smaller than chunk_size"
        )

    if not text:
        return []

    chunks = []

    start = 0
    length = len(text)

    while start < length:

        end = min(start + chunk_size, length)

        # Try to stop at a space or newline
        if end < length:

            last_space = max(
                text.rfind(" ", start, end),
                text.rfind("\n", start, end)
            )

            if last_space > start + overlap:
                end = last_space

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        # Stop when we reach the end
        if end >= length:
            break

        # Create overlap
        next_start = end - overlap

        # Move forward to beginning of next word
        next_space = text.find(" ", next_start, end)

        if next_space != -1:
            next_start = next_space + 1

        start = next_start

    return chunks