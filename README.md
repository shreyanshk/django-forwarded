# Django-Forwarded

Support HTTP "Forwarded" header in your Django applications.

This middleware for [Django](https://www.djangoproject.com/) adds support for the `Forwarded` header which is standardized by Internet Engineering Task Force (IETF) in [RFC 7239](https://tools.ietf.org/html/rfc7239#section-5) and summarized in [Mozilla Developer Network (MDN) article](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Forwarded) of the same name. This header is used by many reverse HTTP proxies to pass client identification details (such as IPv4 or IPv6) to the backend application.

## Installation

Install the middleware with your favorite Python package manager

Pip:
```shell
$ pip install django-forwarded
```

Pipenv:
```shell
$ pipenv install django-forwarded
```

## Usage

### Activate

Add the middleware to Django's MIDDLEWARE setting.

```python
MIDDLEWARE = (
    ... # some middlewares
    "django_forwarded.Forwarded",
    ... # more middlewares
)
```

### Configure

You can configure Django-Forwarded by adding appropriate variable to your Django application [configuration file](https://docs.djangoproject.com/en/2.2/topics/settings/).

#### With TRUSTED_PROXY_LIST

Just specify a list of trusted proxies with the `TRUSTED_PROXY_LIST` variable in the file. This is the recommended way to specify the proxies.

```python
TRUSTED_PROXY_LIST = [
    '2001:db8::10',
    '10.2.3.100',
]
```

#### With TRUSTED_PROXY_DEPTH

Just specify the number of trusted proxies with the `TRUSTED_PROXY_DEPTH` variable. This is useful when you have no control over them and their IP(s) might change frequently over the lifetime of your application.

```python
TRUSTED_PROXY_DEPTH = 2  # trusts maximum of 2 proxies
```

**Note: It is not secure as secure as specifying a list.**

### Access client IP

The middleware identifies the correct client IP from the user supplied configuration and the header received from the proxies. This information is then placed in the `request.META['REMOTE_ADDR']` field.

```python
def some_function(request):
    print(request.META['REMOTE_ADDR'])
```

## Testing

To execute the included test suit, run the following commands in a terminal:

```shell
$ cd <path to the django-forwarded>
$ pipenv shell  # opens a shell in dev environment
$ DJANGO_SETTINGS_MODULE=tests.settings python3 -m unittest  # run the tests
```
