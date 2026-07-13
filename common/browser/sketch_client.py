# -*- coding: utf-8 -*-
"""Pixiv Sketch HTTP client methods extracted from PixivBrowser (behaviour-preserving)."""
from __future__ import annotations

from typing import Optional
from urllib.error import HTTPError

import mechanize

import common.PixivHelper as PixivHelper
from common.PixivException import PixivException
from model.PixivModelSketch import SketchArtist, SketchPost


class SketchClientMixin:
    """Mixin providing domain methods; expects PixivBrowser self APIs."""

    def sketch_get_post_by_post_id(self, post_id, artist=None):
        # https://sketch.pixiv.net/api/replies/1213195054130835383.json
        url = f"https://sketch.pixiv.net/api/replies/{post_id}.json"
        referer = f"https://sketch.pixiv.net/items/{post_id}"
        x_requested_with = f'https://sketch.pixiv.net/items/{post_id}'

        PixivHelper.get_logger().debug('Getting sketch post detail from %s', url)
        response = self.getPixivSketchPage(url=url, referer=referer, x_requested_with=x_requested_with)
        self.handleDebugMediumPage(response, post_id)
        _tzInfo = None
        if self._config.useLocalTimezone:
            _tzInfo = PixivHelper.LocalUTCOffsetTimezone()
        post = SketchPost(post_id, artist, response, _tzInfo, self._config.dateFormat)
        return post

    def sketch_get_posts_by_artist_id(self, artist_id, max_page=0):
        # get artist info
        # https://sketch.pixiv.net/api/users/@camori.json
        url = f"https://sketch.pixiv.net/api/users/@{artist_id}.json"
        referer = f"https://sketch.pixiv.net/@{artist_id}"
        x_requested_with = f'https://sketch.pixiv.net/@{artist_id}'

        PixivHelper.get_logger().debug('Getting sketch artist detail from %s', url)
        response = None
        try:
            response = self.getPixivSketchPage(url=url, referer=referer, x_requested_with=x_requested_with)
        except Exception as ex:
            if isinstance(ex, HTTPError) and ex.status == 404:
                raise PixivException(f"No Pixiv Sketch for : {artist_id}", errorCode=PixivException.USER_ID_NOT_EXISTS)
            else:
                raise
        self.handleDebugMediumPage(response, artist_id)
        _tzInfo = None
        if self._config.useLocalTimezone:
            _tzInfo = PixivHelper.LocalUTCOffsetTimezone()
        artist = SketchArtist(artist_id, response, _tzInfo, self._config.dateFormat)

        # get artists posts
        current_page = 1
        while True:
            # https://sketch.pixiv.net/api/walls/@camori/posts/public.json
            url_posts = f"https://sketch.pixiv.net/api/walls/@{artist_id}/posts/public.json"
            if artist.next_page is not None:
                url_posts = f"https://sketch.pixiv.net{artist.next_page}"
            x_requested_with = f'https://sketch.pixiv.net/@{artist_id}'

            PixivHelper.print_and_log("info", f"Getting page {current_page} from {url_posts}")
            response_post = self.getPixivSketchPage(url=url_posts, referer=referer, x_requested_with=x_requested_with)
            self.handleDebugMediumPage(response_post, artist_id)

            PixivHelper.print_and_log("debug", f"{response_post}")
            artist.parse_posts(response_post)

            current_page = current_page + 1
            if max_page != 0 and current_page > max_page:
                break
            if artist.next_page is None:
                break

        return artist

    def getPixivSketchPage(self, url, referer, x_requested_with) -> str:
        p_req = mechanize.Request(url)
        p_req.add_header('Accept', 'application/vnd.sketch-v4+json')
        p_req.add_header('Referer', referer)
        p_req.add_header('X-Requested-With', x_requested_with)
        p_req.add_header('User-Agent', self._config.useragent)

        p_res = self.open_with_retry(p_req)
        assert (p_res is not None)
        response_post = p_res.read()
        return response_post

