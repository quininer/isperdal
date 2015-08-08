from http.client import responses as resps

from .utils import Ok, Err


class Response(object):
    """
    Response class.
    """

    def __init__(self, start_response):
        """
        init Response.

        + start_response<fn>     WSGI start_response
        """
        self.start_response = start_response
        self.headers = {}
        self.body = []
        self.status_code = 0
        self.status_text = None

    def status(self, code, text=None):
        """
        Set status.

        + code<int>         status code.
        + text<str>         status text.

        - self          Response object
        """
        self.status_code = code
        self.status_text = text
        return self

    def header(self, name, value):
        """
        Set header.

        + name<str>         header name.
        + value<str>        header value.

        ...
        """
        self.headers[name] = value
        return self

    def push(self, body):
        """
        Push content to body.

        + body<str>         body string.
            or bytes.

        ...
        """
        if isinstance(body, str):
            body = body.encode()

        bodysplit = (
            lambda b: [b[r:r+8192] for r in range(0, len(b), 8192)]
        )(body)

        self.body.extend(bodysplit)
        return self

    def ok(self, T=None):
        """
        Complete a response.
            return iterables object or `res.body`.

        + T                 iterables or coroutine

        - <Ok>
        """
        self.start_response(
            "{} {}".format(
                self.status_code or 200,
                self.status_text or resps.get(
                    self.status_code or 200,
                    "Unknown"
                )
            ),
            self.headers.items()
        )
        return Ok(self.body if T is None else T)

    def err(self, E):
        """
        Throw a error.

        + E

        - <Err>
        """
        return Err(E)

    def redirect(self, url):
        if not (300 <= self.status_code < 400):
            self.status(302)
        return Err(url)
