import logging
import requests
import json
import re
import random
import datetime
import io
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram.constants import ParseMode
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8384709837:AAEGhILHFcnOt-2SrCSCow-3-q2affWod9A"
ADMIN_IDS = [8228439601, 7195018532]
CHANNEL_USERNAME = "@YSXCDPD"
GROUP_USERNAME = "@YSXCDQZ"

CAR_API_URL = "https://ovo1.cc/api/car.php"
IP_QUERY_API = "https://api.kona.uno/API/ipdt.php?ip={}"
ZFM_API_URL = "https://api.kona.uno/API/sfzzf.php?name={}&id={}&apikey=@Liuzi0822"
CZC_API_URL = "https://api.kona.uno/API/clzc.php"
DY1_API_URL = "https://www.mxnzp.com/api/idcard/search"
DY1_APP_ID = "eamrfsnpkngzpgzh"
DY1_APP_SECRET = "6v1j7eBbVVWpzLKQaJyHHgOIs56pcufd"
DW2_API_URL = "https://api.pearktrue.cn/api/baidumap/"
SGC_API_URL = "https://qingfeng.qzz.io/api/black?text={}&key=tiyanka"
GWC_API_URL = "http://qingfeng.qzz.io/api/heiheplus?text={}&key=kimodddddddd"

EMOJIS = {
    "home": "🏠", "search": "🔍", "car": "🚗", "location": "📍",
    "id_card": "🪪", "ip": "🌐", "admin": "⚙️", "user": "👤",
    "lock": "🔒", "unlock": "🔓", "file": "📄", "warning": "⚠️",
    "success": "✅", "error": "❌", "info": "ℹ️", "back": "↩️",
    "refresh": "🔄", "stats": "📊", "help": "❓", "download": "📥",
    "clock": "⏱️", "shield": "🛡️", "phone": "📱", "map": "🗺️",
    "database": "💾", "network": "📡", "scan": "📸", "verify": "✅",
    "ban": "🚫", "group": "👥", "channel": "📢", "menu": "📋",
    "copy": "📋", "robot": "🤖", "id_verify": "🔐"
}

WATERMARK_KEYWORDS = [
    "小权专属API水印", "小虫api网站：https://ovo1.cc/", "admin", "小虫api",
    "api_source", "官方API网", "https://api.pearktrue.cn/", "https://api.kona.uno/",
    "https://api.icofun.cn/", "https://www.mxnzp.com/", "https://www.cunyuapi.top/",
    "apikey", "API密钥", "接口来源", "数据来源：API", "©", "版权所有",
    "妹情API", "毒蝎工作室", "@SCORPION7500", "水印: 妹情API", "技术支持: 毒蝎工作室",
    "------------------------", "水印:", "技术支持:", "联系:", "----------------",
    "------", "***", "======", "####", "++++++", "~~~~~~~~", "watermark:", "support:",
    "contact:", "Powered by", "API by", "数据来源", "本接口由", "查询结果", "常用号查询结果",
    "超级查询结果", "超级查询1.0结果", "", "", "厌世心公安出品水印标签"
]

class UserManager:
    def __init__(self):
        self.data = {}
        self.sgc_cooldown = {}
    
    def get_user_data(self, user_id):
        user_id_str = str(user_id)
        if user_id_str not in self.data:
            self.data[user_id_str] = {
                "is_banned": False,
                "username": "未获取到名称",
                "first_name": "",
                "last_name": "",
                "full_name": "",
                "last_active": datetime.datetime.now().isoformat(),
                "query_count": 0
            }
        return self.data[user_id_str]
    
    def update_user_info(self, user_id, username, first_name="", last_name=""):
        user_id_str = str(user_id)
        user_data = self.get_user_data(user_id)
        
        if username:
            user_data["username"] = username.strip()
        
        if first_name:
            user_data["first_name"] = first_name
        if last_name:
            user_data["last_name"] = last_name
        
        full_name = first_name or ""
        if last_name:
            full_name += f" {last_name}"
        user_data["full_name"] = full_name.strip()
        
        if not user_data["username"] or user_data["username"] == "未获取到名称":
            if full_name:
                user_data["username"] = full_name
            else:
                user_data["username"] = f"用户_{user_id}"
        
        user_data["last_active"] = datetime.datetime.now().isoformat()
    
    def increment_query_count(self, user_id):
        user_data = self.get_user_data(user_id)
        user_data["query_count"] = user_data.get("query_count", 0) + 1
    
    def is_banned(self, user_id):
        return self.get_user_data(user_id).get("is_banned", False)
    
    def ban_user(self, user_id):
        self.get_user_data(user_id)["is_banned"] = True
    
    def unban_user(self, user_id):
        self.get_user_data(user_id)["is_banned"] = False
    
    def is_admin(self, user_id):
        return user_id in ADMIN_IDS
    
    def get_user_statistics(self):
        user_count = len(self.data.keys())
        active_users = 0
        total_queries = 0
        user_list = []
        
        for user_id_str, user_info in self.data.items():
            user_queries = user_info.get("query_count", 0)
            total_queries += user_queries
            
            try:
                last_active = datetime.datetime.fromisoformat(user_info.get("last_active", ""))
                if (datetime.datetime.now() - last_active).days <= 7:
                    active_users += 1
            except:
                pass
            
            user_list.append({
                "user_id": user_id_str,
                "username": user_info.get("username", "未获取到名称"),
                "full_name": user_info.get("full_name", ""),
                "first_name": user_info.get("first_name", ""),
                "last_name": user_info.get("last_name", ""),
                "is_admin": self.is_admin(int(user_id_str)),
                "query_count": user_queries,
                "last_active": user_info.get("last_active", "未知")
            })
        
        user_list.sort(key=lambda x: x["query_count"], reverse=True)
        
        return user_count, active_users, total_queries, user_list
    
    def can_use_sgc(self, user_id):
        user_id_str = str(user_id)
        current_time = time.time()
        
        if user_id_str not in self.sgc_cooldown:
            self.sgc_cooldown[user_id_str] = current_time
            return True
        
        last_use_time = self.sgc_cooldown[user_id_str]
        if current_time - last_use_time >= 60:
            self.sgc_cooldown[user_id_str] = current_time
            return True
        else:
            return False
    
    def get_sgc_cooldown_remaining(self, user_id):
        user_id_str = str(user_id)
        current_time = time.time()
        
        if user_id_str not in self.sgc_cooldown:
            return 0
        
        last_use_time = self.sgc_cooldown[user_id_str]
        elapsed = current_time - last_use_time
        remaining = 60 - elapsed
        
        return max(0, int(remaining))

