class Info:
    def __init__(self, title: str, version: str, description: str):
        self.title = title
        self.version = version
        self.description = description

    def dict(self):
        return {
            "title": self.title,
            "version": self.version,
            "description": self.description
        }
