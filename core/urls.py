from django.urls import path, include
from django.contrib import admin
from core import views


admin.site.site_header = "Quiz Admin"
admin.site.site_title = "Quiz Admin Portal"
admin.site.index_title = "Welcome to Quiz Portal"

urlpatterns = [
    path('login/', views.LoginView.as_view(), name="login"),
    path('logout/', views.LogoutView.as_view(), name="logout"),
    path('', include('quiz.urls')),
    path('admin/', admin.site.urls),
]

handler400 = 'core.views.custom_bad_request_view'
handler403 = 'core.views.custom_permission_denied_view'
handler404 = 'core.views.custom_page_not_found_view'
handler500 = 'core.views.custom_error_view'
