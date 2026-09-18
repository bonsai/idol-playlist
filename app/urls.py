from django.urls import path
from catalog.views import dashboard

urlpatterns = [
    path("", dashboard, name="dashboard"),
]
