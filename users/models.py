from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password
from django.db import models
from users.utils.models import CoreModel, table_prefix


class Users(CoreModel, AbstractUser):
    username = models.CharField(max_length=150, unique=True, db_index=True, verbose_name="用户账号",
                                help_text="用户账号")
    email = models.EmailField(max_length=255, verbose_name="邮箱", null=True, blank=True, help_text="邮箱")
    mobile = models.CharField(max_length=255, verbose_name="电话", null=True, blank=True, help_text="电话")
    avatar = models.CharField(max_length=255, verbose_name="头像", null=True, blank=True, help_text="头像")
    name = models.CharField(max_length=40, verbose_name="姓名", help_text="姓名")
    role = models.ManyToManyField(to="Role", blank=True, verbose_name="关联角色", db_constraint=False,
                                  help_text="关联角色")
    last_token = models.CharField(max_length=255, null=True, blank=True, verbose_name="最后一次登录Token",
                                  help_text="最后一次登录Token")

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def __str__(self):
        return self.username

    class Meta:
        db_table = table_prefix + "system_users"
        verbose_name = "用户表"
        verbose_name_plural = verbose_name
        ordering = ("-create_datetime",)


class Role(CoreModel):
    name = models.CharField(max_length=64, verbose_name="角色名称", help_text="角色名称")
    key = models.CharField(max_length=64, unique=True, verbose_name="权限字符", help_text="权限字符")
    sort = models.IntegerField(default=1, verbose_name="角色顺序", help_text="角色顺序")
    status = models.BooleanField(default=True, verbose_name="角色状态", help_text="角色状态")
    admin = models.BooleanField(default=False, verbose_name="是否为admin", help_text="是否为admin")
    remark = models.TextField(verbose_name="备注", help_text="备注", null=True, blank=True)
    menu = models.ManyToManyField(to="Menu", verbose_name="关联菜单", db_constraint=False,
                                  related_name="role_menus", help_text="关联菜单")

    def __str__(self):
        return self.name

    class Meta:
        db_table = table_prefix + "system_roles"
        verbose_name = "角色表"
        verbose_name_plural = verbose_name
        ordering = ("sort",)


class Menu(CoreModel):
    name = models.CharField(max_length=64, verbose_name="菜单名称", help_text="菜单名称")
    MENU_TYPE_CHOICES = (
        ('NULL', 'Null'),
        ('MENU', '菜单'),
        ('CATALOG', '目录'),
        ('EXTLINK', '外链'),
        ('BUTTON', '按钮'),
    )
    menu_type = models.CharField(max_length=10, verbose_name="菜单类型", choices=MENU_TYPE_CHOICES,
                                 help_text="菜单类型")
    path = models.CharField(max_length=128, verbose_name="路由地址", null=True, blank=True,
                            help_text="路由地址")
    component = models.CharField(max_length=128, verbose_name="组件地址", null=True, blank=True,
                                 help_text="组件地址")
    sort = models.IntegerField(default=1, verbose_name="显示排序", null=True, blank=True,
                               help_text="显示排序")
    visible = models.BooleanField(default=True, blank=True, verbose_name="侧边栏中是否显示",
                                  help_text="侧边栏中是否显示")
    icon = models.CharField(max_length=64, verbose_name="菜单图标", null=True, blank=True,
                            help_text="菜单图标")
    redirect = models.CharField(max_length=255, verbose_name="跳转路径", null=True, blank=True,
                                help_text="跳转路径")
    perm = models.CharField(max_length=128, verbose_name="按钮权限", null=True, blank=True,
                            help_text="按钮权限")
    keep_alive = models.BooleanField(default=False, blank=True, verbose_name="是否开启页面缓存",
                                     help_text="【菜单】是否开启页面缓存(1:是 0:否)")
    always_show = models.BooleanField(default=False, blank=True, verbose_name="只有一个子路由是否始终显示",
                                      help_text="【目录】只有一个子路由是否始终显示(1:是 0:否)")
    parent = models.ForeignKey('self', verbose_name="父级菜单", on_delete=models.CASCADE,
                               null=True, blank=True, related_name='children', help_text="父级菜单")
    roles = models.ManyToManyField(to="Role", verbose_name="关联角色", db_constraint=False,
                                   related_name="menu_roles", help_text="关联角色")

    def __str__(self):
        return self.name

    class Meta:
        db_table = table_prefix + "system_menu"
        verbose_name = "菜单表"
        verbose_name_plural = verbose_name
        ordering = ("sort",)
