import json
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory

from djapy.core.mid import UHandleErrorMiddleware


def _make_middleware(response):
    return UHandleErrorMiddleware(lambda request: response)


class TestUHandleErrorMiddleware:
    def setup_method(self):
        self.rf = RequestFactory()

    def test_passes_through_200(self):
        response = JsonResponse({"ok": True})
        mw = _make_middleware(response)
        result = mw(self.rf.get("/"))
        assert result.status_code == 200

    def test_converts_html_error_to_json_for_api(self):
        html_response = HttpResponse("<h1>Not Found</h1>", status=404, content_type="text/html")
        html_response.reason_phrase = "Not Found"
        mw = _make_middleware(html_response)

        request = self.rf.get("/", HTTP_USER_AGENT="curl/7.68.0")
        result = mw(request)

        assert result.status_code == 404
        data = json.loads(result.content)
        assert data["reason"] == "Not Found"
        assert data["alias"] == "server_error"

    def test_keeps_html_for_browser(self):
        html_response = HttpResponse("<h1>Not Found</h1>", status=404, content_type="text/html")
        mw = _make_middleware(html_response)

        request = self.rf.get("/", HTTP_USER_AGENT="Mozilla/5.0 (Windows)")
        result = mw(request)

        assert result.status_code == 404
        assert b"<h1>" in result.content

    def test_passes_through_json_errors(self):
        json_response = JsonResponse({"error": "bad"}, status=400)
        mw = _make_middleware(json_response)

        request = self.rf.get("/", HTTP_USER_AGENT="curl/7.68.0")
        result = mw(request)

        assert result.status_code == 400
        data = json.loads(result.content)
        assert data == {"error": "bad"}

    def test_handles_500(self):
        html_response = HttpResponse("Server Error", status=500, content_type="text/html")
        html_response.reason_phrase = "Internal Server Error"
        mw = _make_middleware(html_response)

        request = self.rf.get("/", HTTP_USER_AGENT="python-requests/2.28")
        result = mw(request)

        assert result.status_code == 500
        data = json.loads(result.content)
        assert data["reason"] == "Internal Server Error"
