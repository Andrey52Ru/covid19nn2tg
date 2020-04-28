import telebot
import sys
from threading import Thread, Lock
from time import sleep
import logging
from secrets import TG_TOKEN
import vk

fn_sent_posts = r"./sent_posts.txt"
fn_chat_ids = r"./chats.txt"
RUN = True
mutex = Lock()

chats = set()
sent_posts = set()

telegram_bot = telebot.TeleBot(TG_TOKEN, threaded=True, num_threads=2)
logger = logging.getLogger(r"main_log")


def logger_init(loggers, log_file, log_level=logging.ERROR,
                format_str='%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: %(message)s'):
    # format_str = '%(asctime)s %(levelname)s - %(name)s: "%(message)s"'
    formatter = logging.Formatter(format_str)
    logger_output_handlers = [logging.FileHandler(log_file, 'a'),
                              logging.StreamHandler(sys.stderr)]
    for h in logger_output_handlers:
        h.setFormatter(formatter)

    for lg in loggers:
        lg.setLevel(log_level)
        for h in lg.handlers[:]:  # remove all old handlers
            lg.removeHandler(h)
        for h in logger_output_handlers:
            lg.addHandler(h)

    # vk.logger.setLevel(logging.ERROR)
    # telebot.logger.setLevel(logging.ERROR)


# @telegram_bot.message_handler(content_types=['text'])
# def get_text_messages(message):
#     pass


@telegram_bot.message_handler(commands=['start', 'subscribe'])
def start_message(message):
    logger.debug(f'Subscribe chat {message.chat.id} ({message.chat.title})')  # Username:{message["from"].username}')
    if message.chat.id not in chats:
        mutex.acquire()
        try:
            chats.add(message.chat.id)
            result = save_chats(chats)
            if not result:
                logger.info(f'Subscribed: {message.chat.id}. Total: {len(chats)}')
                telegram_bot.send_message(message.chat.id, u"Вы успешно подписаны на рассылку")
            else:
                logger.error(r"Subscribe: Exception: " + str(result))
                telegram_bot.send_message(message.chat.id, u"Что-то пошло не так... Попробуйте позднее")
        finally:
            mutex.release()
    else:
        logger.info(f'Already subscribed: {message.chat.id}. Total: {len(chats)}')
        telegram_bot.send_message(message.chat.id, u"Вы уже подписаны на рассылку")


@telegram_bot.message_handler(commands=['stop', 'unsubscribe'])
def stop_message(message):
    logger.debug(f'Unsubscribe chat {message.chat.id} ({message.chat.title})')  # Username:{message["from"].username}')
    if message.chat.id in chats:
        mutex.acquire()
        try:
            chats.remove(message.chat.id)
            result = save_chats(chats)
            if not result:
                logger.info(f'Unsubscribed: {message.chat.id}. Total: {len(chats)}')
                telegram_bot.send_message(message.chat.id, u"Вы успешно отписаны от рассылки")
            else:
                logger.error(r"Unsubscribe: Exception: " + str(result))
                telegram_bot.send_message(message.chat.id, u"Что-то пошло не так... Попробуйте позднее")
        finally:
            mutex.release()
    else:
        logger.info(f'Already unsubscribed: {message.chat.id}. Total: {len(chats)}')
        telegram_bot.send_message(message.chat.id, u"Вы уже отписались от рассылки ранее")


@telegram_bot.message_handler(commands=['status'])
def status_message(message):
    status = ''
    if message.chat.id in chats:
        status = "Subscribed"
        telegram_bot.send_message(message.chat.id, "Вы подписаны")
    else:
        status = "Unsubscribed"
        telegram_bot.send_message(message.chat.id, "Вы не подписаны")
    logger.debug(f'Status: {status} From {message.chat.id} ({message.chat.title})')  # Username:{message["from"].username}')


def send_post(bot, post_id, msg, media):
    logger.info(f'Sending post {post_id}...')
    i = 0
    for chat in chats:
        i += 1
        logger.debug(f'Post to chat #{i} of {len(chats)}: {chat} ')
        if len(media) > 0:
            ret_msg = bot.send_message(chat_id=chat, text=msg + u'\n[ссылка](' + u')\n[ссылка]('.join(media) + u')',
                             disable_web_page_preview=False, parse_mode='Markdown')
            # The last log record
        else:
            ret_msg = bot.send_message(chat, msg)
        logger.debug(f'Posted to chat #{i} of {len(chats)}: {chat} Success: {ret_msg.ok} {ret_msg.result}')
    logger.debug('Post: {}\n\t{}\n\tMedia:'.format(post_id, msg, '\n'.join(media)))


# echo
# @telegram_bot.message_handler(func=lambda message: True)
# def echo_all(message):
#     telegram_bot.reply_to(message, message.text)


def load_data():
    f = None
    try:
        f = open(fn_sent_posts, 'r')
        for line in f:
            # delete \n and append
            sent_posts.add(line[:-1])
    except FileNotFoundError:
        logger.warning(f"\t File not found: {fn_sent_posts}")
    except NameError as e:
        logger.error(r"Exception: " + str(e))
    finally:
        if f:
            f.close()

    try:
        f = open(fn_chat_ids, 'r')
        for line in f:
            chats.add(int(line))
    except FileNotFoundError:
        logger.warning(f"\t File not found: {fn_chat_ids}")
    except NameError as e:
        logger.error(r"Exception: " + str(e))
    finally:
        if f:
            f.close()


def save_chats(data):
    f = open(fn_chat_ids, 'w')
    try:
        for item in data:
            f.write('%s\n' % item)
    except NameError as e:
        return e
    else:
        return None
    finally:
        f.close()


def save_sent_posts():
    mutex.acquire()
    try:
        with open(fn_sent_posts, 'w') as f:
            for item in sent_posts:
                f.write('%s\n' % item)
    except NameError as e:
        logger.error(r"Exception: " + str(e))
    finally:
        mutex.release()


def get_new_posts(args, bot):
    while RUN:
        posts = vk.get_posts(args["url"])
        logger.debug(f"get_new_posts: {len(posts)} posts. Last post {list(posts.keys())[0]}")
        sent_flag = False
        for post_id in list(posts.keys())[::-1]:    # reverse
            if post_id not in sent_posts:
                send_post(bot, post_id, posts[post_id]['text'], posts[post_id]['media_url'])
                sent_posts.add(post_id)
                sent_flag = True
        if sent_flag:
            save_sent_posts()
            logger.debug(r"Save sent posts")
        for i in range(args['posts_interval']):
            if not RUN:
                break
            sleep(1)
    logger.debug(f"Stopped getting new posts")


if __name__ == '__main__':
    conf = {'url': "https://vk.com/covid19nn",
            'posts_interval': 300,
            # 'log_file': r'/tmp/bot.log',
            'log_file': r'./bot.log',
            'log_level': logging.DEBUG}

    logger_init((logger, telebot.logger, vk.logger), conf['log_file'], conf['log_level'])
    load_data()

    logger.info('Chats: \n\t{}'.format("\n\t".join(str(x) for x in chats)))

    # run_bot_thread = Thread(target=telegram_bot.infinity_polling(), args=(True,), daemon=True)
    get_posts_thread = Thread(target=get_new_posts, args=(conf, telegram_bot), name='get_posts_thread', daemon=True)
    # run_bot_thread.start()
    get_posts_thread.start()
    try:
        telegram_bot.infinity_polling(none_stop=True)
        RUN = False
    except KeyboardInterrupt:
        RUN = False
        telegram_bot.stop_polling()
    # run_bot_thread.join()
    get_posts_thread.join()
