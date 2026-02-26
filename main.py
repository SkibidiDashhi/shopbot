import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import (
    BOT_TOKEN, ADMIN_IDS, ADMIN_GROUP_ID,
    B_1, LOGO, Warning, NO, FLASH, SURE, LOVE,
    PLUS, TRUE, ROBUX, ROBLOX, BLOX_FRUIT, LOVE_1, LOVE_2,
    Wallet, Kpay, Wave, Slip, No_1, King, Rq, 
    Ok, Arrow, Shield, onehundred, Money, PRODUCTS,
    SHOP_PHOTO_URL, PRODUCT_PHOTOS
)
import database

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# ================= STATE TRACKING =================
topup_states = {}
ticket_states = {}
purchase_states = {}
robux_states = {}  # user_id -> {'step': 1|2, 'username': str, 'amount': int, 'message_id': int}
broadcast_states = {}  # admin_id -> {'step': 1, 'message': str, 'photo': str}

# ================= ACCOUNT FUNCTION =================
def get_account(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            return None
        account = lines[0].strip()
        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(lines[1:])
        return account
    except Exception as e:
        print("Account error:", e)
        return None

# ================= ADMIN CHECK =================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ================= GET ALL USERS FUNCTION =================
def get_all_users():
    """Get all user IDs from database"""
    database.cursor.execute("SELECT user_id FROM users")
    users = database.cursor.fetchall()
    return [user[0] for user in users]

# ================= /start COMMAND =================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    database.add_user(message.from_user.id)
    await message.answer(
        f"{LOGO} Zuki Storez Bot မှာကြိုဆိုပါတယ်ရှင့်\n\n"
        f"လိုအပ်တာဝယ်ယူရန် /shop ဆိုပြီးပို့ပေးပါ {Warning}\n\n"
        f"လက်ကျန်ငွေစစ်ရန် /balance ဆိုပြီးပို့ပေးပါ {Warning}\n\n"
        f"လက်ကျန်ငွေဖြည့်သွင်းရင် /topup ဆိုပြီးပို့ပေးပါ {Warning}\n\n"
        f"Error ပါလာပါက Report တင်ရန် /ticket ဆိုပြီးပို့ပေးပါ {Warning}\n\n"
        f"ကောင်းမွန်သောနေ့လေးပိုင်ဆိုင်ပါစေရှင့် {LOVE_1}"
    )
    await bot.send_message(
        ADMIN_GROUP_ID,
        f"{B_1} New User Started Bot\n\n"
        f"Name: {message.from_user.full_name}\n"
        f"ID: {message.from_user.id}"
    )

# ================= /balance COMMAND =================
@dp.message(Command("balance"))
async def balance_cmd(message: types.Message):
    balance = database.get_balance(message.from_user.id)
    await message.answer(f"{Wallet} သင့်ရဲ့လက်ကျန်ငွေ : {balance}")

# ================= /broadcast COMMAND (Admin Only) =================
@dp.message(Command("broadcast"))
async def broadcast_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer(f"{NO} ဒီ command ကို Admin များသုံးလို့ရပါတယ်။")
        return
    
    broadcast_states[message.from_user.id] = {'step': 1}
    await message.answer(
        f"{Rq} ကျေးဇူးပြု၍ ပို့လိုသော Message ကိုရိုက်ထည့်ပါ။\n\n"
        f"မှတ်ချက်: ပုံပါလိုပါက စာသားနှင့်အတူ ပုံကိုပါ တစ်ခါတည်းပို့ပေးနိုင်ပါသည်။"
    )

@dp.message(lambda m: m.from_user.id in broadcast_states and broadcast_states[m.from_user.id]['step'] == 1)
async def handle_broadcast_message(message: types.Message):
    admin_id = message.from_user.id
    
    # Check if message has photo
    if message.photo:
        photo_id = message.photo[-1].file_id
        caption = message.caption if message.caption else ""
        
        broadcast_states[admin_id]['photo'] = photo_id
        broadcast_states[admin_id]['message'] = caption
    else:
        broadcast_states[admin_id]['message'] = message.text
        broadcast_states[admin_id]['photo'] = None
    
    # Ask for confirmation
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Send Broadcast", callback_data="broadcast_confirm"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="broadcast_cancel")
            ]
        ]
    )
    
    preview_text = f"{Arrow} Broadcast Preview:\n\n{broadcast_states[admin_id]['message']}"
    
    if broadcast_states[admin_id]['photo']:
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=broadcast_states[admin_id]['photo'],
            caption=preview_text,
            reply_markup=keyboard
        )
    else:
        await message.answer(preview_text, reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "broadcast_confirm")
