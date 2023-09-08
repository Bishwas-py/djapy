class DataWrapper:
    data: dict

    def __init__(self):
        self.data = {}

    def add_data(self, key, value):
        self.data[key] = value

    def get_data(self, key):
        return self.data.get(key, None)

    def __getattr__(self, attr):
        if attr in self.data:
            return self.data[attr]
        raise AttributeError(f"'DataWrapper' object has no attribute '{attr}'")


class QueryWrapper:
    query: dict

    def __init__(self):
        self.query = {}

    def add_query(self, key, value):
        self.query[key] = value

    def get_query(self, key):
        return self.query.get(key, None)

    def __getattr__(self, attr):
        if attr in self.query:
            return self.query[attr]
        raise AttributeError(f"'QueryWrapper' object has no attribute '{attr}'")

    def __getitem__(self, item):
        return self.query[item]

    def get(self, item, default=None):
        return self.query.get(item, default)
