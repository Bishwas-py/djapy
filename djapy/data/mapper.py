class DataWrapper:
    x_data: dict

    def __init__(self):
        self.x_data = {}

    def add_data(self, key, value):
        self.x_data[key] = value

    def get_data(self, key):
        return self.x_data.get(key, None)

    def __getattr__(self, attr):
        if attr in self.x_data:
            return self.x_data[attr]
        raise AttributeError(f"'DataWrapper' object has no attribute '{attr}'")


class QueryWrapper:
    x_query: dict

    def __init__(self):
        self.x_query = {}

    def add_query(self, key, value):
        self.x_query[key] = value

    def get_query(self, key):
        return self.x_query.get(key, None)

    def __getattr__(self, attr):
        if attr in self.x_query:
            return self.x_query[attr]
        raise AttributeError(f"'QueryWrapper' object has no attribute '{attr}'")

    def __getitem__(self, item):
        return self.x_query[item]

    def get(self, item, default=None):
        return self.x_query.get(item, default)

