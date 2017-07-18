# coding:utf-8
from carrybrick.log import send_email


def test_send_email():
    send_email('test, 中文', 'test, 中文')


test_send_email()
