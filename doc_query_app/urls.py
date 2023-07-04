from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("signup", views.signup_view, name="signup"),
    path("query", views.query_files, name="query"),
    path("delete/<str:username>/<str:filename>", views.delete_file, name="delete"),
]