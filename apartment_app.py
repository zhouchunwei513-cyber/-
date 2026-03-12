import kivy
kivy.require('2.3.0')
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.checkbox import CheckBox
from kivy.utils import platform
from kivy.core.window import Window
import json
import os
from datetime import datetime, timedelta
import calendar

# ===================== 全局配置与数据适配 =====================
# 适配安卓文件路径
if platform == 'android':
    from android.storage import app_storage_path
    DATA_FILE = os.path.join(app_storage_path(), "apartment_data.json")
else:
    DATA_FILE = "apartment_data.json"

# 颜色配置
COLOR_SUCCESS = (0.18, 0.73, 0.44, 1)    # 绿色（空房）
COLOR_WARNING = (0.94, 0.62, 0.13, 1)    # 黄色（包房）
COLOR_DANGER = (0.92, 0.26, 0.24, 1)     # 红色（合租）
COLOR_PRIMARY = (0.18, 0.30, 0.49, 1)    # 深蓝
COLOR_LIGHT = (0.93, 0.95, 0.96, 1)      # 浅灰

# ===================== 数据操作（完整复用+安卓适配） =====================
def init_data():
    """初始化数据：4/5/6楼24间，1/2/3楼20间"""
    data = {"rooms": [], "records": []}
    for floor in range(1, 7):
        room_num = 24 if floor in [4,5,6] else 20
        for num in range(1, room_num + 1):
            room_id = f"{floor}{num:02d}"
            data["rooms"].append({
                "room_id": room_id,
                "floor": floor,
                "status": "空房",
                "tenants": [
                    {"name": "", "phone": "", "id_card": "", "check_in_date": ""},
                    {"name": "", "phone": "", "id_card": "", "check_in_date": ""}
                ],
                "rent": 0.0,
                "deposit": 0.0,
                "deposit_status": "未交",
                "arrears": 0.0
            })
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"初始化数据失败：{e}")
    return data

def load_data():
    """加载数据，兼容旧数据"""
    if not os.path.exists(DATA_FILE):
        return init_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 补全缺失字段
        if "records" not in data:
            data["records"] = []
        for room in data["rooms"]:
            if "tenants" not in room:
                room["tenants"] = [{"name": "", "phone": "", "id_card": "", "check_in_date": ""}] * 2
            for t in room["tenants"]:
                if "check_in_date" not in t:
                    t["check_in_date"] = ""
                if "id_card" not in t:
                    t["id_card"] = ""
            if "deposit_status" not in room:
                room["deposit_status"] = "未交"
            if "arrears" not in room:
                room["arrears"] = 0.0
        return data
    except Exception as e:
        print(f"加载数据失败，重新初始化：{e}")
        return init_data()

