"""
File open helpers.
"""

def open_compressed(file_path, mode='r'):
    """Open file path and decompress on the fly using built in standard
    library modules if it has the appropriate extension."""
    if file_path.endswith('.xz'):
        import lzma
        return lzma.open(file_path, mode)
    elif file_path.endswith('.bz2'):
        import bz2
        return bz2.open(file_path, mode)
    elif file_path.endswith('.gz'):
        import gzip
        return gzip.open(file_path, mode)
    else:
        return open(file_path, mode)
