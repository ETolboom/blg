import os


def safe_join(base_dir: str, *parts: str) -> str:
    """Join untrusted ``parts`` onto ``base_dir``; return an absolute path
    guaranteed to be strictly inside ``base_dir``.

    Defends against directory traversal (``..``), absolute-path injection and
    symlinks pointing outside the base. Raises ``ValueError`` if the parts are
    empty or the result would escape the base directory.
    """
    base = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base, *parts))

    try:
        within_base = os.path.commonpath([base, target]) == base
    except ValueError:
        # Different drives/anchors (Windows) -> definitely outside.
        within_base = False

    if target == base or not within_base:
        raise ValueError("Invalid path")

    return target
