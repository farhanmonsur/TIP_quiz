from django.views.generic import TemplateView
from django.contrib.auth import views as auth


class LoginView(auth.LoginView):
    template_name = "login.html"
    extra_context = {'title': "Login"}


class LogoutView(auth.LogoutView):
    extra_context = {'title': "Logout"}


class ErrorView(TemplateView):
    template_name = "error.html"

    def get(self, request, exception=None, *args, **kwargs):
        return super().get(request, *args, **kwargs)


custom_page_not_found_view = ErrorView.as_view(
    extra_context={
        'title': "Error 404 – Page Not Found",
        'status_code': 404,
        'message': "The page you requested was not found."
    }
)

custom_error_view = ErrorView.as_view(
    extra_context={
        'title': "Error 500 – Server Error",
        'status_code': 500,
        'message': "Oops, something went wrong."
    }
)

custom_permission_denied_view = ErrorView.as_view(
    extra_context={
        'title': "Error 403 – Forbidden",
        'status_code': 403,
        'message': "You don’t have permission to access this url on this server."  # noqa
    }
)


custom_bad_request_view = ErrorView.as_view(
    extra_context={
        'title': "Error 400 – Bad Request",
        'status_code': 400,
        'message': "You've sent a bad request."
    }
)
