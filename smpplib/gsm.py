# -*- coding: utf8 -*-
import binascii
import random

from . import consts
from . import exceptions


# from http://stackoverflow.com/questions/2452861/python-library-for-converting-plain-text-ascii-into-gsm-7-bit-character-set
gsm = ("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>"
       "?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ`¿abcdefghijklmnopqrstuvwxyzäöñüà")
ext = ("````````````````````^```````````````````{}`````\\````````````[~]`"
       "|````````````````````````````````````€``````````````````````````")


class EncodeError(ValueError):
    """Raised if text cannot be represented in gsm 7-bit encoding"""


def gsm_encode(plaintext: str, hex=False):
    """Replace non-GSM ASCII symbols"""
    res = ""
    for c in plaintext:
        idx = gsm.find(c)
        if idx != -1:
            res += chr(idx)
            continue
        idx = ext.find(c)
        if idx != -1:
            res += chr(27) + chr(idx)
            continue
        raise EncodeError()
    return binascii.b2a_hex(res) if hex else res


def make_parts(text: str) -> tuple:
    """Returns tuple(parts, encoding, esm_class)"""
    try:
        text = gsm_encode(text)
        encoding = consts.SMPP_ENCODING_DEFAULT
        need_split = len(text) > consts.SEVENBIT_SIZE
        partsize = consts.SEVENBIT_MP_SIZE
        encode = lambda s: s
    except EncodeError:
        encoding = consts.SMPP_ENCODING_ISO10646
        need_split = len(text) > consts.UCS2_SIZE
        partsize = consts.UCS2_MP_SIZE
        encode = lambda s: s.encode('utf-16-be')

    esm_class = consts.SMPP_MSGTYPE_DEFAULT

    if need_split:
        esm_class = consts.SMPP_GSMFEAT_UDHI

        starts = tuple(range(0, len(text), partsize))
        if len(starts) > 255:
            raise exceptions.MessageTooLong()

        parts = []
        ipart = 1
        uid = random.randint(0, 127)
        start_symbols = chr(5) + chr(0) + chr(3)
        sequence_start = start_symbols.encode('utf-8')
        for start in starts:
            sequence_middle = chr(uid).encode('utf-8') + chr(len(starts)).encode('utf-8') + chr(ipart).encode('utf-8')
            str_string = sequence_start + sequence_middle + encode(text[start:start + partsize])
            parts.append(str_string)
            ipart += 1
    else:
        parts = (encode(text),)

    return parts, encoding, esm_class
