from rest_framework.status import HTTP_401_UNAUTHORIZED
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.models import Users
from users.serializers.login import LoginSerializer
from users.utils.json_response import ErrorResponse, DetailResponse


class CustomTokenRefreshView(TokenRefreshView):
    """
    自定义token刷新
    """
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        try:
            token = RefreshToken(refresh_token)
            data = {
                "access": str(token.access_token),
                "refresh": str(token)
            }
        except:
            return ErrorResponse(status=HTTP_401_UNAUTHORIZED)
        return DetailResponse(data=data)


class LoginView(TokenObtainPairView):
    """
    登录接口
    """
    serializer_class = LoginSerializer
    permission_classes = []


class LogoutView(APIView):
    def delete(self, request):
        Users.objects.filter(id=self.request.user.id).update(last_token=None)
        return DetailResponse(msg="注销成功")

