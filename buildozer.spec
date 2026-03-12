[app]
title = ApartmentApp
package.name = apartment
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# 核心配置
requirements = python3,kivy
orientation = landscape
osx.python_version = 3
osx.kivy_version = 2.2.0

# Android 配置（修复版）
android.api = 33
android.archs = arm64-v8a,armeabi-v7a
android.sdk = 33
android.ndk = 25b
android.gradle_dependencies =
android.add_libs_armeabi_v7a =
android.add_libs_arm64_v8a =
android.buildtools = 33.0.2
android.use_aapt2 = True

# 权限（按需添加）
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# 打包输出
package.debug = True
