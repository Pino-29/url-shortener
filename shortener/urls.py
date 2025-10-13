from django.urls import path
from . import views

app_name = 'shortener'

urlpatterns = [
    path('', views.home, name='home'),
    path('v1/urls/', views.create_short_url, name='create_short_url'),
    path('v1/urls/<str:short_code>/', views.redirect_to_original, name='redirect_to_original'),
]