import telebot
from threading import Thread
from time import sleep
from secrets import TG_TOKEN
from vk import get_posts

bot = telebot.TeleBot(TG_TOKEN, threaded=True)
chat_id = set()
queue = []
sent_posts = set()

fn_sent_posts = "./sent_posts.txt"
fn_chat_ids = "./chats.txt"

# @bot.message_handler(content_types=['text'])
# def get_text_messages(message):
#     pass


# @bot.message_handler(commands=['start', 'help'])
# def send_welcome(message):
#     bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    if message.chat.id not in chat_id:
        print(message)
        chat_id.add(message.chat.id)
        # save to file
        f = open(fn_chat_ids, 'w')
        try:
            for item in chat_id:
                f.write('%s\n' % item)
        except NameError as e:
            print(e)
            bot.send_message(message.chat.id, "Try again later")
        else:
            print(f'New chat ({message.chat.id})')
        finally:
            f.close()
        bot.send_message(message.chat.id, "Started")


@bot.message_handler(commands=['stop'])
def stop_message(message):
    chat_id.remove(message.chat.id)
    # save to file
    f = open(fn_chat_ids, 'w')
    try:
        for item in chat_id:
            f.write('%s\n' % item)
    except NameError as e:
        print(e)
        bot.send_message(message.chat.id, f"{e}\nTry again later")
    else:
        print(f'Delete chat ({message.chat.id})')
    finally:
        f.close()
    bot.send_message(message.chat.id, "Stop")


def send_msg(msg, media):
    for chat in chat_id:
        print(f'\nMessage to {chat}:')
        print(f'\n\t{msg}')
        if len(media) > 0:
            # bot.send_photo(chat, media[0], caption=msg)
            # bot.send_message(chat, msg + '\n[ссылка] (' + ')\n[ссылка] ('.join(media) + ')')
            bot.send_message(chat, msg + '\n[ссылка] (' + ')\n[ссылка] ('.join(media) + ')', {'parseMode': 'Markdown'})
        else:
            bot.send_message(chat, msg)

# echo
# @bot.message_handler(func=lambda message: True)
# def echo_all(message):
#     bot.reply_to(message, message.text)


def run_bot(args):
    # bot.polling(none_stop=True)
    bot.infinity_polling(True)


def get_new_posts(args):
    posts = get_posts(args["url"])
    while args["run"]:
        for post_id in posts:
            if post_id not in sent_posts:
                # print('_' * 30)
                # print(f"{post_id}:\n\t{posts[post_id]['date']}\n\t{posts[post_id]['text']}\n\t{posts[post_id]['media_url']}")
                # # print(posts[post_id]['media'])
                # print('=' * 30)
                send_msg(posts[post_id]['text'], posts[post_id]['media_url'])
                sent_posts.add(post_id)
        save_sent_posts()
        sleep(args['posts_interval'])


def save_sent_posts():
    try:
        with open(fn_sent_posts, 'w') as f:
            for item in sent_posts:
                f.write('%s\n' % item)
    except NameError as e:
        print(e)


def load_data():
    f = None
    try:
        f = open(fn_sent_posts, 'r')
        for line in f:
            # delete \n and append
            sent_posts.add(line[:-1])
    except FileNotFoundError:
        print(f"\t File not found: {fn_sent_posts}")
    except NameError as e:
        print(e)
    finally:
        if f:
            f.close()

    try:
        f = open(fn_chat_ids, 'r')
        for line in f:
            # delete \n and append
            chat_id.add(line[:-1])
    except FileNotFoundError:
        print(f"\t File not found: {fn_chat_ids}")
    except NameError as e:
        print(e)
    finally:
        if f:
            f.close()


if __name__ == '__main__':
    info = {'run': True,
            'url': "https://vk.com/covid19nn",
            'posts_interval': 30}

    load_data()
    print('Chats: \n\t{}'.format("\n\t".join(chat_id)))

    run_bot_thread = Thread(target=run_bot, args=(info,), daemon=True)
    get_posts_thread = Thread(target=get_new_posts, args=(info,), daemon=True)
    run_bot_thread.start()
    get_posts_thread.start()
    while True:
        try:
            sleep(30)
        except KeyboardInterrupt:
            info["run"] = False
            break
    bot.stop_polling()
    run_bot_thread.join()
    get_posts_thread.join()


