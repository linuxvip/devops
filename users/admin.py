from django.contrib import admin

# from django.contrib.auth.admin import UserAdmin
from .models import Users, Role, Menu


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'mobile', 'name')
    search_fields = ('username', 'email', 'mobile', 'name')
    filter_horizontal = ('role', )  # 或者使用 filter_vertical


admin.site.register(Users, CustomUserAdmin)


class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'key', 'sort', 'status', 'admin')
    search_fields = ('name', 'key', 'remark')
    filter_horizontal = ("menu",)


admin.site.register(Role, RoleAdmin)


class MenuAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'menu_type', 'path', 'component', 'sort', 'visible', 'icon', 'redirect', 'perm', 'parent')
    search_fields = ('name', 'path', 'component', 'perm')
    list_filter = ('menu_type', 'visible', 'parent')

admin.site.register(Menu, MenuAdmin)

admin.site.site_header = '后台管理系统'
admin.site.index_title = '首页'
