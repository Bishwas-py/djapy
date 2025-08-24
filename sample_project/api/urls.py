from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.list_users, name='list_users'),
    path('users/<int:user_id>/', views.get_user, name='get_user'),
    path('users/create/', views.create_user, name='create_user'),
    path('posts/', views.list_posts, name='list_posts'),
    path('posts/create/', views.create_post, name='create_post'),
    path('hello/', views.hello_world, name='hello_world'),
    path('trigger-error/', views.trigger_message_error, name='trigger_message_error'),
    path('trigger-custom/', views.trigger_custom_message, name='trigger_custom_message'),
]
