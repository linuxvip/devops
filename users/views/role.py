# -*- coding: utf-8 -*-

"""
@Remark: 角色管理
"""
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from users.models import Role, Menu
from users.views.menu import MenuSerializer
from users.utils.json_response import SuccessResponse, DetailResponse
from users.utils.serializers import CustomModelSerializer
from users.utils.validator import CustomUniqueValidator
from users.utils.viewset import CustomModelViewSet


class RoleSerializer(CustomModelSerializer):
    """
    角色-序列化器
    """

    class Meta:
        model = Role
        fields = "__all__"
        read_only_fields = ["id"]


class RoleInitSerializer(CustomModelSerializer):
    """
    初始化获取数信息(用于生成初始化json文件)
    """

    class Meta:
        model = Role
        fields = ['name', 'key', 'sort', 'status', 'admin', 'data_range', 'remark',
                  'creator', 'dept_belong_id']
        read_only_fields = ["id"]
        extra_kwargs = {
            'creator': {'write_only': True},
        }


class RoleCreateUpdateSerializer(CustomModelSerializer):
    """
    角色管理 创建/更新时的列化器
    """
    menu = MenuSerializer(many=True, read_only=True)
    key = serializers.CharField(max_length=50,
                                validators=[CustomUniqueValidator(queryset=Role.objects.all(), message="权限字符必须唯一")])
    name = serializers.CharField(max_length=50, validators=[CustomUniqueValidator(queryset=Role.objects.all())])

    def validate(self, attrs: dict):
        return super().validate(attrs)

    def save(self, **kwargs):
        is_superuser = self.request.user.is_superuser
        if not is_superuser:
            self.validated_data.pop('admin')
        data = super().save(**kwargs)
        data.menu.set(self.initial_data.get('menu', []))
        data.permission.set(self.initial_data.get('permission', []))
        return data

    class Meta:
        model = Role
        fields = '__all__'


class MenuPermissonSerializer(CustomModelSerializer):
    """
    菜单的按钮权限
    """
    menuPermission = serializers.SerializerMethodField()

    def get_menuPermission(self, instance):
        is_superuser = self.request.user.is_superuser
        if is_superuser:
            queryset = MenuButton.objects.filter(menu__id=instance.id)
        else:
            menu_permission_id_list = self.request.user.role.values_list('permission', flat=True)
            queryset = MenuButton.objects.filter(id__in=menu_permission_id_list, menu__id=instance.id)
        serializer = MenuButtonSerializer(queryset, many=True, read_only=True)
        return serializer.data

    class Meta:
        model = Menu
        fields = ['id', 'parent', 'name', 'menuPermission']


class RoleViewSet(CustomModelViewSet):
    """
    角色管理接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    create_serializer_class = RoleCreateUpdateSerializer
    update_serializer_class = RoleCreateUpdateSerializer
    search_fields = ['name', 'key']

    @action(methods=['GET'], detail=False, permission_classes=[IsAuthenticated])
    def role_get_menu(self, request):
        """根据当前用户的角色返回角色拥有的菜单"""
        is_superuser = request.user.is_superuser
        is_admin = request.user.role.values_list('admin', flat=True)
        if is_superuser or True in is_admin:
            queryset = Menu.objects.filter(status=True).all()
        else:
            menu_id_list = request.user.role.values_list('menu', flat=True)
            queryset = Menu.objects.filter(id__in=menu_id_list)
        # queryset = self.filter_queryset(queryset)
        serializer = MenuPermissonSerializer(queryset, many=True,request=request)
        return DetailResponse(data=serializer.data)
