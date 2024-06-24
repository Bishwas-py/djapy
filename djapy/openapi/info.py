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
    def __init__(self, title: str, version: str, description: str, site_name="Djapy"):
        self.title = title
        self.version = version
        self.cvar_describe = description
        self.license = None
        self.contact = None
        self.site_name = site_name

    def dict(self):
        return {
            "title": self.title,
            "version": self.version,
            "description": self.cvar_describe,
            "license": self.license,
            "contact": self.contact
        }
