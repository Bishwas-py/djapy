# The `data` module

The `data` module is the contains `__init__.py`, `fields.py`, `mapper.py` and `dec.py`. The `__init__.py` file is 
empty, and the `dec.py` file is a decorator that is used to decorate the `mapper.py` file.

## The `fields.py` file

The `fields.py` file contains the utility functions for `dec.py` and which are also used by other modules.

## The `mapper.py` file

The `mapper.py` file contains the `QueryWrapper` and `DataWrapper` classes. The `QueryWrapper` class is used to
wrap the querysets and the `DataWrapper` class is used to wrap the data that is returned by the `QueryWrapper` class.

## The `dec.py` file

It contains the `input_required` and `field_required` decorators.

### The `input_required` decorator
The `input_required` decorator is used in following way:

```python
from djapy.data import input_required


@input_required(['data', 'data1', 'data2'], ['query', 'query1', 'query2'])
def my_view(request, data, query):
    data1 = data['data1']  # or data.get('data1') or data.data1
    data2 = data.data2
    query1 = query['query1']  # or query.get('query1') or query.query1
    query2 = query.query2
# ...
```

The `QueryWrapper` and `DataWrapper` are only used by the `input_required` decorator. The `input_required` decorator    
uses the wrappers to assign the value of gained query or data to the view function.


### The `field_required` decorator

