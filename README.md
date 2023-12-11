# Devops 运维平台

[![img](https://img.shields.io/badge/python-%3E=3.9.x-green.svg)](https://python.org/)  [![PyPI - Django Version badge](https://img.shields.io/badge/django%20versions-4.2.7-blue)](https://docs.djangoproject.com/zh-hans/4.2/) 
[![img](https://img.shields.io/badge/node-%3E%3D%2012.0.0-brightgreen)](https://nodejs.org/zh-cn/) 


💡 **「关于」**

Devops 运维学习，基于Django4.2，包含RBAC权限控制系统，目的是打造一个快速开发平台，可以将运维工作中的操作 快速接入，进行开发的一个平台。



🗓️ **「开发线路」**



## 平台简介

💡 [Devops平台]() 是一套的快速开发平台，基于Django的运维后台管理平台。



* 后端采用 Python 语言 Django 框架 [Django REST Framework](https://pypi.org/project/djangorestframework)。
* 权限认证使用Django REST Framework SimpleJWT
* 支持加载动态权限菜单，多方式轻松权限控制。



## 内置功能

1. 菜单管理：配置系统菜单，操作权限，按钮权限标识、后端接口权限等。
3. 角色管理：角色菜单权限分配、数据权限分配、设置角色进行数据范围权限划分。
4. ‍权限权限：授权角色的权限范围。
5. 用户管理：用户是系统操作者，该功能主要完成系统用户配置。

           


## 准备工作

~~~
Python >= 3.9.0 (推荐3.9+版本)
nodejs >= 14.0 (推荐最新)
Mysql >= 5.7.0 (可选，默认数据库sqlite3，推荐8.0版本)
Redis(可选，最新版)
~~~


### 访问项目

- 访问地址：[http://localhost:8080](http://localhost:8080) (默认为此地址，如有修改请按照配置文件)