async def broadcast_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only command", show_alert=True)
        return
    
    admin_id = callback.from_user.id
    state = broadcast_states.get(admin_id)
    
    if not state:
        await callback.answer("Session expired", show_alert=True)
        return
    
    await callback.message.edit_text("📤 Sending broadcast messages... Please wait.")
    
    # Get all users
    users = get_all_users()
    successful = 0
    failed = 0
    
    for user_id in users:
        try:
            if state['photo']:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=state['photo'],
                    caption=state['message']
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=state['message']
                )
            successful += 1
            await asyncio.sleep(0.05)  # Small delay to avoid rate limiting
        except Exception as e:
            failed += 1
            print(f"Failed to send to {user_id}: {e}")
    
    # Send result to admin
    result_text = (
        f"{SURE} Broadcast Completed!\n\n"
        f"✅ Successful: {successful}\n"
        f"❌ Failed: {failed}"
    )
    
    await callback.message.edit_text(result_text)
    
    # Also send to admin group
    await bot.send_message(
        ADMIN_GROUP_ID,
        f"📢 Broadcast Report\n\n"
        f"Admin: {callback.from_user.full_name}\n"
        f"✅ Successful: {successful}\n"
        f"❌ Failed: {failed}"
    )
    
    del broadcast_states[admin_id]
    await callback.answer()

@dp.callback_query(lambda c: c.data == "broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery):
    admin_id = callback.from_user.id
    
    await callback.message.edit_text("❌ Broadcast cancelled.")
    
    if admin_id in broadcast_states:
        del broadcast_states[admin_id]
    
    await callback.answer()

# ================= /addbalance COMMAND =================
@dp.message(Command("addbalance"))
async def add_balance_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer(f"{NO} ဒီ command ကို Admin များသုံးလို့ရပါတယ်။")
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.answer(
            f"{Warning} နည်းလမ်းမှားယွင်းနေပါသည်။\n\n"
            f"အသုံးပြုပုံ: /addbalance [user_id] [ငွေပမာဏ]\n"
            f"ဥပမာ: /addbalance 123456789 10000"
        )
        return
    
    try:
        user_id = int(args[1])
        amount = int(args[2])
        
        if amount <= 0:
            await message.answer(f"{NO} ငွေပမာဏ မှန်ကန်စွာထည့်ပါ။")
            return
        
        database.add_balance(user_id, amount)
        new_balance = database.get_balance(user_id)
        
        await message.answer(
            f"{TRUE} လက်ကျန်ငွေထည့်သွင်းပြီးပါပြီ။\n\n"
            f"User ID: {user_id}\n"
            f"ထည့်သွင်းငွေ: {amount}\n"
            f"လက်ကျန်ငွေ: {new_balance}"
        )
        
        try:
            await bot.send_message(
                user_id,
                f"{PLUS} သင့်အကောင့်သို့ ငွေထည့်သွင်းပေးထားပါသည်။\n\n"
                f"ထည့်သွင်းငွေ: {amount}\n"
                f"လက်ကျန်ငွေ: {new_balance}\n\n"
                f"ဝယ်ယူရန်: /shop"
            )
        except:
            await message.answer(f"⚠️ User {user_id} ကို message ပို့မရပါ။")
            
    except ValueError:
        await message.answer(f"{NO} User ID နှင့် ငွေပမာဏသည် နံပါတ်ဖြစ်ရပါမည်။")
    except Exception as e:
        await message.answer(f"❌ အမှားအယွင်းရှိနေပါသည်: {str(e)}")

# ================= /ticket COMMAND =================
@dp.message(Command("ticket"))
async def ticket_cmd(message: types.Message):
    ticket_states[message.from_user.id] = {'step': 1}
    await message.answer(
        f"{Rq} ကျေးဇူးပြု၍ သင်တွေ့ကြုံရသော Error သို့မဟုတ် အဆင်မပြေမှုကို ရှင်းလင်းစွာရေးသားပို့ပေးပါ။\n\n"
        f"ဥပမာ - ကျွန်တော် ငွေဖြည့်လိုက်ပေမယ့် လက်ကျန်မတိုးလာပါ။"
    )

@dp.message(lambda m: m.from_user.id in ticket_states and ticket_states[m.from_user.id]['step'] == 1)
async def handle_ticket_message(message: types.Message):
    user_id = message.from_user.id
    ticket_text = message.text
    
    ticket_states[user_id]['message'] = ticket_text
    ticket_states[user_id]['step'] = 2
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 Yes, send screenshot", callback_data="ticket_photo_yes"),
                InlineKeyboardButton(text="❌ No, just send", callback_data="ticket_photo_no")
            ]
        ]
    )
    
    await message.answer(
        f"သင့်တွင် Screenshot ရှိပါသလား?\n"
        f"(ရှိပါက ပို့ပေးခြင်းဖြင့် ပြဿနာဖြေရှင်းရန် ပိုမိုလွယ်ကူစေပါသည်)",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith("ticket_photo_"))
