class ErrorMap:
    excluded_error = []
    only_included_error = []

    def __init__(self, excluded_error: list = None, only_included_error: list = None) -> None:
        self.excluded_error = excluded_error or self.excluded_error
        self.only_included_error = only_included_error or self.only_included_error

        if not isinstance(self.only_included_error, list):
            raise TypeError(f"Expected list, got {type(self.only_included_error)}")
        if not isinstance(self.excluded_error, list):
            raise TypeError(f"Expected list, got {type(self.excluded_error)}")
