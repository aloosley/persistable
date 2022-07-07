class ExplainedNotImplementedError(NotImplementedError):
    def __init__(self, method_name: str) -> None:
        super().__init__(f"{self.__class__.__name__}.{method_name} not implemented")
