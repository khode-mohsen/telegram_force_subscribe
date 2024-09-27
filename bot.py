import logging
import requests
# import time

from telegram import (
    ForceReply,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    # Application,
    # CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ApplicationBuilder,
    CallbackQueryHandler,
    CallbackContext,
    # JobQueue
)



CHANNEL_ID = # Int
API_TOKEN = '' # Str
CHNNEL_USERNAME = '' #Str
PROXY_URL = '' # Str

request_kwargs = {
    'proxy_url': PROXY_URL
    }


MSG_FORCE_SUBSCRIBATION = f'لطفا برای ارسال پیام اول وارد گروه @{CHNNEL_USERNAME} شوید .'
MSG_FAIL_SUBSCRIBATION_CHECK = f'عضویت شما در @{CHNNEL_USERNAME} تایید نشد لطفا مجددا تلاش فرمایید!'
MSG_SUCCESS_SUBSCRIBATION = 'عضویت شما با موفقیت تایید شد!'

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.WARN
)
logging.getLogger(__name__).setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
users_in_check = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )

def check_subscription(user_id: int) -> bool:
    url = f"https://api.telegram.org/bot{API_TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={user_id}"
    response = requests.get(url).json()
    status = response.get('result', {}).get('status', '')
    return status in ['member', 'administrator', 'creator']

import asyncio
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    chat_id = update.effective_message.chat_id
    message_id = update.effective_message.message_id

    if check_subscription(user_id):
        await update.message.reply_text(MSG_SUCCESS_SUBSCRIBATION)
    else:
        await update.message.delete()
        keyboard = [[InlineKeyboardButton("Check Subscription", callback_data='check_subscription')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if user_id not in users_in_check:
            users_in_check.append(user_id)
            msg = await update.message.reply_text(MSG_FORCE_SUBSCRIBATION, reply_markup=reply_markup)
            context.job_queue.run_once(delete_message, 15, chat_id=chat_id, data=msg, name=str(user_id))


async def delete_message(context: CallbackContext) -> None:
    job = context.job
    users_in_check.remove(int(job.name))
    await job.data.delete()

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    current_text = query.message.text
    new_text = MSG_SUCCESS_SUBSCRIBATION if check_subscription(user_id) else MSG_FAIL_SUBSCRIBATION_CHECK
    await query.answer()
    if current_text != new_text:
        keyboard = [[InlineKeyboardButton("Check Subscription", callback_data='check_subscription')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(text=new_text, reply_markup=reply_markup)
        except Exception as e:
            print(f"not able to delete {e}")


def main() -> None:
    application = ApplicationBuilder().token(API_TOKEN).proxy(PROXY_URL).build()
    # application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == "__main__":
    main()