async def ticket_photo_choice(callback: CallbackQuery):
    user_id = callback.from_user.id
    state = ticket_states.get(user_id)
    
    if not state:
        await callback.answer("Session expired. Please use /ticket again.")
        return
    
    choice = callback.data.split("_")[2]
    
    if choice == "yes":
        ticket_states[user_id]['step'] = 3
        await callback.message.edit_text("📸 ကျေးဇူးပြု၍ Screenshot ကိုပို့ပေးပါ။")
    else:
        await send_ticket_to_admin(callback.message, user_id, state['message'], None)
        await callback.message.edit_text(f"{SURE} သင့် Report ကို Admin Team ထံပို့ပြီးပါပြီ။ မကြာမီ ပြန်လည်ဖြေကြားပါမည်။")
        del ticket_states[user_id]
    
    await callback.answer()

@dp.message(lambda m: m.from_user.id in ticket_states and ticket_states[m.from_user.id].get('step') == 3 and m.photo)
async def handle_ticket_photo(message: types.Message):
    user_id = message.from_user.id
    state = ticket_states.get(user_id)
    
    if not state:
        return
    
    photo_id = message.photo[-1].file_id
    await send_ticket_to_admin(message, user_id, state['message'], photo_id)
    await message.answer(f"{SURE} သင့် Report ကို Admin Team ထံပို့ပြီးပါပြီ။ မကြာမီ ပြန်လည်ဖြေကြားပါမည်။")
    del ticket_states[user_id]

async def send_ticket_to_admin(message: types.Message, user_id: int, ticket_text: str, photo_id: str = None):
    caption = (
        f"{Rq} NEW TICKET REPORT\n\n"
        f"👤 User: {message.from_user.full_name}\n"
        f"🆔 ID: {user_id}\n"
        f"📝 Username: @{message.from_user.username or 'None'}\n"
        f"💬 Message: {ticket_text}\n"
        f"📅 Date: {message.date}\n\n"
        f"Use /reply_{user_id} to respond to this user"
    )
    
    try:
        if photo_id:
            await bot.send_photo(
                ADMIN_GROUP_ID,
                photo=photo_id,
                caption=caption
            )
        else:
            await bot.send_message(
                ADMIN_GROUP_ID,
                caption
            )
    except Exception as e:
        print(f"❌ Error sending ticket to admin group: {e}")
        await message.answer("❌ Admin ထံပို့ရာတွင် အဆင်မပြေမှုရှိပါသည်။ ခဏနေမှထပ်ကြိုးစားပါ။")

