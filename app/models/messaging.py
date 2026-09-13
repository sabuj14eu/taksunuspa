# -*- coding: utf-8 -*-
"""A record of every message the site tried to send.

Without this, "did the therapist get the booking?" has no answer. Each attempt
is logged with its outcome, so a misconfigured gateway shows up as a list of
failures rather than as silence.
"""
from datetime import datetime

from ..extensions import db


class MessageLog(db.Model):
    __tablename__ = "message_log"
    id = db.Column(db.Integer, primary_key=True)
    channel = db.Column(db.String(16))          # whatsapp | telegram
    purpose = db.Column(db.String(30))          # new_booking | therapist_assigned ...
    recipient = db.Column(db.String(60))        # number or chat id
    recipient_name = db.Column(db.String(80))
    body = db.Column(db.Text)
    ok = db.Column(db.Boolean, default=False)
    detail = db.Column(db.String(300))          # provider response or the error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
