class SandboxedFunction:
    def __init__(self, caps: list[str] | None, rw_paths: list[str] | None):
        self.caps = caps
        self.rw_paths = rw_paths

    def inner_file_name(self) -> str:
        return (f"{self.__class__.__name__.lower()}.py")

    def capabilities(self) -> list[str] | None:
        return self.caps

    def read_write_paths(self) -> list[str] | None:
        return self.rw_paths
