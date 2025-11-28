# btn : about and close change here

from pyrogram import __version__
from bot import Bot
from config import OWNER_ID
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ForceReply

from config import (
    OWNER_ID, 
    SHORTLINK_URL_1, SHORTLINK_API_1, 
    SHORTLINK_URL_2, SHORTLINK_API_2, 
    VERIFY_GAP_TIME, 
    TUT_VID
)
from helper_func import get_exp_time
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ForceReply
from pyrogram import filters

# In-memory storage for shortener settings (since no dedicated DB table was found)
# This is a temporary fix. A proper DB solution would be better.
SHORTENER_SETTINGS = {
    'shortener1_enabled': True,
    'shortener2_enabled': True,
    'gap_time': VERIFY_GAP_TIME
}

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('shortener'))
async def shortener_settings_command(client: Bot, message: Message):
    await message.reply_text(
        "**Shortener Settings Panel**",
        reply_markup=get_shortener_settings_markup(),
        quote=True
    )

def get_shortener_settings_markup():
    s1_status = "✅ ON" if SHORTENER_SETTINGS['shortener1_enabled'] else "❌ OFF"
    s2_status = "✅ ON" if SHORTENER_SETTINGS['shortener2_enabled'] else "❌ OFF"
    gap_time_str = get_exp_time(SHORTENER_SETTINGS['gap_time'])
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Shortener 1: {s1_status}", callback_data="shortener_toggle_1")],
        [InlineKeyboardButton(f"Shortener 2: {s2_status}", callback_data="shortener_toggle_2")],
        [InlineKeyboardButton(f"Gap Time: {gap_time_str}", callback_data="shortener_set_gap")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="shortener_refresh")],
        [InlineKeyboardButton("❌ Close", callback_data="close")]
    ])

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    
    # --- Shortener Settings Callbacks (Fix 3) ---
    if data.startswith("shortener_"):
        await query.answer()
        
        if data == "shortener_toggle_1":
            SHORTENER_SETTINGS['shortener1_enabled'] = not SHORTENER_SETTINGS['shortener1_enabled']
            await query.message.edit_reply_markup(get_shortener_settings_markup())
        
        elif data == "shortener_toggle_2":
            SHORTENER_SETTINGS['shortener2_enabled'] = not SHORTENER_SETTINGS['shortener2_enabled']
            await query.message.edit_reply_markup(get_shortener_settings_markup())
            
        elif data == "shortener_set_gap":
            await query.message.reply_text(
                "Reply to this message with the new **Gap Time** in seconds (e.g., `1800` for 30 mins).",
                reply_markup=ForceReply(True)
            )
            # This requires a message handler to process the reply
            
        elif data == "shortener_refresh":
            await query.message.edit_reply_markup(get_shortener_settings_markup())
            
        return

    # --- Batch Image Selection Callbacks (Fix 4) ---
    elif data.startswith("batch_img_"):
        await query.answer()
        
        parts = data.split("_")
        choice = parts[2]
        f_msg_id = int(parts[3])
        s_msg_id = int(parts[4])
        
        if choice == "yes":
            await query.message.edit_text("Send the verification image URL for this batch:")
            # Use client.ask to get the image URL
            try:
                image_msg = await client.ask(
                    text="Send the verification image URL:",
                    chat_id=query.from_user.id,
                    filters=filters.text,
                    timeout=60
                )
                batch_image = image_msg.text.strip()
                await process_batch_link(client, query.message, f_msg_id, s_msg_id, batch_image)
            except:
                await query.message.edit_text("❌ Timed out or error while getting image URL. Generating link without custom image.")
                await process_batch_link(client, query.message, f_msg_id, s_msg_id)
                
        elif choice == "no":
            await query.message.edit_text("Generating link without custom image.")
            await process_batch_link(client, query.message, f_msg_id, s_msg_id)
            
        return

    # --- Existing Callbacks ---
    elif data == "about":
        await query.message.edit_text(
            text = f"<b>○ ᴏᴡɴᴇʀ : <a href='tg://user?id={OWNER_ID}'>ᴍɪᴋᴇʏ</a>\n○ ᴍʏ ᴜᴘᴅᴀᴛᴇs : <a href='https://t.me/Hanimes_Hindi'>Channel</a>\n○ ᴍᴏᴠɪᴇs ᴜᴘᴅᴀᴛᴇs : <a href='https://t.me/Hanimes_Hindi'>MovizTube</a>\n○ ᴏᴜʀ ᴄᴏᴍᴍᴜɴɪᴛʏ : <a href='https://t.me/Hanimes_Hindi'>Chat</a></b>",
            disable_web_page_preview = True,
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⚡️ ᴄʟᴏsᴇ", callback_data = "close"),
                        InlineKeyboardButton('🍁 Support', url='https://t.me/Hanimes_Hindi')
                    ]
                ]
            )
        )
    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.reply & filters.text)
async def handle_shortener_gap_reply(client: Bot, message: Message):
    if message.reply_to_message and message.reply_to_message.text and "Gap Time" in message.reply_to_message.text:
        try:
            new_gap_time = int(message.text.strip())
            if new_gap_time < 0:
                raise ValueError("Gap time cannot be negative.")
            
            SHORTENER_SETTINGS['gap_time'] = new_gap_time
            await message.reply_text(f"✅ Gap Time successfully updated to **{get_exp_time(new_gap_time)}**.", quote=True)
            
            # Optional: Refresh the settings panel if it's still visible
            # This requires knowing the original message ID, which is complex. A simple reply is enough.
            
        except ValueError:
            await message.reply_text("❌ Invalid input. Please send a valid number of seconds for the Gap Time.", quote=True)
