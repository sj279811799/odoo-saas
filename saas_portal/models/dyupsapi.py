#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Nginx Upstream Api for Python By Song """
import requests
import time
import os
from openerp.exceptions import ValidationError


HEADERS = {'Accept': 'application/json'}
TIME = not os.environ.get('TIME_API') is None


def timed_url(fn):
    def wrapped(*args, **kw):
        if TIME:
            start = time.time()
            ret = fn(*args, **kw)
            delta = time.time() - start
            print(delta, args[1], fn.__name__)
            return ret
        else:
            return fn(*args, **kw)
    return wrapped


class NginxClient(object):

    def __init__(self, headers=HEADERS, **kw):
        self._headers = headers
        self._session = requests.Session()

    def _error(self, text):
        raise ValidationError(text)

    @timed_url
    def _get(self, url):
        r = self._session.get(url, headers=self._headers)
        if r.status_code < 200 or r.status_code >= 300:
            self._error(r.text)
        return r.text

    @timed_url
    def _post(self, url, data=None):
        r = self._session.post(url, data=data, headers=self._headers)
        if r.status_code < 200 or r.status_code >= 300:
            self._error(r.text)
        return r.text

    @timed_url
    def _delete(self, url):
        r = self._session.delete(url, headers=self._headers)
        if r.status_code < 200 or r.status_code >= 300:
            self._error(r.text)
        return r.text