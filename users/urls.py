from django.urls import path
from rest_framework import routers

from users.views.user import UserViewSet
from users.views.role import RoleViewSet
from users.views.menu import MenuViewSet


users_url = routers.SimpleRouter()
users_url.register(r'user', UserViewSet)
users_url.register(r'role', RoleViewSet)
users_url.register(r'menu', MenuViewSet)


urlpatterns = [
    ]
urlpatterns += users_url.urls
