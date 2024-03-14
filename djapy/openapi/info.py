from typing_extensions import TypedDict


class License(TypedDict):
    name: str
    url: str
    identifier: str


class Contact(TypedDict):
    name: str
    url: str
    email: str


class Info:
    def __init__(self, title: str, version: str, description: str):
        self.title = title
        self.version = version
        self.description = description
        self.license = None
        self.contact = None

    def dict(self):
        return {
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "license": self.license,
            "contact": self.contact,
        }
