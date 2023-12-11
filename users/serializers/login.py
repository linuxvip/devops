from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.translation import gettext_lazy as _

from users.models import Users


class LoginSerializer(TokenObtainPairSerializer):
    """
    登录的序列化器:
    重写djangorestframework-simplejwt的序列化器
    """

    class Meta:
        model = Users
        fields = "__all__"
        read_only_fields = ["id"]

    default_error_messages = {"no_active_account": _("账号/密码错误")}

    def validate(self, attrs):
        try:
            super().validate(attrs)
            refresh = self.get_token(self.user)
            res_data = {}
            res_data["refreshToken"] = str(refresh)
            res_data["accessToken"] = str(refresh.access_token)
            res_data["tokenType"] = "Bearer"
            res_data["expires"] = int(0)
            return {"code": "00000", "msg": "登录成功", "data": res_data}

        except Exception as e:
            res_data = {}
            return {"code": "40000", "msg": "用户密码错误", "data": res_data}
