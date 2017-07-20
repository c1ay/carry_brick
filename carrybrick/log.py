# coding: utf-8
import logging
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from logging import handlers
from datetime import datetime

HOST = 'smtp.qq.com'
FROM = ''
TO = ''

USERNAME = ''
PASSWD = ''


def get_logger(name, log_dir='log'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # log_file_name = '{}/{}.log'.format(log_dir, datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
    # file_handler = logging.FileHandler(log_file_name)
    # file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    # file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def email_logger(subject='数字货币每日搬砖'):
    logger = logging.getLogger('email_logger')
    logger.setLevel(logging.DEBUG)
    # subject = "数字货币搬砖{}收益".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    email_handler = handlers.SMTPHandler(HOST, FROM, TO, subject, (USERNAME, PASSWD), secure=None)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    email_handler.setFormatter(formatter)
    logger.addHandler(email_handler)
    return logger


def send_email(title, msg, to=TO):
    handle = smtplib.SMTP_SSL(HOST, 465, timeout=5)
    handle.login(USERNAME, PASSWD)
    msg = MIMEText(str(msg), "plain", "utf-8")
    msg['From'] = FROM
    msg["Subject"] = Header(title, 'utf-8').encode()
    msg["To"] = to
    try:
        handle.sendmail(FROM, [to], msg.as_string())
    except Exception as e:
        print(e)
        handle.quit()
        return
    handle.quit()
