from django.urls import path
from . import views

urlpatterns = [
    path('posts/', views.PostView.as_view(), name='posts_list'),
    path('status/', views.StatusView.as_view()),
    path('rel/', views.RelView.as_view()),
    path('play/', views.TestView.say_hello),
]