# ================= ADMIN REPLY HANDLER =================
@dp.message(lambda m: m.text and m.text.startswith('/reply_'))
async def admin_reply(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer(f"{NO} ဒီ command ကို Admin များသုံးလို့ရပါတယ်။")
        return
    
    try:
        parts = message.text.split(' ', 1)
        command = parts[0]
        reply_text = parts[1] if len(parts) > 1 else ""
        
        user_id = int(command.replace('/reply_', ''))
        
        if not reply_text:
            await message.answer("ပြန်ကြားလိုသည့် စာသားကိုရေးပေးပါ။\nဥပမာ: /reply_123456789 ကျေးဇူးတင်ပါတယ်။")
            return
        
        await bot.send_message(
            user_id,
            f"👑 Admin Team မှ ပြန်ကြားချက်:\n\n{reply_text}"
        )
        
        await message.answer(f"✅ User {user_id} ကို ပြန်ကြားပြီးပါပြီ။")
        
    except ValueError:
        await message.answer("❌ User ID မှားယွင်းနေပါသည်။ ဥပမာ: /reply_123456789")
    except Exception as e:
        await message.answer(f"❌ ပြန်ကြားရာတွင် အဆင်မပြေမှုရှိပါသည်: {str(e)}")

# ================= /topup COMMAND =================
@dp.message(Command("topup"))
async def topup_cmd(message: types.Message):
    topup_states[message.from_user.id] = {'step': 1}
    await message.answer(
        f"{Kpay} 09420136212 [ KBZ Pay ]\n"
        f"{Wave} 09951734587 [ Wave Pay ]\n\n"
        f"{King} နာမည် - Zar Chi Win\n\n"
        f"{No_1} Note ကိုစနောက်တာထည့်လာလျှင် ဖြည့်ပေးမည်မဟုတ်ပါ {No_1}\n\n"
        f"{Slip} ငွေလွှဲပြီးပါက Slip Screenshot ကိုပို့ပေးမှသာထည့်ပေးလို့ရပါမည်။"
    )
    await message.answer(f"{Wallet} ငွေထည့်မည့် ပမာဏပို့ပေးပါ။")

@dp.message(lambda m: m.from_user.id in topup_states and topup_states[m.from_user.id]['step'] == 1 and not m.photo)
async def handle_topup_amount(message: types.Message):
    user_id = message.from_user.id
    state = topup_states[user_id]
    
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.answer(f"{NO} ငွေပမာဏ သက်ဆိုင်ရာဖြည့်ပါ")
            return
        state['amount'] = amount
        state['step'] = 2
        await message.answer(f"{Slip} ငွေလွှဲ Screenshot ပို့ပေးပါ")
    except ValueError:
        await message.answer(f"{NO} ငွေပမာဏ အမှန်တကယ် စာရိုက်ပေးပါ")

@dp.message(lambda m: m.from_user.id in topup_states and m.photo)
async def handle_topup_photo(message: types.Message):
    user_id = message.from_user.id
    state = topup_states.get(user_id)
    
    if not state or state.get('step') != 2:
        await message.answer("Please enter the amount first using /topup command")
        return

    photo = message.photo[-1]
    photo_id = photo.file_id
    amount = state.get('amount', 'Unknown')

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{user_id}")
            ]
        ]
    )
    
    caption = (
        f"{PLUS} New Topup Request\n\n"
        f"👤 Name: {message.from_user.full_name}\n"
        f"🆔 ID: {user_id}\n"
        f"💰 Amount: {amount} MMK\n"
        f"📝 Username: @{message.from_user.username or 'None'}"
    )

    try:
        await bot.send_photo(
            ADMIN_GROUP_ID,
            photo=photo_id,
            caption=caption,
            reply_markup=keyboard
        )
        
        state['photo_id'] = photo_id
        state['step'] = 3
        
        await message.answer(
            f"{SURE} သင့်ရဲ့ Request ကို Admin များထံပို့ပြီးပါပြီ။\n"
            f"ခဏစောင့်ပေးပါ။ {Rq}"
        )
        
    except Exception as e:
        print(f"❌ Error sending to admin group: {e}")
        await message.answer("❌ နည်းပညာအခက်အခဲရှိနေပါသည်။ ခဏနေမှထပ်ကြိုးစားပါ။")
        if user_id in topup_states:
            del topup_states[user_id]

