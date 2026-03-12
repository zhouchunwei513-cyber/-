[app]
title = 公寓管理系统
package.name = apartmentmanager
version = 1.0
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.main.py = apartment_app.py
source.include_patterns = assets/*,images/*,fonts/*

# 安卓配置
android.ndk = 25b
android.sdk = 24
android.api = 33
android.ndk_api = 21
android.build_tools = 33.0.0
android.arch = arm64-v8a
android.orientation = landscape
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET
android.add_android_assets = True

# 依赖
requirements = python3,kivy==2.3.0,plyer,python-dateutil
# 国内源加速（可选）
# android.ndk_url = https://mirrors.tuna.tsinghua.edu.cn/android-ndk/android-ndk-r25b/android-ndk-r25b-linux.zip
# android.sdk_url = https://mirrors.tuna.tsinghua.edu.cn/android-sdk/android-sdk_r24.4.1-linux.tgz

# 其他配置
log_level = 2
warn_on_root = 1

# 强制使用本地源码，跳过远程克隆
p4a.source_dir = ~/.buildozer/android/platform/python-for-android
