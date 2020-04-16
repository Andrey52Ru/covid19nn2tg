import telebot
from secrets import TG_TOKEN
from vk import get_posts

bot = telebot.TeleBot(TG_TOKEN)


# @bot.message_handler(content_types=['text'])
# def get_text_messages(message):
#     pass

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)


bot.polling()

posts = get_posts("https://vk.com/covid19nn")
for post_id in posts:
    print(f"{post_id}:\n\t{posts[post_id]['date']}\n\t{posts[post_id]['text']}\n\t{posts[post_id]['media_url']}")
    # print(posts[post_id]['media'])
    print('=' * 30)

print(f'{len(posts)}')