def save_data(data):
    """保存数据到文件"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"保存数据失败：{e}")
        return False

# ===================== 弹窗组件（安卓适配） =====================
class InputPopup(Popup):
    """通用输入弹窗"""
    def __init__(self, title, hint, input_type="text", min_val=None, max_val=None, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.size_hint = (0.8, 0.5)
        self.callback = callback
        self.min_val = min_val
        self.max_val = max_val

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.input = TextInput(
            hint_text=hint,
            input_filter=input_type if input_type != "text" else None,
            multiline=False
        )
        if input_type == "int":
            self.input.input_filter = "int"
        elif input_type == "float":
            self.input.input_filter = "float"
        
        layout.add_widget(self.input)
        
        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        confirm_btn = Button(text="确认", background_color=COLOR_SUCCESS)
        cancel_btn = Button(text="取消", background_color=COLOR_DANGER)
        
        confirm_btn.bind(on_press=self.on_confirm)
        cancel_btn.bind(on_press=self.dismiss)
        
        btn_layout.add_widget(confirm_btn)
        btn_layout.add_widget(cancel_btn)
        
        layout.add_widget(btn_layout)
        self.content = layout

    def on_confirm(self, *args):
        try:
            value = self.input.text
            if self.min_val is not None and self.max_val is not None:
                if self.input.input_filter == "int":
                    value = int(value)
                    if not (self.min_val <= value <= self.max_val):
                        self.show_error(f"请输入{self.min_val}-{self.max_val}之间的数值")
                        return
                elif self.input.input_filter == "float":
                    value = float(value)
                    if value < self.min_val:
                        self.show_error(f"请输入不小于{self.min_val}的数值")
                        return
            if self.callback:
                self.callback(value)
            self.dismiss()
        except ValueError:
            self.show_error("请输入有效的数值")

    def show_error(self, msg):
        error_popup = Popup(title="错误", content=Label(text=msg), size_hint=(0.7, 0.3))
        error_popup.open()

class SelectPopup(Popup):
    """选择弹窗（用于选择租客）"""
    def __init__(self, title, options, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.size_hint = (0.8, 0.6)
        self.callback = callback
        self.selected = None

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        scroll = ScrollView()
        option_layout = GridLayout(cols=1, size_hint_y=None, spacing=5)
        option_layout.bind(minimum_height=option_layout.setter('height'))
        
        for i, (label, value) in enumerate(options):
            btn = Button(
                text=label, 
                size_hint_y=None, 
                height=60,
                background_color=COLOR_PRIMARY
            )
            btn.bind(on_press=lambda x, v=value: self.select_option(v))
            option_layout.add_widget(btn)
        
        scroll.add_widget(option_layout)
        layout.add_widget(scroll)
        
        confirm_btn = Button(text="确认选择", size_hint_y=0.2, background_color=COLOR_SUCCESS)
        confirm_btn.bind(on_press=self.on_confirm)
        layout.add_widget(confirm_btn)
        
        self.content = layout

    def select_option(self, value):
        self.selected = value

    def on_confirm(self, *args):
        if self.selected is not None and self.callback:
            self.callback(self.selected)
        self.dismiss()

class ConfirmPopup(Popup):
    """确认弹窗"""
    def __init__(self, title, message, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.size_hint = (0.8, 0.4)
        self.callback = callback

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        layout.add_widget(Label(text=message))
        
        btn_layout = BoxLayout(size_hint_y=0.4, spacing=10)
        yes_btn = Button(text="是", background_color=COLOR_SUCCESS)
        no_btn = Button(text="否", background_color=COLOR_DANGER)
        
        yes_btn.bind(on_press=lambda x: self.on_confirm(True))
        no_btn.bind(on_press=lambda x: self.on_confirm(False))
        
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        
        layout.add_widget(btn_layout)
        self.content = layout

    def on_confirm(self, result):
        if self.callback:
            self.callback(result)
        self.dismiss()

# ===================== 主界面布局 =====================
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = load_data()
        self.current_room = None
        
        # 主布局
        main_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        # 1. 标题
        main_layout.add_widget(Label(text="公寓管理系统", font_size=28, bold=True, size_hint_y=0.1))
        
        # 2. 楼层选择
        floor_layout = BoxLayout(size_hint_y=0.1, spacing=5)
        for floor in range(1, 7):
            btn = Button(
                text=f"{floor}楼", 
                background_color=COLOR_PRIMARY,
                on_press=lambda x, f=floor: self.show_floor(f)
            )
            floor_layout.add_widget(btn)
        main_layout.add_widget(floor_layout)
        
        # 3. 房间列表（滚动视图）
        self.room_scroll = ScrollView()
        self.room_grid = GridLayout(cols=3, size_hint_y=None, spacing=5)
        self.room_grid.bind(minimum_height=self.room_grid.setter('height'))
        self.room_scroll.add_widget(self.room_grid)
        main_layout.add_widget(self.room_scroll)
        
        # 4. 当前房间信息
        info_layout = BoxLayout(orientation="vertical", size_hint_y=0.2, spacing=10)
        self.room_label = Label(text="未选择房间", font_size=20, bold=True)
        info_layout.add_widget(self.room_label)
        
        # 状态选择
        self.status_spinner = Spinner(
            text='空房', 
            values=['空房', '包房', '合租（2人）', '合租（空1床位）'],
            size_hint_y=0.25,
            on_text=self.on_status_change
        )
        info_layout.add_widget(self.status_spinner)
        
        # 租金和欠费显示
        rent_layout = BoxLayout(size_hint_y=0.25, spacing=10)
        rent_layout.add_widget(Label(text="月租金："))
        self.rent_input = TextInput(hint_text="0.0", input_filter="float", size_hint_x=0.7)
        rent_layout.add_widget(self.rent_input)
        info_layout.add_widget(rent_layout)
        
        arrears_layout = BoxLayout(size_hint_y=0.25, spacing=10)
        arrears_layout.add_widget(Label(text="当前欠费："))
        self.arrears_label = Label(text="0.00元", color=COLOR_DANGER)
        arrears_layout.add_widget(self.arrears_label)
        info_layout.add_widget(arrears_layout)
        
        main_layout.add_widget(info_layout)
        
        # 5. 功能按钮区
        btn_layout1 = BoxLayout(size_hint_y=0.15, spacing=5)
        btn_layout1.add_widget(Button(text="保存信息", background_color=COLOR_SUCCESS, on_press=self.save_room))
        btn_layout1.add_widget(Button(text="入住缴费", background_color=COLOR_PRIMARY, on_press=self.pay_checkin))
        btn_layout1.add_widget(Button(text="在住缴费", background_color=COLOR_PRIMARY, on_press=self.pay_stay))
        main_layout.add_widget(btn_layout1)
        
        btn_layout2 = BoxLayout(size_hint_y=0.15, spacing=5)
        btn_layout2.add_widget(Button(text="退房结算", background_color=COLOR_WARNING, on_press=self.check_out))
        btn_layout2.add_widget(Button(text="押金退款", background_color=COLOR_WARNING, on_press=self.refund_deposit))
        btn_layout2.add_widget(Button(text="重置房间", background_color=COLOR_DANGER, on_press=self.reset_room))
        main_layout.add_widget(btn_layout2)
        
        btn_layout3 = BoxLayout(size_hint_y=0.1, spacing=5)
        btn_layout3.add_widget(Button(text="欠费统计", background_color=COLOR_PRIMARY, on_press=self.show_arrears_stats))
        btn_layout3.add_widget(Button(text="缴费记录", background_color=COLOR_PRIMARY, on_press=self.show_records))
        btn_layout3.add_widget(Button(text="手动收租提醒", background_color=COLOR_DANGER, on_press=self.manual_reminder))
        main_layout.add_widget(btn_layout3)
        
        self.add_widget(main_layout)
        
        # 初始化显示1楼
        self.show_floor(1)

    def show_floor(self, floor):
        """显示指定楼层房间"""
        self.room_grid.clear_widgets()
        rooms = sorted([r for r in self.data["rooms"] if r["floor"] == floor], key=lambda x: int(x["room_id"]))
        
        for room in rooms:
            # 设置房间按钮颜色
            if room["status"] == "空房":
                bg_color = COLOR_SUCCESS
            elif room["status"] == "包房":
                bg_color = COLOR_WARNING
            else:
                bg_color = COLOR_DANGER
            
            # 按钮文本
            t1 = room["tenants"][0]["name"][:4] if room["tenants"][0]["name"] else ""
            t2 = room["tenants"][1]["name"][:4] if room["tenants"][1]["name"] else ""
            text = f"{room['room_id']}\n{room['status']}"
            if t1:
                text += f"\n{t1}"
            if t2:
                text += f"|{t2}"
            
            btn = Button(
                text=text,
                size_hint_y=None,
                height=100,
                background_color=bg_color,
                on_press=lambda x, r=room: self.select_room(r)
            )
            self.room_grid.add_widget(btn)

    def select_room(self, room):
        """选中房间加载信息"""
        self.current_room = room
        self.room_label.text = f"当前房间：{room['room_id']}"
        self.status_spinner.text = room["status"]
        self.rent_input.text = str(room["rent"])
        self.arrears_label.text = f"{room['arrears']:.2f}元"

    def on_status_change(self, *args):
        """房间状态变更联动设置默认租金"""
        status = self.status_spinner.text
        if status == "空房":
            self.rent_input.text = "0"
        elif status == "包房":
            self.rent_input.text = "460"
        elif "合租" in status:
            self.rent_input.text = "230"

    def save_room(self, *args):
        """保存房间信息"""
        if not self.current_room:
            Popup(title="提示", content=Label(text="请先选择房间！"), size_hint=(0.7, 0.3)).open()
            return
        
        try:
            room = self.current_room
            room["status"] = self.status_spinner.text
            room["rent"] = float(self.rent_input.text or 0)
            
            if save_data(self.data):
                Popup(title="成功", content=Label(text="房间信息保存成功！"), size_hint=(0.7, 0.3)).open()
                self.show_floor(self.current_room["floor"])
            else:
                Popup(title="失败", content=Label(text="保存失败，请重试！"), size_hint=(0.7, 0.3)).open()
        except Exception as e:
            Popup(title="错误", content=Label(text=f"保存失败：{str(e)}"), size_hint=(0.7, 0.3)).open()

    def get_payer(self):
        """获取缴费人（返回租客姓名和标识）"""
        if not self.current_room:
            return None
        
        status = self.current_room["status"]
        t1 = self.current_room["tenants"][0]["name"].strip()
        t2 = self.current_room["tenants"][1]["name"].strip()
        
        if status == "包房":
            if not t1:
                Popup(title="提示", content=Label(text="请先填写租客1姓名！"), size_hint=(0.7, 0.3)).open()
                return None
            return (t1, f"租客1({t1})")
        
        if "合租" in status:
            options = []
            if t1:
                options.append((f"租客1：{t1}", (t1, f"租客1({t1})")))
            if t2:
                options.append((f"租客2：{t2}", (t2, f"租客2({t2})")))
            
            if not options:
                Popup(title="提示", content=Label(text="请先填写租客姓名！"), size_hint=(0.7, 0.3)).open()
                return None
            
            def on_select(selected):
                self.payer_selected = selected
            
            self.payer_selected = None
            select_popup = SelectPopup(title="选择缴费人", options=options, callback=on_select)
            select_popup.open()
            
            # 等待选择
            while select_popup.is_open:
                pass
            
            return self.payer_selected
        
        return None

    def pay_checkin(self, *args):
        """入住缴费"""
        if not self.current_room or self.current_room["status"] == "空房":
            Popup(title="提示", content=Label(text="空房无法进行入住缴费！"), size_hint=(0.7, 0.3)).open()
            return
        
        payer = self.get_payer()
        if not payer:
            return
        
        # 输入缴费月数
        def on_months_input(months):
            months = int(months)
            
            # 输入押金
            def on_deposit_input(deposit):
                deposit = float(deposit)
                
                # 选择是否缴纳暖气费
                def on_heating_confirm(confirm):
                    heating_fee = 100 if self.current_room["status"] == "包房" else 50 if confirm else 0
                    rent = self.current_room["rent"]
                    rent_amount = rent * months
                    total = rent_amount + deposit + heating_fee
                    
                    # 确认缴费
                    def on_pay_confirm(confirm):
                        if confirm:
                            # 更新房间信息
                            self.current_room["deposit"] = deposit
                            self.current_room["deposit_status"] = "已交"
                            self.current_room["arrears"] = max(0, self.current_room["arrears"] - rent_amount)
                            
                            # 保存缴费记录
                            self.data["records"].append({
                                "room": self.current_room["room_id"],
                                "payer": payer[1],
                                "type": "入住缴费",
                                "rent_month": months,
                                "rent_amount": rent_amount,
                                "deposit": deposit,
                                "heating": heating_fee,
                                "total": total,
                                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            
                            if save_data(self.data):
                                Popup(title="成功", content=Label(text=f"缴费完成！总计：{total:.2f}元"), size_hint=(0.7, 0.3)).open()
                                self.arrears_label.text = f"{self.current_room['arrears']:.2f}元"
                            else:
                                Popup(title="失败", content=Label(text="缴费记录保存失败！"), size_hint=(0.7, 0.3)).open()
                    
                    confirm_popup = ConfirmPopup(
                        title="确认缴费",
                        message=f"总计金额：{total:.2f}元\n房租：{rent_amount:.2f}元\n押金：{deposit:.2f}元\n暖气费：{heating_fee:.2f}元",
                        callback=on_pay_confirm
                    )
                    confirm_popup.open()
                
                confirm_popup = ConfirmPopup(title="暖气费", message="是否缴纳暖气费？", callback=on_heating_confirm)
                confirm_popup.open()
            
            deposit_popup = InputPopup(
                title="押金金额",
                hint="请输入押金金额（元）",
                input_type="float",
                min_val=0,
                callback=on_deposit_input
            )
            deposit_popup.open()
        
        months_popup = InputPopup(
            title="缴费月数",
            hint="请输入缴费月数（1-12）",
            input_type="int",
            min_val=1,
            max_val=12,
            callback=on_months_input
        )
        months_popup.open()

    def pay_stay(self, *args):
        """在住缴费"""
        if not self.current_room or self.current_room["status"] == "空房":
            Popup(title="提示", content=Label(text="空房无法进行在住缴费！"), size_hint=(0.7, 0.3)).open()
            return
        
        payer = self.get_payer()
        if not payer:
            return
        
        # 输入缴费月数
        def on_months_input(months):
            months = int(months)
            
            # 选择是否缴纳暖气费
            def on_heating_confirm(confirm):
                heating_fee = 100 if self.current_room["status"] == "包房" else 50 if confirm else 0
                rent = self.current_room["rent"]
                rent_amount = rent * months
                total = rent_amount + heating_fee
                
                # 确认缴费
                def on_pay_confirm(confirm):
                    if confirm:
                        # 更新欠费
                        self.current_room["arrears"] = max(0, self.current_room["arrears"] - rent_amount)
                        
                        # 保存缴费记录
                        self.data["records"].append({
                            "room": self.current_room["room_id"],
                            "payer": payer[1],
                            "type": "在住缴费",
                            "rent_month": months,
                            "rent_amount": rent_amount,
                            "deposit": 0,
                            "heating": heating_fee,
                            "total": total,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        if save_data(self.data):
                            Popup(title="成功", content=Label(text=f"缴费完成！总计：{total:.2f}元"), size_hint=(0.7, 0.3)).open()
                            self.arrears_label.text = f"{self.current_room['arrears']:.2f}元"
                        else:
                            Popup(title="失败", content=Label(text="缴费记录保存失败！"), size_hint=(0.7, 0.3)).open()
                
                confirm_popup = ConfirmPopup(
                    title="确认缴费",
                    message=f"总计金额：{total:.2f}元\n房租：{rent_amount:.2f}元\n暖气费：{heating_fee:.2f}元",
                    callback=on_pay_confirm
                )
                confirm_popup.open()
            
            confirm_popup = ConfirmPopup(title="暖气费", message="是否缴纳暖气费？", callback=on_heating_confirm)
            confirm_popup.open()
        
        months_popup = InputPopup(
            title="缴费月数",
            hint="请输入缴费月数（1-12）",
            input_type="int",
            min_val=1,
            max_val=12,
            callback=on_months_input
        )
        months_popup.open()

    def check_out(self, *args):
        """退房结算"""
        if not self.current_room:
            return
        
        status = self.current_room["status"]
        if status == "空房":
            Popup(title="提示", content=Label(text="该房间已是空房！"), size_hint=(0.7, 0.3)).open()
            return
        
        # 选择退房人
        if status == "包房":
            tenant_idx = 0
            tenant_name = self.current_room["tenants"][0]["name"]
            if not tenant_name:
                Popup(title="提示", content=Label(text="请填写租客1姓名！"), size_hint=(0.7, 0.3)).open()
                return
            self.process_checkout(tenant_idx, tenant_name)
        else:
            # 列出可用租客
            options = []
            if self.current_room["tenants"][0]["name"]:
                options.append((f"租客1：{self.current_room['tenants'][0]['name']}", 0))
            if self.current_room["tenants"][1]["name"]:
                options.append((f"租客2：{self.current_room['tenants'][1]['name']}", 1))
            
            if not options:
                Popup(title="提示", content=Label(text="该房间无在住租客！"), size_hint=(0.7, 0.3)).open()
                return
            
            def on_select(tenant_idx):
                tenant_name = self.current_room["tenants"][tenant_idx]["name"]
                self.process_checkout(tenant_idx, tenant_name)
            
            select_popup = SelectPopup(title="选择退房人", options=options, callback=on_select)
            select_popup.open()

    def process_checkout(self, tenant_idx, tenant_name):
        """处理退房逻辑"""
        # 检查入住日期
        check_in_date = self.current_room["tenants"][tenant_idx].get("check_in_date")
        if not check_in_date:
            Popup(title="提示", content=Label(text=f"租客{tenant_idx+1}未填写入住日期！"), size_hint=(0.7, 0.3)).open()
            return
        
        try:
            # 计算入住天数和费用
            cid = datetime.strptime(check_in_date, "%Y-%m-%d")
            days = (datetime.now() - cid).days
            rent = self.current_room["rent"]
            fee = rent if days > 15 else rent / 2
            
            # 确认退房
            def on_confirm(confirm):
                if confirm:
                    # 保存退房记录
                    if fee > 0:
                        self.data["records"].append({
                            "room": self.current_room["room_id"],
                            "payer": f"{tenant_name}（退房）",
                            "type": "退房缴费",
                            "rent_month": 0.5 if days <= 15 else 1,
                            "rent_amount": fee,
                            "deposit": 0,
                            "heating": 0,
                            "total": fee,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        # 更新欠费
                        self.current_room["arrears"] = max(0, self.current_room["arrears"] - fee)
                    
                    # 清空租客信息
                    self.current_room["tenants"][tenant_idx] = {
                        "name": "", "phone": "", "id_card": "", "check_in_date": ""
                    }
                    
                    # 更新房间状态
                    remaining = 0
                    if self.current_room["tenants"][0]["name"]:
                        remaining += 1
                    if self.current_room["tenants"][1]["name"]:
                        remaining += 1
                    
                    if self.current_room["status"] == "包房":
                        self.current_room["status"] = "空房"
                        self.current_room["arrears"] = 0
                    elif self.current_room["status"] == "合租（2人）":
                        self.current_room["status"] = "合租（空1床位）"
                    elif self.current_room["status"] == "合租（空1床位）":
                        self.current_room["status"] = "空房"
                        self.current_room["arrears"] = 0
                    
                    # 更新押金状态
                    if self.current_room.get("deposit_status") == "已交":
                        self.current_room["deposit_status"] = "待退款"
                    
                    # 保存数据
                    if save_data(self.data):
                        Popup(title="成功", content=Label(text=f"{tenant_name}退房完成！费用：{fee:.2f}元"), size_hint=(0.7, 0.3)).open()
                        self.show_floor(self.current_room["floor"])
                        self.select_room(self.current_room)
                    else:
                        Popup(title="失败", content=Label(text="退房记录保存失败！"), size_hint=(0.7, 0.3)).open()
            
            confirm_popup = ConfirmPopup(
                title="退房结算",
                message=f"{tenant_name}\n入住天数：{days}天\n需缴费用：{fee:.2f}元\n是否确认退房？",
                callback=on_confirm
            )
            confirm_popup.open()
        except Exception as e:
            Popup(title="错误", content=Label(text=f"退房失败：{str(e)}"), size_hint=(0.7, 0.3)).open()

    def refund_deposit(self, *args):
        """押金退款"""
        if not self.current_room:
            return
        
        deposit_status = self.current_room.get("deposit_status")
        if deposit_status != "待退款":
            Popup(title="提示", content=Label(text="该房间无待退款押金！"), size_hint=(0.7, 0.3)).open()
            return
        
        deposit = self.current_room["deposit"]
        
        def on_confirm(confirm):
            if confirm:
                self.current_room["deposit_status"] = "已退款"
                
                # 保存退款记录
                self.data["records"].append({
                    "room": self.current_room["room_id"],
                    "payer": "押金退款",
                    "type": "退款记录",
                    "rent_month": 0,
                    "rent_amount": 0,
                    "deposit": -deposit,
                    "heating": 0,
                    "total": -deposit,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                if save_data(self.data):
                    Popup(title="成功", content=Label(text=f"押金退款完成！金额：{deposit:.2f}元"), size_hint=(0.7, 0.3)).open()
                else:
                    Popup(title="失败", content=Label(text="退款记录保存失败！"), size_hint=(0.7, 0.3)).open()
        
        confirm_popup = ConfirmPopup(
            title="押金退款",
            message=f"押金金额：{deposit:.2f}元\n是否确认退款？",
            callback=on_confirm
        )
        confirm_popup.open()

    def reset_room(self, *args):
        """重置房间"""
        if not self.current_room:
            return
        
        def on_confirm(confirm):
            if confirm:
                # 重置房间信息
                self.current_room.update({
                    "status": "空房",
                    "tenants": [{"name": "", "phone": "", "id_card": "", "check_in_date": ""}] * 2,
                    "rent": 0.0,
                    "deposit": 0.0,
                    "deposit_status": "未交",
                    "arrears": 0.0
                })
                
                if save_data(self.data):
                    Popup(title="成功", content=Label(text="房间已重置为初始状态！"), size_hint=(0.7, 0.3)).open()
                    self.show_floor(self.current_room["floor"])
                    self.select_room(self.current_room)
                else:
                    Popup(title="失败", content=Label(text="重置房间失败！"), size_hint=(0.7, 0.3)).open()
        
        confirm_popup = ConfirmPopup(
            title="重置房间",
            message="确认清空该房间所有信息？",
            callback=on_confirm
        )
        confirm_popup.open()

    def show_arrears_stats(self, *args):
        """显示欠费统计"""
        stats_text = "房间欠费统计\n\n"
        total_arrears = 0
        
        for room in self.data["rooms"]:
            if room["status"] != "空房" and room["arrears"] > 0:
                stats_text += f"{room['room_id']} | {room['status']} | 欠费：{room['arrears']:.2f}元\n"
                total_arrears += room["arrears"]
        
        stats_text += f"\n全楼总欠费：{total_arrears:.2f}元"
        
        # 显示统计弹窗
        popup = Popup(
            title="欠费统计",
            content=ScrollView(content=Label(text=stats_text, font_size=14)),
            size_hint=(0.9, 0.8)
        )
        popup.open()

    def show_records(self, *args):
        """显示缴费记录"""
        records_text = "缴费记录\n\n"
        
        for rec in reversed(self.data["records"]):  # 倒序显示最新记录
            records_text += (
                f"房间：{rec['room']} | 缴费人：{rec['payer']} | 类型：{rec['type']}\n"
                f"金额：{rec['total']:.2f}元 | 时间：{rec['time']}\n\n"
            )
        
        if not self.data["records"]:
            records_text += "暂无缴费记录"
        
        # 显示记录弹窗
        popup = Popup(
            title="缴费记录",
            content=ScrollView(content=Label(text=records_text, font_size=12)),
            size_hint=(0.9, 0.8)
        )
        popup.open()

    def manual_reminder(self, *args):
        """手动收租提醒"""
        reminder_text = "当前欠费房间提醒\n\n"
        has_arrears = False
        
        for room in self.data["rooms"]:
            if room["status"] != "空房" and room["arrears"] > 0:
                reminder_text += f"{room['room_id']} | {room['status']} | 欠费：{room['arrears']:.2f}元\n"
                has_arrears = True
        
        if not has_arrears:
            reminder_text += "暂无欠费房间！"
        
        Popup(title="收租提醒", content=Label(text=reminder_text), size_hint=(0.9, 0.7)).open()

# ===================== 应用入口 =====================
class ApartmentApp(App):
    def build(self):
        # 设置窗口大小（适配安卓）
        if platform != 'android':
            Window.size = (800, 1200)
        
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        return sm

if __name__ == "__main__":
    ApartmentApp().run()
