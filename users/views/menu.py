# -*- coding: utf-8 -*-

"""
@Remark: 菜单模块
"""
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from users.models import Menu
from users.utils.json_response import SuccessResponse, DetailResponse
from users.utils.serializers import CustomModelSerializer
from users.utils.viewset import CustomModelViewSet


class MenuSerializer(CustomModelSerializer):
    """
    菜单表的简单序列化器
    """
    class Meta:
        model = Menu
        fields = "__all__"
        read_only_fields = ["id"]


class MenuCreateSerializer(CustomModelSerializer):
    """
    菜单表的创建序列化器
    """
    name = serializers.CharField(required=False)

    class Meta:
        model = Menu
        fields = "__all__"
        read_only_fields = ["id"]


class RoutesSerializer(CustomModelSerializer):
    """
    前端菜单路由的简单序列化器
    """
    class Meta:
        model = Menu
        fields = "__all__"
        read_only_fields = ["id"]


class MenuViewSet(CustomModelViewSet):
    """
    菜单管理接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    create_serializer_class = MenuCreateSerializer
    update_serializer_class = MenuCreateSerializer
    search_fields = ['name', 'status']
    filter_fields = ['parent', 'name', 'status', 'is_link', 'visible', 'cache', 'is_catalog']

    @action(methods=['GET'], detail=False, permission_classes=[IsAuthenticated])
    def routes(self, request):
        """用于前端获取当前角色的路由"""
        user = request.user
        menus = self.get_user_menus(user)
        if user.is_superuser:
            # Return all menus for superuser
            return self.serialize_menus(Menu.objects.filter(parent__isnull=True))
        else:
            # Return menus based on user's roles
            return self.serialize_menus(user.role.first().menu.filter(parent__isnull=True))

        return DetailResponse(data=menus, msg="获取成功")

    def serialize_menus(self, menus):
        serialized_menus = []
        for menu in menus:
            serialized_menu = {
                "path": menu.path,
                "component": menu.component,
                "redirect": menu.redirect,
                "name": menu.name,
                "meta": {
                    "title": menu.name,
                    "icon": menu.icon,
                    "hidden": not menu.visible,
                    "roles": [role.name for role in menu.roles.all()],
                },
                "children": self.serialize_menus(menu.children.all()) if menu.children.exists() else []
            }
            serialized_menus.append(serialized_menu)
        return serialized_menus

    def list(self, request):
        """懒加载"""
        params = request.query_params
        parent = params.get('parent', None)
        if params:
            if parent:
                queryset = self.queryset.filter(parent=parent)
            else:
                queryset = self.queryset
        else:
            queryset = self.queryset.filter(parent__isnull=True)
        queryset = self.filter_queryset(queryset)
        serializer = MenuSerializer(queryset, many=True, request=request)
        data = serializer.data
        return SuccessResponse(data=data)