user_manager = UserManager()

def is_valid_id_card(id_card):
    if len(id_card) != 18:
        return False
    front_17 = id_card[:17]
    last_char = id_card[-1].upper()
    if not front_17.isdigit():
        return False
    if last_char not in '0123456789X':
        return False
    return True

def remove_watermarks(text):
    if not text:
        return ""
    
    cleaned_text = text.strip()
    for keyword in WATERMARK_KEYWORDS:
        cleaned_text = cleaned_text.replace(keyword, "")
    
    lines = cleaned_text.split('\n')
    filtered_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if re.match(r'^[-=*~#_]{3,}$', line):
            continue
        
        if any(keyword in line.lower() for keyword in ["水印", "技术支持", "联系", "contact", "support", "watermark", "powered", "api by", "数据来源", "查询结果", "常用号查询", "超级查询"]):
            continue
        
        if re.match(r'^(https?://|www\.)', line, re.IGNORECASE):
            continue
        
        filtered_lines.append(line)
    
    result = '\n'.join(filtered_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()

def clean_filename(query):
    safe_name = re.sub(r'[^\w\u4e00-\u9fa5\-]', '_', str(query))
    if len(safe_name) > 50:
        safe_name = safe_name[:50]
    return safe_name

async def send_as_txt_file(update: Update, query: str, content: str, prefix="查询结果"):
    try:
        safe_query = clean_filename(query)
        filename = f"{safe_query}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        file_content = f"=== 公网辅查系统 ===\n"
        file_content += f"查询内容: {query}\n"
        file_content += f"查询时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        file_content += f"查询类型: {prefix}\n"
        file_content += "=" * 40 + "\n\n"
        file_content += content
        
        file_obj = io.BytesIO(file_content.encode('utf-8'))
        file_obj.name = filename
        
        await update.message.reply_document(
            document=file_obj,
            caption=f"{EMOJIS['file']} <b>{prefix}</b>\n"
                   f"📁 文件名: <code>{filename}</code>\n"
                   f"⏱️ 生成时间: {datetime.datetime.now().strftime('%H:%M:%S')}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"发送TXT文件失败: {e}")
        await update.message.reply_text(
            f"{EMOJIS['error']} 发送文件失败: {str(e)[:50]}",
            parse_mode=ParseMode.HTML
        )

async def update_user_info(update: Update, context: CallbackContext):
    try:
        user = update.effective_user
        if not user:
            return
        
        username = f"@{user.username}" if user.username else ""
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        
        user_manager.update_user_info(user.id, username, first_name, last_name)
        
        logger.debug(f"更新用户信息：ID={user.id}, 用户名={username}, 全名={first_name} {last_name}")
    except Exception as e:
        logger.error(f"更新用户信息失败: {e}")

async def check_membership(update: Update, context: CallbackContext) -> bool:
    try:
        user_id = update.effective_user.id
        if user_id in ADMIN_IDS:
            return True
        for channel in [CHANNEL_USERNAME, GROUP_USERNAME]:
            try:
                member = await context.bot.get_chat_member(channel, user_id)
                if member.status in ['left', 'kicked']:
                    return False
            except Exception as e:
                logger.warning(f"检查频道 {channel} 失败: {e}")
                return False
        return True
    except Exception as e:
        logger.error(f"成员验证失败: {e}")
        return False

def create_membership_keyboard():
    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['channel']} 公安认证频道", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton(f"{EMOJIS['group']} 公安合规群组", url=f"https://t.me/{GROUP_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton(f"{EMOJIS['verify']} 已加入，点击验证", callback_data="check_membership")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_main_menu_keyboard(is_admin=False):
    if is_admin:
        keyboard = [
            [
                InlineKeyboardButton(f"{EMOJIS['car']} 车牌查询", callback_data="menu_car"),
                InlineKeyboardButton(f"{EMOJIS['ip']} IP查询", callback_data="menu_ip")
            ],
            [
                InlineKeyboardButton(f"{EMOJIS['location']} 定位生成", callback_data="menu_location"),
                InlineKeyboardButton(f"{EMOJIS['id_card']} 身份证", callback_data="menu_idcard")
            ],
            [
                InlineKeyboardButton(f"{EMOJIS['scan']} 车辆在场", callback_data="menu_car_check"),
                InlineKeyboardButton(f"{EMOJIS['search']} 社工查", callback_data="menu_sgc")
            ],
            [
                InlineKeyboardButton(f"{EMOJIS['map']} 定位关联", callback_data="menu_loc_relation"),
                InlineKeyboardButton(f"{EMOJIS['location']} 常用地查询", callback_data="menu_common_loc")
            ],
            [
                InlineKeyboardButton(f"{EMOJIS['search']} 公网查", callback_data="menu_gwc"),
                InlineKeyboardButton(f"{EMOJIS['stats']} 用户统计", callback_data="menu_stats")
            ],
            [
                InlineKeyboardButton(f"{EMOJIS['help']} 使用指令", callback_data="menu_help")
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(f"{EMOJIS['car']} 车牌查询", callback_data="menu_car"),
                InlineKeyboardButton(f"{EMOJIS['ip']} IP查询", callback_data="menu_ip")
            ],
            [
                InlineKeyboardButton(f"{EMOJIS['location']} 定位生成", callback_data="menu_location"),
                InlineKeyboardButton(f"{EMOJIS['id_card']} 身份证", callback_data="menu_idcard")
            ],
            [
                InlineKeyboardButton(f"{EMOJIS['scan']} 车辆在场", callback_data="menu_car_check"),
                InlineKeyboardButton(f"{EMOJIS['search']} 社工查", callback_data="menu_sgc")
            ],
            [
                InlineKeyboardButton(f"{EMOJIS['help']} 使用指令", callback_data="menu_help")
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def create_back_button():
    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['back']} 返回主菜单", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def check_user_access(update: Update, context: CallbackContext):
    try:
        await update_user_info(update, context)
        user_id = update.effective_user.id
        
        if user_manager.is_banned(user_id):
            await update.message.reply_text(
                f"{EMOJIS['ban']} <b>账户已被限制</b>\n\n"
                f"❌ 您的账户访问权限已被限制",
                parse_mode=ParseMode.HTML,
                reply_markup=create_back_button()
            )
            return False
        
        if not await check_membership(update, context):
            await update.message.reply_text(
                f"{EMOJIS['warning']} <b>需要验证</b>\n\n"
                f"请先加入认证频道及合规群组",
                parse_mode=ParseMode.HTML,
                reply_markup=create_membership_keyboard()
            )
            return False
        
        return True
    except Exception as e:
        logger.error(f"权限检查失败: {e}")
        await update.message.reply_text(
            f"{EMOJIS['error']} 系统权限检查异常",
            parse_mode=ParseMode.HTML
        )
        return False

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def start(update: Update, context: CallbackContext):
    try:
        user_id = update.effective_user.id
        await update_user_info(update, context)
        
        if user_manager.is_banned(user_id):
            await update.message.reply_text(
                f"{EMOJIS['ban']} <b>账户已被限制</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=create_back_button()
            )
            return
        
        if await check_membership(update, context):
            user_data = user_manager.get_user_data(user_id)
            username = user_data.get("username", "用户")
            query_count = user_data.get("query_count", 0)
            
            if is_admin(user_id):
                welcome_text = (
                    f"{EMOJIS['shield']} <b>公网辅查系统 - 管理员</b>\n\n"
                    f"{EMOJIS['user']} 欢迎：<code>{username}</code>\n"
                    f"{EMOJIS['database']} 查询次数：<b>{query_count}</b> 次\n"
                    f"{EMOJIS['clock']} 时间：{datetime.datetime.now().strftime('%H:%M:%S')}\n\n"
                    f"💡 请使用下方菜单按钮"
                )
            else:
                welcome_text = (
                    f"{EMOJIS['shield']} <b>公网辅查系统</b>\n\n"
                    f"{EMOJIS['user']} 欢迎：<code>{username}</code>\n"
                    f"{EMOJIS['database']} 查询次数：<b>{query_count}</b> 次\n\n"
                    f"🔍 <b>可用功能</b>\n"
                    f"• {EMOJIS['car']} 车牌信息查询\n"
                    f"• {EMOJIS['ip']} IP地址查询\n"
                    f"• {EMOJIS['location']} 定位链生成\n"
                    f"• {EMOJIS['id_card']} 身份证正反面\n"
                    f"• {EMOJIS['scan']} 车辆在场查询\n"
                    f"• {EMOJIS['search']} 社工查\n\n"
                    f"⚠️ 请合法使用"
                )
            
            await update.message.reply_text(
                welcome_text,
                parse_mode=ParseMode.HTML,
                reply_markup=create_main_menu_keyboard(is_admin(user_id))
            )
        else:
            await update.message.reply_text(
                f"{EMOJIS['warning']} <b>需要验证</b>\n\n"
                f"请先加入认证频道及合规群组",
                parse_mode=ParseMode.HTML,
                reply_markup=create_membership_keyboard()
            )
    except Exception as e:
        logger.error(f"start命令失败: {e}")
        await update.message.reply_text(
            f"{EMOJIS['error']} 系统启动异常",
            parse_mode=ParseMode.HTML
        )

async def menu_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    is_admin_user = is_admin(user_id)
    
    if query.data == "check_membership":
        if await check_membership(update, context):
            await query.edit_message_text(
                f"{EMOJIS['success']} <b>验证通过！</b>\n\n"
                f"✅ 已解锁全部查询功能",
                parse_mode=ParseMode.HTML,
                reply_markup=create_main_menu_keyboard(is_admin_user)
            )
        else:
            await query.edit_message_text(
                f"{EMOJIS['warning']} <b>验证未通过</b>\n\n"
                f"请先完成频道和群组加入",
                parse_mode=ParseMode.HTML,
                reply_markup=create_membership_keyboard()
            )
        return
    
    elif query.data == "menu_main":
        try:
            user_id = query.from_user.id
            await update_user_info(update, context)
            
            if user_manager.is_banned(user_id):
                await query.edit_message_text(
                    f"{EMOJIS['ban']} <b>账户已被限制</b>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=create_back_button()
                )
                return
            
            if await check_membership(update, context):
                user_data = user_manager.get_user_data(user_id)
                username = user_data.get("username", "用户")
                query_count = user_data.get("query_count", 0)
                
                if is_admin_user:
                    welcome_text = (
                        f"{EMOJIS['shield']} <b>公网辅查系统 - 管理员</b>\n\n"
                        f"{EMOJIS['user']} 欢迎：<code>{username}</code>\n"
                        f"{EMOJIS['database']} 查询次数：<b>{query_count}</b> 次\n"
                        f"{EMOJIS['clock']} 时间：{datetime.datetime.now().strftime('%H:%M:%S')}\n\n"
                        f"💡 请使用下方菜单按钮"
                    )
                else:
                    welcome_text = (
                        f"{EMOJIS['shield']} <b>公网辅查系统</b>\n\n"
                        f"{EMOJIS['user']} 欢迎：<code>{username}</code>\n"
                        f"{EMOJIS['database']} 查询次数：<b>{query_count}</b> 次\n\n"
                        f"🔍 <b>可用功能</b>\n"
                        f"• {EMOJIS['car']} 车牌信息查询\n"
                        f"• {EMOJIS['ip']} IP地址查询\n"
                        f"• {EMOJIS['location']} 定位链生成\n"
                        f"• {EMOJIS['id_card']} 身份证正反面\n"
                        f"• {EMOJIS['scan']} 车辆在场查询\n"
                        f"• {EMOJIS['search']} 社工查\n\n"
                        f"⚠️ 请合法使用"
                    )
                
                await query.edit_message_text(
                    welcome_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=create_main_menu_keyboard(is_admin_user)
                )
            else:
                await query.edit_message_text(
                    f"{EMOJIS['warning']} <b>需要验证</b>\n\n"
                    f"请先加入认证频道及合规群组",
                    parse_mode=ParseMode.HTML,
                    reply_markup=create_membership_keyboard()
                )
        except Exception as e:
            logger.error(f"返回主菜单失败: {e}")
            await query.edit_message_text(
                f"{EMOJIS['error']} 返回主菜单失败",
                parse_mode=ParseMode.HTML
            )
        return
    
    menu_handlers = {
        "menu_car": f"{EMOJIS['car']} <b>车牌查询</b>\n\n格式：<code>/QGC 车牌号</code>\n示例：<code>/QGC 京A88888</code>",
        "menu_ip": f"{EMOJIS['ip']} <b>IP查询</b>\n\n格式：<code>/IP IP地址</code>\n示例：<code>/IP 114.114.114.114</code>",
        "menu_location": f"{EMOJIS['location']} <b>定位生成</b>\n\n格式：<code>/DW3 经度 纬度</code>\n示例：<code>/DW3 116.404 39.915</code>",
        "menu_idcard": f"{EMOJIS['id_card']} <b>身份证生成</b>\n\n格式：<code>/ZFM 姓名 身份证</code>\n示例：<code>/ZFM 张三 110101199003076716</code>",
        "menu_car_check": f"{EMOJIS['scan']} <b>车辆在场</b>\n\n格式：<code>/CZC 车牌号</code>\n示例：<code>/CZC 京A88888</code>",
        "menu_sgc": f"{EMOJIS['search']} <b>社工查</b>\n\n命令：<code>/SGC </code>\n示例：<code>/SGC 13800138000</code>或<code>/SGC 110101199003076716</code>\n\n注意：每60秒只能使用一次",
        "menu_help": f"{EMOJIS['help']} <b>使用指令</b>\n\n命令列表：\n• /QGC - 车牌查询\n• /IP - IP查询\n• /DW3 - 定位生成\n• /ZFM - 身份证生成\n• /CZC - 车辆在场\n• /SGC - 社工查\n• /start - 返回主菜单"
    }
    
    if query.data in menu_handlers:
        await query.edit_message_text(
            menu_handlers[query.data],
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    if is_admin_user:
        admin_menu_handlers = {
            "menu_loc_relation": f"{EMOJIS['map']} <b>定位关联（管理员）</b>\n\n格式：<code>/DW1 身份证号</code>\n示例：<code>/DW1 110101199003076716</code>",
            "menu_common_loc": f"{EMOJIS['location']} <b>常用地查询（管理员）</b>\n\n格式：<code>/DW2 地址</code>\n示例：<code>/DW2 北京市朝阳区</code>",
            "menu_gwc": f"{EMOJIS['search']} <b>公网查（管理员）</b>\n\n格式：<code>/GWC 任何信息</code>\n示例：<code>/GWC 手机号</code>或<code>/GWC 身份证</code>或<code>/GWC 姓名</code>",
        }
        
        if query.data in admin_menu_handlers:
            await query.edit_message_text(
                admin_menu_handlers[query.data],
                parse_mode=ParseMode.HTML,
                reply_markup=create_back_button()
            )
            return
        
        if query.data == "menu_stats":
            user_count, active_users, total_queries, user_list = user_manager.get_user_statistics()
            
            stats_text = (
                f"{EMOJIS['stats']} <b>用户数据统计</b>\n\n"
                f"📊 <b>整体统计</b>\n"
                f"├ 总用户数：<b>{user_count}</b> 人\n"
                f"├ 活跃用户：<b>{active_users}</b> 人（7天内）\n"
                f"├ 总查询量：<b>{total_queries}</b> 次\n"
                f"└ 平均查询：<b>{total_queries//max(user_count,1)}</b> 次/人\n\n"
                f"🏆 <b>查询排行榜（前10）</b>\n"
            )
            
            for i, user in enumerate(user_list[:10], 1):
                user_name = user.get('username', f"用户{user['user_id']}")
                if len(user_name) > 12:
                    user_name = user_name[:12] + "..."
                
                try:
                    last_active = datetime.datetime.fromisoformat(user.get('last_active', '')).strftime('%m-%d %H:%M')
                except:
                    last_active = "未知"
                
                admin_tag = " 👑" if user.get('is_admin') else ""
                banned_tag = " 🚫" if user.get('is_banned', False) else ""
                
                stats_text += f"{i:2d}. {user_name}{admin_tag}{banned_tag}\n"
                stats_text += f"     ID：{user['user_id']}\n"
                stats_text += f"     苹果直达链接：tg://user?id={user['user_id']}\n"
                stats_text += f"     安卓直达链接：tg://openmessage?user_id={user['user_id']}\n"
                stats_text += f"    📊 {user.get('query_count', 0)}次 | ⏰ {last_active}\n"
            
            await query.edit_message_text(
                stats_text,
                parse_mode=ParseMode.HTML,
                reply_markup=create_back_button()
            )
            return
    
    if query.data in ["menu_stats", "menu_loc_relation", "menu_common_loc", "menu_gwc"] and not is_admin_user:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

async def car_info_command(update: Update, context: CallbackContext):
    if not await check_user_access(update, context):
        return
    
    if not context.args:
        await update.message.reply_text(
            f"{EMOJIS['car']} <b>车牌查询</b>\n\n格式：<code>/QGC 车牌号</code>\n示例：<code>/QGC 京A88888</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    license_plate = context.args[0].upper()
    user_manager.increment_query_count(update.effective_user.id)
    
    try:
        msg = await update.message.reply_text(
            f"{EMOJIS['search']} <b>查询中...</b>\n车牌：<code>{license_plate}</code>",
            parse_mode=ParseMode.HTML
        )
        
        response = requests.get(
            CAR_API_URL,
            params={"plate": license_plate},
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("code") == 200:
                    info = data.get("data", {})
                    result = (
                        f"{EMOJIS['car']} <b>查询结果</b>\n\n"
                        f"🚗 车牌：<code>{license_plate}</code>\n"
                        f"👤 车主：<code>{info.get('name', '未公开')}</code>\n"
                        f"📞 电话：<code>{info.get('phone', '未公开')}</code>\n"
                        f"🪪 身份证：<code>{info.get('id_card', '未公开')}</code>\n"
                        f"📍 地址：{info.get('address', '未公开')}"
                    )
                else:
                    result = f"{EMOJIS['error']} 查询失败：{data.get('message', '未知错误')}"
            except:
                cleaned_text = remove_watermarks(response.text)
                result = f"{EMOJIS['car']} <b>查询结果</b>\n\n🚗 车牌：<code>{license_plate}</code>\n\n{cleaned_text}"
        else:
            result = f"{EMOJIS['error']} 查询接口异常"
        
        await msg.edit_text(
            result,
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
    except Exception as e:
        logger.error(f"车牌查询失败: {e}")
        await update.message.reply_text(
            f"{EMOJIS['error']} 查询异常",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )

async def ip_query_command(update: Update, context: CallbackContext):
    if not await check_user_access(update, context):
        return
    
    if not context.args:
        await update.message.reply_text(
            f"{EMOJIS['ip']} <b>IP查询</b>\n\n格式：<code>/IP IP地址</code>\n示例：<code>/IP 114.114.114.114</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    ip = context.args[0]
    user_manager.increment_query_count(update.effective_user.id)
    
    try:
        msg = await update.message.reply_text(
            f"{EMOJIS['search']} <b>查询中...</b>\nIP：<code>{ip}</code>",
            parse_mode=ParseMode.HTML
        )
        
        response = requests.get(IP_QUERY_API.format(ip), timeout=10)
        
        if response.status_code == 200:
            await msg.delete()
            await update.message.reply_photo(
                photo=response.content,
                caption=f"{EMOJIS['ip']} <b>IP查询结果</b>\n🌐 IP：<code>{ip}</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=create_back_button()
            )
        else:
            await msg.edit_text(
                f"{EMOJIS['error']} 查询失败",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"IP查询失败: {e}")
        await update.message.reply_text(
            f"{EMOJIS['error']} 查询异常",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )

async def CZC_command(update: Update, context: CallbackContext):
    if not await check_user_access(update, context):
        return
    
    if not context.args:
        await update.message.reply_text(
            f"{EMOJIS['scan']} <b>车辆在场</b>\n\n格式：<code>/CZC 车牌号</code>\n示例：<code>/CZC 京A88888</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    plate = context.args[0].upper()
    user_manager.increment_query_count(update.effective_user.id)
    
    try:
        msg = await update.message.reply_text(
            f"{EMOJIS['search']} <b>查询中...</b>\n车牌：<code>{plate}</code>",
            parse_mode=ParseMode.HTML
        )
        
        response = requests.get(
            CZC_API_URL,
            params={"plate_number": plate},
            timeout=15
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict):
                    result = remove_watermarks(json.dumps(data, ensure_ascii=False, indent=2))
                else:
                    result = remove_watermarks(response.text)
            except:
                result = remove_watermarks(response.text)
            
            await msg.delete()
            
            result_text = f"{EMOJIS['scan']} <b>查询结果</b>\n\n🚗 车牌：<code>{plate}</code>\n\n{result}"
            
            if len(result_text) > 1500:
                await send_as_txt_file(update, plate, result, "车辆在场查询")
            else:
                await update.message.reply_text(
                    result_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=create_back_button()
                )
        else:
            await msg.edit_text(
                f"{EMOJIS['error']} 查询失败",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"查询失败: {e}")
        await update.message.reply_text(
            f"{EMOJIS['error']} 查询异常",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )

async def ZFM_command(update: Update, context: CallbackContext):
    if not await check_user_access(update, context):
        return
    
    if len(context.args) < 2 or not is_valid_id_card(context.args[1]):
        await update.message.reply_text(
            f"{EMOJIS['id_card']} <b>身份证生成</b>\n\n格式：<code>/ZFM 姓名 身份证</code>\n示例：<code>/ZFM 张三 110101199003076716</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    name, id_card = context.args[0], context.args[1]
    user_manager.increment_query_count(update.effective_user.id)
    
    try:
        msg = await update.message.reply_text(
            f"{EMOJIS['search']} <b>生成中...</b>\n姓名：<code>{name}</code>",
            parse_mode=ParseMode.HTML
        )
        
        response = requests.get(ZFM_API_URL.format(name, id_card), timeout=60)
        
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            await msg.delete()
            await update.message.reply_photo(
                photo=response.content,
                caption=f"{EMOJIS['id_card']} <b>身份证</b>\n👤 姓名：<code>{name}</code>\n🪪 身份证：<code>{id_card}</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=create_back_button()
            )
        else:
            await msg.edit_text(
                f"{EMOJIS['error']} 生成失败",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"身份证生成失败: {e}")
        await update.message.reply_text(
            f"{EMOJIS['error']} 生成异常",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )

async def DW4_command(update: Update, context: CallbackContext):
    if not await check_user_access(update, context):
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            f"{EMOJIS['location']} <b>定位生成</b>\n\n格式：<code>/DW3 经度 纬度</code>\n示例：<code>/DW3 116.404 39.915</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    try:
        lon, lat = float(context.args[0]), float(context.args[1])
        baidu_link = f"https://api.map.baidu.com/marker?location={lat},{lon}&title=GPS定位点&output=html"
        amap_link = f"https://uri.amap.com/marker?position={lon},{lat}&name=GPS定位点"
        
        keyboard = [
            [InlineKeyboardButton(f"{EMOJIS['map']} 百度地图", url=baidu_link)],
            [InlineKeyboardButton(f"{EMOJIS['map']} 高德地图", url=amap_link)],
            [InlineKeyboardButton(f"{EMOJIS['back']} 返回主菜单", callback_data="menu_main")]
        ]
        
        await update.message.reply_text(
            f"{EMOJIS['location']} <b>定位链接</b>\n\n📍 坐标：<code>{lon}</code>, <code>{lat}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await update.message.reply_text(
            f"{EMOJIS['error']} 坐标格式错误",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )

async def SGC_command(update: Update, context: CallbackContext):
    if not await check_user_access(update, context):
        return
    
    if not context.args:
        await update.message.reply_text(
            f"{EMOJIS['search']} <b>社工查</b>\n\n格式：<code>/SGC 手机号或身份证</code>\n示例：<code>/SGC 13800138000</code>或<code>/SGC 110101199003076716</code>\n\n注意：每60秒只能使用一次",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    query_text = ' '.join(context.args)
    user_id = update.effective_user.id
    
    if not user_manager.can_use_sgc(user_id):
        remaining = user_manager.get_sgc_cooldown_remaining(user_id)
        await update.message.reply_text(
            f"{EMOJIS['clock']} <b>冷却时间中</b>\n\n"
            f"❌ 社工查每60秒只能使用一次\n"
            f"⏳ 请等待 {remaining} 秒后再试",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    user_manager.increment_query_count(user_id)
    
    try:
        msg = await update.message.reply_text(
            f"{EMOJIS['search']} <b>查询中...</b>\n查询内容：<code>{query_text[:50]}</code>",
            parse_mode=ParseMode.HTML
        )
        
        encoded_text = requests.utils.quote(query_text)
        response = requests.get(
            SGC_API_URL.format(encoded_text),
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict):
                    result = remove_watermarks(json.dumps(data, ensure_ascii=False, indent=2))
                else:
                    result = remove_watermarks(response.text)
            except:
                result = remove_watermarks(response.text)
            
            result_text = f"{EMOJIS['search']} <b>查询结果</b>\n\n📝 查询内容：<code>{query_text}</code>\n\n{result}"
            
            if len(result_text) > 1500:
                await send_as_txt_file(update, query_text, result, "社工查")
            else:
                await msg.edit_text(
                    result_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=create_back_button()
                )
        else:
            await msg.edit_text(
                f"{EMOJIS['error']} 查询失败，状态码：{response.status_code}",
                parse_mode=ParseMode.HTML,
                reply_markup=create_back_button()
            )
    except Exception as e:
        logger.error(f"社工查询失败: {e}")
        await update.message.reply_text(
            f"{EMOJIS['error']} 查询异常：{str(e)[:100]}",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )

async def dw1_command(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            f"{EMOJIS['error']} 无管理员权限",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    if not context.args or not is_valid_id_card(context.args[0]):
        await update.message.reply_text(
            f"{EMOJIS['map']} <b>定位关联</b>\n\n格式：<code>/DW1 身份证号</code>\n示例：<code>/DW1 110101199003076716</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    id_card = context.args[0]
    user_manager.increment_query_count(update.effective_user.id)
    
    try:
        msg = await update.message.reply_text(
            f"{EMOJIS['search']} <b>查询中...</b>\n身份证：<code>{id_card}</code>",
            parse_mode=ParseMode.HTML
        )
        
        response = requests.get(
            DY1_API_URL,
            params={"idcard": id_card, "app_id": DY1_APP_ID, "app_secret": DY1_APP_SECRET},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 1:
                address_data = data.get("data", {})
                address = address_data.get("address", "未知地址")
                await msg.edit_text(
                    f"{EMOJIS['map']} <b>查询结果</b>\n\n🪪 身份证：<code>{id_card}</code>\n📍 地址：{address}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=create_back_button()
                )
            else:
                await msg.edit_text(
                    f"{EMOJIS['error']} 查询失败：{data.get('msg', '未知错误')}",
                    parse_mode=ParseMode.HTML
                )
        else:
            await msg.edit_text(
                f"{EMOJIS['error']} 查询接口异常",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"定位查询失败: {e}")
        await update.message.reply_text(
            f"{EMOJIS['error']} 查询异常",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )

async def DW2_command(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            f"{EMOJIS['error']} 无管理员权限",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            f"{EMOJIS['location']} <b>常用地查询</b>\n\n格式：<code>/DW2 地址</code>\n示例：<code>/DW2 北京市朝阳区</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    address = ' '.join(context.args)
    user_manager.increment_query_count(update.effective_user.id)
    
    try:
        msg = await update.message.reply_text(
            f"{EMOJIS['search']} <b>查询中...</b>\n地址：{address}",
            parse_mode=ParseMode.HTML
        )
        
        response = requests.get(DW2_API_URL, params={"keyword": address}, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("code") == 200:
                    result_lines = [f"{EMOJIS['success']} <b>检索成功</b>\n"]
                    data_list = data.get("data", [])
                    
                    if data_list:
                        for i, item in enumerate(data_list, 1):
                            address_text = item.get("address", "")
                            if address_text:
                                result_lines.append(f"{i}. {address_text}")
                    else:
                        result_lines.append(f"{EMOJIS['warning']} 未找到地址信息")
                    
                    result = "\n".join(result_lines)
                    await msg.edit_text(
                        result,
                        parse_mode=ParseMode.HTML,
                        reply_markup=create_back_button()
                    )
                else:
                    await msg.edit_text(
                        f"{EMOJIS['error']} 查询失败：{data.get('msg', '未知错误')}",
                        parse_mode=ParseMode.HTML
                    )
            except:
                result = remove_watermarks(response.text) or "无地址信息"
                await msg.edit_text(
                    f"{EMOJIS['location']} <b>查询结果</b>\n\n地址：{address}\n\n{result}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=create_back_button()
                )
        else:
            await msg.edit_text(
                f"{EMOJIS['error']} 查询失败",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"地址查询失败: {e}")
        await update.message.reply_text(
            f"{EMOJIS['error']} 查询异常",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )

async def GWC_command(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            f"{EMOJIS['error']} 无管理员权限",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            f"{EMOJIS['search']} <b>公网查（管理员）</b>\n\n命令：<code>/GWC </code>\n示例：<code>/GWC 手机号</code>或<code>/GWC 身份证</code>或<code>/GWC 姓名</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    query_text = ' '.join(context.args)
    user_manager.increment_query_count(update.effective_user.id)
    
    try:
        msg = await update.message.reply_text(
            f"{EMOJIS['search']} <b>查询中...</b>\n查询内容：<code>{query_text[:50]}</code>",
            parse_mode=ParseMode.HTML
        )
        
        encoded_text = requests.utils.quote(query_text)
        response = requests.get(
            GWC_API_URL.format(encoded_text),
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict):
                    result = remove_watermarks(json.dumps(data, ensure_ascii=False, indent=2))
                else:
                    result = remove_watermarks(response.text)
            except:
                result = remove_watermarks(response.text)
            
            specific_watermarks = [
                "本API为 @QingFengSGK and @HeiKeAPI and @duanfa 所有 官网 qingfeng.qzz.io",
                "本API为 @QingFengSGK and @HeiKeAPI and @duanfa 所有 官网 qingfeng.qzz.io\n",
                "本API为 @QingFengSGK and @HeiKeAPI and @duanfa 所有 官网 qingfeng.qzz.io\n\n",
                "@QingFengSGK",
                "@HeiKeAPI",
                "@duanfa",
                "qingfeng.qzz.io"
            ]
            
            for watermark in specific_watermarks:
                result = result.replace(watermark, "")
            
            lines = result.split('\n')
            cleaned_lines = []
            for line in lines:
                stripped_line = line.strip()
                if stripped_line and stripped_line not in specific_watermarks:
                    if not any(keyword in stripped_line for keyword in ["本API为", "@QingFengSGK", "@HeiKeAPI", "@duanfa", "qingfeng.qzz.io"]):
                        cleaned_lines.append(stripped_line)
            
            result = '\n'.join(cleaned_lines)
            
            result_text = f"{EMOJIS['search']} <b>查询结果</b>\n\n📝 查询内容：<code>{query_text}</code>\n\n{result}"
            
            if len(result_text) > 1500:
                await send_as_txt_file(update, query_text, result, "公网查")
            else:
                await msg.edit_text(
                    result_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=create_back_button()
                )
        else:
            await msg.edit_text(
                f"{EMOJIS['error']} 查询失败，状态码：{response.status_code}",
                parse_mode=ParseMode.HTML,
                reply_markup=create_back_button()
            )
    except Exception as e:
        logger.error(f"公网查询失败: {e}")
        await update.message.reply_text(
            f"{EMOJIS['error']} 查询异常：{str(e)[:100]}",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )

async def FJ_command(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            f"{EMOJIS['error']} 无管理员权限",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            f"{EMOJIS['ban']} <b>封禁用户</b>\n\n格式：<code>/FJ 用户ID</code>\n示例：<code>/FJ 123456789</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    user_id = int(context.args[0])
    user_data = user_manager.get_user_data(user_id)
    user_manager.ban_user(user_id)
    
    display_name = user_data.get("full_name", "")
    if not display_name:
        display_name = user_data.get("username", f"用户_{user_id}")
    
    result = f"{EMOJIS['ban']} <b>封禁成功</b>\n\n👤 用户：{display_name}\n🆔 ID：<code>{user_id}</code>"
    
    await update.message.reply_text(
        result,
        parse_mode=ParseMode.HTML,
        reply_markup=create_back_button()
    )

async def JF_command(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            f"{EMOJIS['error']} 无管理员权限",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            f"{EMOJIS['unlock']} <b>解封用户</b>\n\n格式：<code>/JF 用户ID</code>\n示例：<code>/JF 123456789</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    user_id = int(context.args[0])
    user_data = user_manager.get_user_data(user_id)
    user_manager.unban_user(user_id)
    
    display_name = user_data.get("full_name", "")
    if not display_name:
        display_name = user_data.get("username", f"用户_{user_id}")
    
    result = f"{EMOJIS['unlock']} <b>解封成功</b>\n\n👤 用户：{display_name}\n🆔 ID：<code>{user_id}</code>"
    
    await update.message.reply_text(
        result,
        parse_mode=ParseMode.HTML,
        reply_markup=create_back_button()
    )

async def check_user_command(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            f"{EMOJIS['error']} 无管理员权限",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            f"{EMOJIS['user']} <b>查看用户信息</b>\n\n格式：<code>/CKYH 用户ID</code>\n示例：<code>/CKYH 123456789</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )
        return
    
    user_id = int(context.args[0])
    user_data = user_manager.get_user_data(user_id)
    
    display_name = user_data.get("full_name", "")
    if not display_name:
        display_name = user_data.get("username", f"用户_{user_id}")
    
    admin_status = "👑 是" if user_manager.is_admin(user_id) else "👤 否"
    ban_status = f"{EMOJIS['ban']} 已封禁" if user_data.get("is_banned") else f"{EMOJIS['success']} 正常"
    
    info = (
        f"{EMOJIS['user']} <b>用户详细信息</b>\n\n"
        f"🆔 用户ID：<code>{user_id}</code>\n\n"
        f"👤 显示名称：{display_name}\n"
        f"📛 用户名：{user_data.get('username', '无')}\n"
        f"📊 查询次数：<b>{user_data.get('query_count', 0)}</b> 次\n"
        f"👑 管理员：{admin_status}\n"
        f"🚫 封禁状态：{ban_status}\n"
        f"⏰ 最后活跃：{user_data.get('last_active', '未知')}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(f"{EMOJIS['ban']} 封禁用户", callback_data=f"ban_{user_id}"),
            InlineKeyboardButton(f"{EMOJIS['unlock']} 解封用户", callback_data=f"unban_{user_id}")
        ],
        [
            InlineKeyboardButton(f"{EMOJIS['back']} 返回主菜单", callback_data="menu_main")
        ]
    ]
    
    await update.message.reply_text(
        info,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.answer("❌ 无管理员权限", show_alert=True)
        return
    
    if query.data.startswith("ban_"):
        try:
            target_user_id = int(query.data.replace("ban_", ""))
            user_data = user_manager.get_user_data(target_user_id)
            
            display_name = user_data.get("full_name", "")
            if not display_name:
                display_name = user_data.get("username", f"用户_{target_user_id}")
            
            user_manager.ban_user(target_user_id)
            
            result = f"{EMOJIS['ban']} <b>封禁成功</b>\n\n👤 用户：{display_name}\n🆔 ID：<code>{target_user_id}</code>"
            
            await query.edit_message_text(
                result,
                parse_mode=ParseMode.HTML,
                reply_markup=create_back_button()
            )
        except Exception as e:
            logger.error(f"封禁用户失败: {e}")
            await query.edit_message_text(
                f"{EMOJIS['error']} 封禁失败",
                parse_mode=ParseMode.HTML
            )
        return
    
    elif query.data.startswith("unban_"):
        try:
            target_user_id = int(query.data.replace("unban_", ""))
            user_data = user_manager.get_user_data(target_user_id)
            
            display_name = user_data.get("full_name", "")
            if not display_name:
                display_name = user_data.get("username", f"用户_{target_user_id}")
            
            user_manager.unban_user(target_user_id)
            
            result = f"{EMOJIS['unlock']} <b>解封成功</b>\n\n👤 用户：{display_name}\n🆔 ID：<code>{target_user_id}</code>"
            
            await query.edit_message_text(
                result,
                parse_mode=ParseMode.HTML,
                reply_markup=create_back_button()
            )
        except Exception as e:
            logger.error(f"解封用户失败: {e}")
            await query.edit_message_text(
                f"{EMOJIS['error']} 解封失败",
                parse_mode=ParseMode.HTML
            )
        return

async def record_user(update: Update, context: CallbackContext):
    try:
        user = update.effective_user
        if not user:
            return
        await update_user_info(update, context)
    except Exception as e:
        logger.error(f"记录用户失败: {e}")

async def error_handler(update: Update, context: CallbackContext):
    logger.error(f"更新处理失败: {context.error}", exc_info=True)
    if update and update.message:
        await update.message.reply_text(
            f"{EMOJIS['error']} 系统处理异常",
            parse_mode=ParseMode.HTML,
            reply_markup=create_back_button()
        )

async def keep_alive_task(context: CallbackContext):
    try:
        await context.bot.get_me()
        logger.debug("连接保活：心跳请求成功")
    except Exception as e:
        logger.warning(f"连接保活失败: {e}")

def main():
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        
        application.add_handler(CommandHandler("qgc", car_info_command))
        application.add_handler(CommandHandler("ip", ip_query_command))
        application.add_handler(CommandHandler("DW3", DW4_command))
        application.add_handler(CommandHandler("ZFM", ZFM_command))
        application.add_handler(CommandHandler("CZC", CZC_command))
        application.add_handler(CommandHandler("SGC", SGC_command))
        application.add_handler(CommandHandler("GWC", GWC_command))
        
        application.add_handler(CommandHandler("dw1", dw1_command))
        application.add_handler(CommandHandler("DW2", DW2_command))
        
        application.add_handler(CommandHandler("FJ", FJ_command))
        application.add_handler(CommandHandler("JF", JF_command))
        application.add_handler(CommandHandler("CKYH", check_user_command))
        
        application.add_handler(CallbackQueryHandler(menu_handler))
        application.add_handler(CallbackQueryHandler(admin_button_handler))
        
        application.add_handler(MessageHandler(filters.TEXT, record_user, block=False))
        
        application.add_error_handler(error_handler)
        
        application.job_queue.run_repeating(keep_alive_task, interval=300, first=10)
        
        print("=" * 50)
        print("公网辅查系统启动成功！")
        print(f"管理员ID：{ADMIN_IDS}")
        print("=" * 50)
        
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            poll_interval=0.5
        )
        
    except Exception as e:
        logger.critical(f"机器人启动失败: {e}")
        print(f"启动失败：{e}")

if __name__ == '__main__':
    main()