@dp.callback_query(lambda c: c.data.startswith("approve_"))
async def approve_topup(callback: CallbackQuery):
    try:
        user_id = int(callback.data.split("_")[1])
        state = topup_states.get(user_id)
        
        if not state:
            await callback.answer("❌ Request expired or already processed", show_alert=True)
            await callback.message.edit_caption(
                callback.message.caption + "\n\n❌ This request has expired"
            )
            return
            
        amount = state.get('amount', 0)
        
        database.add_balance(user_id, amount)
        
        await callback.message.edit_caption(
            f"✅ APPROVED\n\n"
            f"User ID: {user_id}\n"
            f"Amount: {amount} MMK\n"
            f"Approved by: {callback.from_user.full_name}"
        )
        
        await bot.send_message(
            user_id,
            f"{TRUE} Topup အောင်မြင်ပါသည်\n\n"
            f"💰 ငွေပမာဏ: {amount} MMK\n"
            f"✅ သင့်အကောင့်သို့ထည့်သွင်းပြီးပါပြီ။\n\n"
            f"လက်ကျန်စစ်ရန်: /balance"
        )
        
        del topup_states[user_id]
        await callback.answer("✅ Approved successfully")
        
    except Exception as e:
        print(f"Error in approve: {e}")
        await callback.answer("❌ Error processing approval", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("reject_"))
async def reject_topup(callback: CallbackQuery):
    try:
        user_id = int(callback.data.split("_")[1])
        state = topup_states.get(user_id)
        
        if not state:
            await callback.answer("❌ Request expired or already processed", show_alert=True)
            await callback.message.edit_caption(
                callback.message.caption + "\n\n❌ This request has expired"
            )
            return
            
        amount = state.get('amount', 'Unknown')
        
        await callback.message.edit_caption(
            f"❌ REJECTED\n\n"
            f"User ID: {user_id}\n"
            f"Amount: {amount} MMK\n"
            f"Rejected by: {callback.from_user.full_name}"
        )
        
        await bot.send_message(
            user_id,
            f"{NO} Topup မအောင်မြင်ပါ\n\n"
            f"ငွေလွှဲပြေစာကို ပြန်လည်စစ်ဆေးပြီးမှသာ ထည့်သွင်းပေးပါမည်။\n"
            f"ထပ်မံကြိုးစားရန်: /topup"
        )
        
        del topup_states[user_id]
        await callback.answer("✅ Rejected")
        
    except Exception as e:
        print(f"Error in reject: {e}")
        await callback.answer("❌ Error processing rejection", show_alert=True)

# ================= /shop COMMAND =================
@dp.message(Command("shop"))
async def shop_cmd(message: types.Message):
    try:
        if not PRODUCTS:
            await message.answer("❌ Products not available at the moment.")
            return
            
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🎮 Blox Fruits Random", callback_data="view_blox"),
                ],
                [
                    InlineKeyboardButton(text="👤 Avatar Random", callback_data="view_avatar"),
                ],
                [
                    InlineKeyboardButton(text="💰 Buy Robux", callback_data="view_robux"),
                ],
                [
                    InlineKeyboardButton(text="🌐 Zuki Services", url="https://www.zukiservices.com")
                ]
            ]
        )
        
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=SHOP_PHOTO_URL,
            caption=f"{LOGO} မိမိဝယ်ချင်သည့် ပစ္စည်းကိုနှိပ်ပေးပါရန်။",
            reply_markup=keyboard
        )
        
    except Exception as e:
        print(f"Error in shop command: {e}")
        await message.answer("❌ Shop menu temporarily unavailable. Please try again later.")

