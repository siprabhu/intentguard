"""Portable digests for UTF-8 source/fixture files tracked by Git."""
import hashlib
from pathlib import Path


def source_digest(path):
    # Git's platform line-ending conversion must not invalidate identical text.
    return hashlib.sha256(Path(path).read_text(encoding='utf-8').encode('utf-8')).hexdigest()
