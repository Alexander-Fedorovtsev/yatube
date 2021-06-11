from django.urls import path

from . import views

app_name = 'about'

urlpatterns = [
    path('', views.AboutProjectView.as_view(), name='project'),
    path('author/', views.AboutAuthorView.as_view(), name='author'),
    path('tech/', views.AboutTechView.as_view(), name='tech'),
]