# ================= VIEW PRODUCT DETAILS =================
@dp.callback_query(lambda c: c.data.startswith("view_"))
async def view_product(callback: CallbackQuery):
    try:
        product_key = callback.data.replace("view_", "")
        
        product_map = {
            "blox": "Blox Fruits Random",
            "avatar": "Avatar Random",
            "robux": "Buy Robux"
        }
        
        product_name = product_map.get(product_key)
        if not product_name:
            await callback.answer("Product not found")
            return
        
        # Special handling for Robux
        if product_key == "robux":
            await callback.message.delete()
            robux_states[callback.from_user.id] = {'step': 1}
            await bot.send_message(
                callback.message.chat.id,
                f"{ROBLOX} သင့်ရဲ့ Roblox Username ပို့ပေးပါ။"
            )
            await callback.answer()
            return
            
        product = PRODUCTS.get(product_name)
        if not product:
            await callback.answer("Product details not found")
            return
            
        product_photo = PRODUCT_PHOTOS.get(product_name, SHOP_PHOTO_URL)
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Yes, Buy Now", callback_data=f"confirm_{product_key}"),
                    InlineKeyboardButton(text="❌ No, Go Back", callback_data="back_to_shop")
                ]
            ]
        )
        
        await callback.message.delete()
        
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=product_photo,
            caption=(
                f"📦 {product_name}\n\n"
                f"💰 Price: {product['price']} MMK\n"
                f"📝 Description: {product.get('description', 'Random account with good items')}\n\n"
                f"သေချာဝယ်ယူလိုပါသလား?"
            ),
            reply_markup=keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        print(f"Error in view_product: {e}")
        await callback.answer("❌ Error loading product details")

# ================= ROBUX PURCHASE HANDLERS =================
@dp.message(lambda m: m.from_user.id in robux_states and robux_states[m.from_user.id]['step'] == 1)
async def handle_robux_username(message: types.Message):
    user_id = message.from_user.id
    username = message.text.strip()
    
    robux_states[user_id]['username'] = username
    robux_states[user_id]['step'] = 2
    
    await message.answer(
        f"{ROBUX} သင်ဝယ်ယူချင်သော Robux Amount ကိုထည့်ပေးပါ။\n"
        f"(1 Robux = 25 MMK)"
    )

@dp.message(lambda m: m.from_user.id in robux_states and robux_states[m.from_user.id]['step'] == 2)
async def handle_robux_amount(message: types.Message):
    user_id = message.from_user.id
    state = robux_states[user_id]
    
    try:
        robux_amount = int(message.text.strip())
        if robux_amount <= 0:
            await message.answer(f"{NO} ကျေးဇူးပြု၍ မှန်ကန်သော ဂဏန်းထည့်ပါ။")
            return
            
        total_price = robux_amount * 25
        state['robux_amount'] = robux_amount
        state['total_price'] = total_price
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Buy for Sure", callback_data="robux_confirm"),
                    InlineKeyboardButton(text="❌ Not going to buy", callback_data="robux_cancel")
                ]
            ]
        )
        
        await message.answer(
            f"{ROBUX} သင်ဝယ်ယူမည့် Robux အချက်အလက်များ\n\n"
            f"Roblox Username: {state['username']}\n"
            f"Robux Amount: {robux_amount}\n"
            f"စုစုပေါင်းငွေ: {total_price} MMK\n\n"
            f"သေချာဝယ်ယူလိုပါသလား?",
            reply_markup=keyboard
        )
        
    except ValueError:
        await message.answer(f"{NO} ကျေးဇူးပြု၍ မှန်ကန်သော ဂဏန်းထည့်ပါ။")

