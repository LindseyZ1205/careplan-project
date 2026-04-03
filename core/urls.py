from django.urls import path

from . import views

urlpatterns = [
    path("", views.careplan_form, name="careplan_form"),
    path("api/careplan/", views.generate_careplan_api, name="generate_careplan_api"),
    path(
        "api/careplan/<int:id>/status/",
        views.careplan_status_api,
        name="careplan_status",
    ),
    path("api/careplan/<int:id>/", views.get_careplan_api, name="get_careplan"),
]
