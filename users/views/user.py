import hashlib

from django.contrib.auth.hashers import make_password, check_password
from rest_framework import serializers
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from users.models import Users, Role, Menu
from users.utils.json_response import ErrorResponse, DetailResponse
from users.utils.serializers import CustomModelSerializer
from users.utils.validator import CustomUniqueValidator
from users.utils.viewset import CustomModelViewSet
from users.views.role import RoleSerializer


class UserSerializer(CustomModelSerializer):
    """
    用户管理-序列化器
    """
    class Meta:
        model = Users
        read_only_fields = ["id"]
        exclude = ["password", "first_name", "last_name", "groups", "user_permissions"]

    def get_role_info(self, instance, parsed_query):
        roles = instance.role.all()
        # You can do what ever you want in here
        # `parsed_query` param is passed to BookSerializer to allow further querying
        serializer = RoleSerializer(
            roles,
            many=True,
            parsed_query=parsed_query
        )
        return serializer.data


class UserCreateSerializer(CustomModelSerializer):
    """
    用户新增-序列化器
    """

    username = serializers.CharField(
        max_length=50,
        validators=[
            CustomUniqueValidator(queryset=Users.objects.all(), message="账号必须唯一")
        ],
    )
    password = serializers.CharField(required=False,)

    def validate_password(self, value):
        """
        对密码进行验证
        """
        password = self.initial_data.get("password")
        if password:
            return make_password(value)
        return value

    def save(self, **kwargs):
        data = super().save(**kwargs)
        return data

    class Meta:
        model = Users
        fields = "__all__"
        read_only_fields = ["id"]


class UserUpdateSerializer(CustomModelSerializer):
    """
    用户修改-序列化器
    """

    username = serializers.CharField(
        max_length=50,
        validators=[
            CustomUniqueValidator(queryset=Users.objects.all(), message="账号必须唯一")
        ],
    )
    # password = serializers.CharField(required=False, allow_blank=True)
    mobile = serializers.CharField(
        max_length=50,
        validators=[
            CustomUniqueValidator(queryset=Users.objects.all(), message="手机号必须唯一")
        ],
        allow_blank=True
    )

    def save(self, **kwargs):
        data = super().save(**kwargs)
        return data

    class Meta:
        model = Users
        read_only_fields = ["id", "password"]
        fields = "__all__"


class UserInfoUpdateSerializer(CustomModelSerializer):
    """
    用户修改-序列化器
    """
    mobile = serializers.CharField(
        max_length=50,
        validators=[
            CustomUniqueValidator(queryset=Users.objects.all(), message="手机号必须唯一")
        ],
        allow_blank=True
    )

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

    class Meta:
        model = Users
        fields = "__all__"
        extra_kwargs = {
            "post": {"required": False, "read_only": True},
        }


class UserViewSet(CustomModelViewSet):
    """
    用户接口
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """

    # queryset = Users.objects.exclude(is_superuser=True).all()
    queryset = Users.objects.all()
    serializer_class = UserSerializer
    create_serializer_class = UserCreateSerializer
    update_serializer_class = UserUpdateSerializer
    filter_fields = ["^name", "~username", "^mobile", "is_active"]
    search_fields = ["username", "name", "dept__name", "role__name"]

    @action(methods=["GET"], detail=False, permission_classes=[IsAuthenticated])
    def user_info(self, request):
        """获取当前用户信息"""
        user = request.user
        data = {
            "userId": user.id,
            "nickname": user.username,
            "avatar": user.avatar,
            "roles": [role.key for role in user.role.all()],
            "perms": self.get_user_perms(user),
        }

        return DetailResponse(data=data, msg="获取成功")

    def get_user_perms(self, user):
        perms = []
        if user.is_superuser:
            for menu in Menu.objects.all():
                if menu.perm:
                    perms.append(menu.perm)
        else:
            for role in user.role.all():
                for perm in role.menu.values_list('perm', flat=True):
                    if perm:
                        perms.append(perm)
        return perms

    @action(methods=["PUT"], detail=False, permission_classes=[IsAuthenticated])
    def update_user_info(self, request):
        """修改当前用户信息"""
        serializer = UserInfoUpdateSerializer(request.user, data=request.data, request=request)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return DetailResponse(data=None, msg="修改成功")

    @action(methods=["PUT"], detail=True, permission_classes=[IsAuthenticated])
    def change_password(self, request, *args, **kwargs):
        """密码修改"""
        data = request.data
        old_pwd = data.get("oldPassword")
        new_pwd = data.get("newPassword")
        new_pwd2 = data.get("newPassword2")
        if old_pwd is None or new_pwd is None or new_pwd2 is None:
            return ErrorResponse(msg="参数不能为空")
        if new_pwd != new_pwd2:
            return ErrorResponse(msg="两次密码不匹配")
        verify_password = check_password(old_pwd, self.request.user.password)
        if not verify_password:
            verify_password = check_password(hashlib.md5(old_pwd.encode(encoding='UTF-8')).hexdigest(), self.request.user.password)
        if verify_password:
            request.user.password = make_password(new_pwd)
            request.user.save()
            return DetailResponse(data=None, msg="修改成功")
        else:
            return ErrorResponse(msg="旧密码不正确")

    @action(methods=["PUT"], detail=True, permission_classes=[IsAuthenticated])
    def reset_to_default_password(self, request, *args, **kwargs):
        """恢复默认密码"""
        instance = Users.objects.filter(id=kwargs.get("pk")).first()
        if instance:
            instance.set_password("123456")
            instance.save()
            return DetailResponse(data=None, msg="密码重置成功")
        else:
            return ErrorResponse(msg="未获取到用户")

    @action(methods=["PUT"], detail=True)
    def reset_password(self, request, pk):
        """
        密码重置
        """
        instance = Users.objects.filter(id=pk).first()
        data = request.data
        new_pwd = data.get("newPassword")
        new_pwd2 = data.get("newPassword2")
        if instance:
            if new_pwd != new_pwd2:
                return ErrorResponse(msg="两次密码不匹配")
            else:
                instance.password = make_password(new_pwd)
                instance.save()
                return DetailResponse(data=None, msg="修改成功")
        else:
            return ErrorResponse(msg="未获取到用户")