@dp.callback_query(lambda c: c.data == "robux_confirm")
async def robux_confirm(callback: CallbackQuery):
    user_id = callback.from_user.id
    state = robux_states.get(user_id)
    
    if not state:
        await callback.answer("Session expired. Please try again.")
        return
    
    balance = database.get_balance(user_id)
    
    if balance < state['total_price']:
        await callback.message.delete()
        await bot.send_message(
            callback.message.chat.id,
            f"{NO} Balance မလုံလောက်ပါ\n\n"
            f"Your Balance: {balance} MMK\n"
            f"Need: {state['total_price']} MMK\n\n"
            f"ငွေဖြည့်ရန်: /topup"
        )
        await callback.answer()
        del robux_states[user_id]
        return
    
    # Deduct balance
    database.deduct_balance(user_id, state['total_price'])
    
    await callback.message.delete()
    
    # Send confirmation to user
    await bot.send_message(
        user_id,
        f"{TRUE} Robux ဝယ်ယူမှုအောင်မြင်ပါသည်\n\n"
        f"Roblox Username: {state['username']}\n"
        f"Robux Amount: {state['robux_amount']}\n"
        f"စုစုပေါင်းငွေ: {state['total_price']} MMK\n\n"
        f"ကျေးဇူးပြု၍ ခဏစောင့်ပါ။ သင့် Roblox အကောင့်သို့ Robux ပို့ပေးပါမည်။"
    )
    
    # Create admin notification keyboard with 2 buttons in a row
    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Order Complete", callback_data=f"robux_complete_{user_id}"),
                InlineKeyboardButton(text="❌ Order Failed", callback_data=f"robux_failed_{user_id}")
            ]
        ]
    )
    
    # Send to admin group
    admin_message = await bot.send_message(
        ADMIN_GROUP_ID,
        f"🛒 NEW ROBUX ORDER\n\n"
        f"👤 User: {callback.from_user.full_name}\n"
        f"🆔 ID: {user_id}\n"
        f"📝 Username: @{callback.from_user.username or 'None'}\n"
        f"🎮 Roblox Username: {state['username']}\n"
        f"💰 Robux Amount: {state['robux_amount']}\n"
        f"💵 Total Price: {state['total_price']} MMK\n"
        f"⏰ Time: {callback.message.date}\n\n"
        f"{Arrow} Please process this order and update status:",
        reply_markup=admin_keyboard
    )
    
    # Store admin message ID for reference
    state['admin_message_id'] = admin_message.message_id
    
    await callback.answer("✅ Purchase successful!")

# ================= ROBUX ADMIN ORDER STATUS HANDLERS =================
@dp.callback_query(lambda c: c.data.startswith("robux_complete_"))
async def robux_order_complete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only command", show_alert=True)
        return
    
    user_id = int(callback.data.replace("robux_complete_", ""))
    
    # Update admin message
    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ Order Completed by {callback.from_user.full_name}"
    )
    
    # Notify user
    await bot.send_message(
        user_id,
        f"{TRUE} သင့် Robux မှာယူမှု ပြီးဆုံးပါပြီ။\n"
        f"ကျေးဇူးတင်ပါသည် {LOVE_1}"
    )
    
    await callback.answer("✅ Order marked as complete")

@dp.callback_query(lambda c: c.data.startswith("robux_failed_"))
async def robux_order_failed(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin only command", show_alert=True)
        return
    
    user_id = int(callback.data.replace("robux_failed_", ""))
    
    # Update admin message
    await callback.message.edit_text(
        callback.message.text + f"\n\n❌ Order Failed by {callback.from_user.full_name}"
    )
    
    # Refund user
    # Note: You need to get the amount from somewhere - you might want to store order details
    # This is a placeholder - you'll need to implement refund logic
    await bot.send_message(
        user_id,
        f"{NO} သင့် Robux မှာယူမှု မအောင်မြင်ပါ။\n"
        f"ငွေပြန်အမ်းပေးပါမည်။ ကျေးဇူးပြု၍ Admin ကိုဆက်သွယ်ပါ။"
    )
    
    await callback.answer("❌ Order marked as failed")

@dp.callback_query(lambda c: c.data == "robux_cancel")
async def robux_cancel(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    await callback.message.delete()
    await bot.send_message(
        callback.message.chat.id,
        "❌ Robux ဝယ်ယူမှုကို ဖျက်သိမ်းလိုက်ပါသည်။"
    )
    
    if user_id in robux_states:
        del robux_states[user_id]
    
    await callback.answer()

# ================= BACK TO SHOP =================
@dp.callback_query(lambda c: c.data == "back_to_shop")
async def back_to_shop(callback: CallbackQuery):
    try:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🎮 Blox Fruits Random", callback_data="view_blox"),
                ],
                [
                    InlineKeyboardButton(text="👤 Avatar Random", callback_data="view_avatar"),
                ],
                [
                    InlineKeyboardButton(text="💰 Buy Robux", callback_data="view_robux"),
                ],
                [
                    InlineKeyboardButton(text="🌐 Zuki Services", url="https://www.zukiservices.com")
                ]
            ]
        )
        
        await callback.message.delete()
        
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=SHOP_PHOTO_URL,
            caption=f"{LOGO} မိမိဝယ်ချင်သည့် ပစ္စည်းကိုနှိပ်ပေးပါရန်။",
            reply_markup=keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        print(f"Error in back_to_shop: {e}")
        await callback.answer("❌ Error returning to shop")

