from django.views.decorators.csrf import csrf_exempt


class CSRFExempt:
    @csrf_exempt
    def __render__(self, request, *args, **kwargs):
        render = getattr(super(), 'render')
        return render(request, *args, **kwargs)
