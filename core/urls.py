from django.urls import path

from . import views

urlpatterns = [
    path("", views.careplan_form, name="careplan_form"),
    path("api/careplan/", views.generate_careplan_api, name="generate_careplan_api"),
]

