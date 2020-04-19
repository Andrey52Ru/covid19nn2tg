import telebot
import sys
from threading import Thread
from time import sleep
import logging
from secrets import TG_TOKEN
import vk

fn_sent_posts = r"./sent_posts.txt"
fn_chat_ids = r"./chats.txt"
RUN = True

chat_id = set()
sent_posts = set()

bot = telebot.TeleBot(TG_TOKEN, threaded=True)
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


# @bot.message_handler(content_types=['text'])
# def get_text_messages(message):
#     pass


@bot.message_handler(commands=['start'])
def start_message(message):
    logger.debug(f'New chat {message.chat.id}...')
    if message.chat.id not in chat_id:
        chat_id.add(message.chat.id)
        # save to file
        f = open(fn_chat_ids, 'w')
        try:
            for item in chat_id:
                f.write('%s\n' % item)
        except NameError as e:
            logger.error(r"Exception: " + str(e))
            bot.send_message(message.chat.id, "Try again later")
        else:
            logger.info(f'Success: new chat {message.chat.id}. Total: {len(chat_id)}')
        finally:
            f.close()
        bot.send_message(message.chat.id, "Started")


@bot.message_handler(commands=['stop'])
def stop_message(message):
    logger.debug(f'Removing chat {message.chat.id}...')
    chat_id.remove(message.chat.id)
    # save to file
    f = open(fn_chat_ids, 'w')
    try:
        for item in chat_id:
            f.write('%s\n' % item)
    except NameError as e:
        logger.error(r"Exception: " + str(e))
        bot.send_message(message.chat.id, f"{e}\nTry again later")
    else:
        logger.info(f'Success: removed chat {message.chat.id}. Total: {len(chat_id)}')
    finally:
        f.close()
    bot.send_message(message.chat.id, "Stop")


def send_msg(post_id, msg, media):
    logger.info(f'Sending message {post_id}...')
    for chat in chat_id:
        logger.debug(f'\nMessage to chat {chat}:')
        if len(media) > 0:
            bot.send_message(chat_id=chat, text=msg + '\n[ссылка](' + ')\n[ссылка]('.join(media) + ')',
                             disable_web_page_preview=False, parse_mode='Markdown')
        else:
            bot.send_message(chat, msg)
    logger.debug('Post: {}\n\t{}\n\tMedia:'.format(post_id, msg, '\n'.join(media)))


# echo
# @bot.message_handler(func=lambda message: True)
# def echo_all(message):
#     bot.reply_to(message, message.text)


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
            chat_id.add(int(line))
    except FileNotFoundError:
        logger.warning(f"\t File not found: {fn_chat_ids}")
    except NameError as e:
        logger.error(r"Exception: " + str(e))
    finally:
        if f:
            f.close()


def save_sent_posts():
    try:
        with open(fn_sent_posts, 'w') as f:
            for item in sent_posts:
                f.write('%s\n' % item)
    except NameError as e:
        logger.error(r"Exception: " + str(e))


def get_new_posts(args):
    while RUN:
        posts = vk.get_posts(args["url"])
        for post_id in list(posts.keys())[::-1]:    # reverse
            if post_id not in sent_posts:
                send_msg(post_id, posts[post_id]['text'], posts[post_id]['media_url'])
                sent_posts.add(post_id)
        save_sent_posts()
        for i in range(args['posts_interval']):
            if not RUN:
                break
            sleep(1)


if __name__ == '__main__':
    conf = {'url': "https://vk.com/covid19nn",
            'posts_interval': 300,
            # 'log_file': r'/tmp/bot.log',
            'log_file': r'./bot.log',
            'log_level': logging.DEBUG}

    logger_init((logger, telebot.logger, vk.logger), conf['log_file'], conf['log_level'])
    load_data()

    logger.info('Chats: \n\t{}'.format("\n\t".join(str(x) for x in chat_id)))

    # run_bot_thread = Thread(target=bot.infinity_polling(), args=(True,), daemon=True)
    get_posts_thread = Thread(target=get_new_posts, args=(conf,), daemon=True)
    # run_bot_thread.start()
    get_posts_thread.start()
    try:
        bot.infinity_polling(none_stop=True)
    except KeyboardInterrupt:
        bot.stop_polling()
        run = False
    bot.stop_polling()
    # run_bot_thread.join()
    get_posts_thread.join()

