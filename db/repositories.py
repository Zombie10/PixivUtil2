# -*- coding: utf-8 -*-
"""
Repository façades over PixivDBManager.

These do **not** change the SQLite schema. They only group existing
select/insert/update methods by domain so handlers can depend on a
narrower API and unit tests can mock per domain.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional


class _BaseRepo:
    def __init__(self, db):
        self._db = db

    @property
    def db(self):
        return self._db


class MemberRepository(_BaseRepo):
    def select_by_id(self, member_id):
        return self._db.selectMemberByMemberId(member_id)

    def select_by_id2(self, member_id):
        return self._db.selectMemberByMemberId2(member_id)

    def select_all(self):
        return self._db.selectAllMember()

    def select_by_last_download_date(self, days):
        return self._db.selectMembersByLastDownloadDate(days)

    def update_name(self, member_id, member_name, member_token):
        return self._db.updateMemberName(member_id, member_name, member_token)


class ImageRepository(_BaseRepo):
    def select_by_id(self, image_id):
        return self._db.selectImageByImageId(image_id)

    def select_by_id_and_page(self, image_id, page):
        return self._db.selectImageByImageIdAndPage(image_id, page)

    def select_by_member(self, member_id):
        if hasattr(self._db, "selectImageByMemberId"):
            return self._db.selectImageByMemberId(member_id)
        return None

    def insert(self, *args, **kwargs):
        return self._db.insertImage(*args, **kwargs)


class FanboxRepository(_BaseRepo):
    def select_post(self, post_id):
        return self._db.selectPostByPostId(post_id)

    def insert_post(self, *args, **kwargs):
        return self._db.insertPost(*args, **kwargs)

    def insert_post_images(self, rows: Iterable):
        return self._db.insertPostImages(rows)

    def update_post_date(self, post_id, updated_date):
        return self._db.updatePostUpdateDate(post_id, updated_date)

    def select_image_by_page(self, image_id, page):
        return self._db.selectFanboxImageByImageIdAndPage(image_id, page)


class SketchRepository(_BaseRepo):
    def select_image_by_page(self, image_id, page):
        return self._db.selectSketchImageByImageIdAndPage(image_id, page)


class Repositories:
    """Bundle of domain repositories sharing one PixivDBManager connection."""

    def __init__(self, db_manager):
        self.raw = db_manager  # escape hatch for full API
        self.members = MemberRepository(db_manager)
        self.images = ImageRepository(db_manager)
        self.fanbox = FanboxRepository(db_manager)
        self.sketch = SketchRepository(db_manager)

    @classmethod
    def from_caller(cls, caller) -> "Repositories":
        return cls(caller.__dbManager__)
