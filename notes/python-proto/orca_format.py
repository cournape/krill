import pathlib

def load_orca_file(path):
    path = pathlib.Path(path)
    size = path.stat().st_size

    if size > 1024 ** 2:
        raise ValueError(f"File {path} too big.")

    with open(path, "rt") as fp:
        # We can read all in memory because we checked the file was not crazy
        # large
        lines = fp.read().splitlines()
        if len(lines) > 200:
            raise ValueError(
                f"File {path} has too many lines ({len(lines)}, max is 200)"
            )

        if len(lines) < 1:
            raise ValueError(f"Empty file !")

        n = len(lines[0])
        for i, line in enumerate(lines):
            if len(line) != n:
                raise ValueError(
                    f"Line {i} length is inconsistent: {len(line)} vs {n}")

        return [list(line) for line in lines]
