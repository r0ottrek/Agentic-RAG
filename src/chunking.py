def chunk_text(text: str, size: int, overlap:int) -> list[str]:
    """split text into overlapping windows of 'size' characters."""
    if not text.strip():
            return[]
    chunks = []
    start = 0
    while start < len(text):
          end = start + size
          chunks.append(text[start:end])
          start += size - overlap # step forward, but leave 'overlap' shared with the last chunk
    return chunks