# ================= CONFIRM PURCHASE (for Blox Fruits & Avatar) =================
@dp.callback_query(lambda c: c.data.startswith("confirm_") and not c.data == "confirm_robux")
async def confirm_purchase(callback: CallbackQuery):
    try:
        product_key = callback.data.replace("confirm_", "")
        
        product_map = {
            "blox": "Blox Fruits Random",
            "avatar": "Avatar Random"
        }
        
        product_name = product_map.get(product_key)
        if not product_name:
            await callback.answer("Product not found")
            return
            
        user_id = callback.from_user.id
        price = PRODUCTS[product_name]["price"]
        filename = PRODUCTS[product_name]["file"]
        
        purchase_states[user_id] = {
            'product': product_name,
            'price': price,
            'filename': filename
        }
        
        balance = database.get_balance(user_id)
        if balance < price:
            await callback.message.delete()
            await bot.send_message(
                callback.message.chat.id,
                f"{NO} Balance မလုံလောက်ပါ\n\n"
                f"Your Balance: {balance} MMK\n"
                f"Need: {price} MMK\n\n"
                f"ငွေဖြည့်ရန်: /topup"
            )
            await callback.answer()
            return
            
        await process_purchase(callback, user_id, product_name, price, filename)
        
    except Exception as e:
        print(f"Error in confirm_purchase: {e}")
        await callback.answer("❌ Error processing purchase")

# ================= PROCESS PURCHASE =================
async def process_purchase(callback: CallbackQuery, user_id: int, product_name: str, price: int, filename: str):
    try:
        if not database.deduct_balance(user_id, price):
            await callback.message.delete()
            await bot.send_message(
                callback.message.chat.id,
                f"{NO} Balance deduction failed. Please try again."
            )
            await callback.answer()
            return

        account = get_account(filename)
        if not account:
            database.add_balance(user_id, price)
            await callback.message.delete()
            await bot.send_message(
                callback.message.chat.id,
                "❌ Product out of stock. Your balance has been refunded.\n\n"
                "ပစ္စည်းပြီးသွားပါသည်။ ကျေးဇူးပြု၍ ခဏစောင့်ပါ။"
            )
            await callback.answer()
            return

        await callback.message.delete()
        
        await bot.send_message(
            user_id,
            f"{TRUE} {product_name} ဝယ်ယူမှုအောင်မြင်ပါသည်\n\n"
            f"📦 Account Details:\n{account}\n\n"
            f"ဝယ်ယူမှုအတွက်ကျေးဇူးတင်ပါသည်။"
        )
        
        await bot.send_message(
            ADMIN_GROUP_ID,
            f"🛒 New Purchase\n\n"
            f"User: {callback.from_user.full_name}\n"
            f"ID: {user_id}\n"
            f"Product: {product_name}\n"
            f"Price: {price} MMK"
        )
        
        if user_id in purchase_states:
            del purchase_states[user_id]
            
        await callback.answer("✅ Purchase successful!")
        
    except Exception as e:
        print(f"Error in process_purchase: {e}")
        await callback.message.delete()
        await bot.send_message(
            callback.message.chat.id,
            "❌ An error occurred during purchase. Please try again."
        )
        await callback.answer()

# ================= ERROR HANDLER =================
@dp.errors()
async def errors_handler(event: types.ErrorEvent):
    print(f"Bot error: {event.exception}")
    try:
        if event.update.message:
            await event.update.message.answer("❌ An error occurred. Please try again later.")
    except:
        pass

# ================= START BOT =================
async def main():
    print("✅ Bot Started Successfully")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
