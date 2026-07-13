# -*- coding: utf-8 -*-
"""FANBOX HTTP/auth client methods extracted from PixivBrowser (behaviour-preserving)."""
from __future__ import annotations

import http.cookiejar
import re
import sys
from typing import List
from urllib.error import HTTPError

import curl_cffi
import mechanize
from bs4 import BeautifulSoup

import common.FirefoxCookieReader as FirefoxCookieReader
import common.PixivHelper as PixivHelper
import common.PixivJson as PixivJson
from common.PixivException import PixivException
from model.PixivModelFanbox import FanboxArtist, FanboxPost


class FanboxClientMixin:
    """Mixin providing domain methods; expects PixivBrowser self APIs."""

    def _use_browser_fanbox_cookies(self):
        return bool(getattr(self._config, "cookieFanboxFromBrowser", True))

    def _get_firefox_profile_path(self):
        return getattr(self._config, "firefoxProfilePath", "") or ""

    def _get_fanbox_cookies_from_browser(self, force_refresh=False):
        if not self._use_browser_fanbox_cookies():
            return {}

        try:
            cookies = FirefoxCookieReader.get_fanbox_cookies(
                profile_override=self._get_firefox_profile_path(),
                force_refresh=force_refresh,
            )
            if cookies:
                PixivHelper.get_logger().debug(
                    "Loaded %s FANBOX cookies from Firefox profile %s",
                    len(cookies),
                    FirefoxCookieReader.get_cached_profile_path(),
                )
            return cookies
        except Exception:
            PixivHelper.get_logger().warning(
                "Failed to read FANBOX cookies from Firefox: %s", sys.exc_info()
            )
            return {}

    def _sync_fanbox_auth_from_browser(self, cookies):
        if not cookies:
            return None

        fanbox_sessid = cookies.get("FANBOXSESSID")
        if cookies.get("cf_clearance"):
            self._config.cf_clearance = cookies["cf_clearance"]
        if cookies.get("__cf_bm"):
            self._config.cf_bm = cookies["__cf_bm"]
        if fanbox_sessid:
            self._config.cookieFanbox = fanbox_sessid
            if not self._use_browser_fanbox_cookies():
                self._config.cookieFanboxTemp = FirefoxCookieReader.build_cookie_header(cookies)
        return fanbox_sessid

    def _get_fanbox_cookie_header(self, force_refresh=False):
        if self._use_browser_fanbox_cookies():
            header = FirefoxCookieReader.get_fanbox_cookie_header(
                profile_override=self._get_firefox_profile_path(),
                force_refresh=force_refresh,
            )
            if header:
                return header

        if self._config.cookieFanboxTemp:
            return self._config.cookieFanboxTemp
        if self._config.cookieFanbox:
            return f"FANBOXSESSID={self._config.cookieFanbox}"
        return ""

    def fanboxLoginUsingCookie(self, login_cookie=None):
        """  Log in to Pixiv using saved cookie, return True if success """
        result = False
        parsed = ""
        browser_cookies = self._get_fanbox_cookies_from_browser()
        if browser_cookies:
            PixivHelper.print_and_log("info", "Using FANBOX cookies from Firefox")
            browser_login_cookie = self._sync_fanbox_auth_from_browser(browser_cookies)
            if browser_login_cookie:
                login_cookie = browser_login_cookie

        if login_cookie is None or len(login_cookie) == 0:
            login_cookie = self._config.cookieFanbox

        # Issue #1342
        if self._config.cf_clearance != "":
            ck1 = http.cookiejar.Cookie(version=0, name='cf_clearance', value=self._config.cf_clearance, port=None,
                                        port_specified=False, domain='fanbox.cc', domain_specified=False,
                                        domain_initial_dot=False, path='/', path_specified=True,
                                        secure=False, expires=None, discard=True, comment=None,
                                        comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
            self.addCookie(ck1)
        if self._config.cf_bm != "":
            ck2 = http.cookiejar.Cookie(version=0, name='__cf_bm', value=self._config.cf_bm, port=None,
                                        port_specified=False, domain='fanbox.cc', domain_specified=False,
                                        domain_initial_dot=False, path='/', path_specified=True,
                                        secure=False, expires=None, discard=True, comment=None,
                                        comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
            self.addCookie(ck2)

        if len(login_cookie) > 0:
            PixivHelper.print_and_log('info', 'Trying to log in FANBOX with saved cookie')
            # self.clearCookie()
            self._loadCookie(login_cookie, "fanbox.cc")

            req = mechanize.Request("https://www.fanbox.cc")
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
            req.add_header('Origin', 'https://www.fanbox.cc')
            req.add_header('User-Agent', self._config.useragent)
            try:
                res = self.open_with_retry(req)
                parsed = BeautifulSoup(res, features="html5lib")
                PixivHelper.get_logger().info('Logging in with cookie to Fanbox, return url: %s', res.geturl())
                res.close()
            except Exception:
                PixivHelper.get_logger().error('Error at fanboxLoginUsingCookie(): %s', sys.exc_info())
                self.cookiejar.clear("fanbox.cc")

            if '"user":{"isLoggedIn":true' in str(parsed):
                result = True
                self._is_logged_in_to_FANBOX = True
            # Issue #1342
            elif "challenge_basic_security_FANBOX" in str(parsed):
                fanboxErrorPage = parsed.decode('utf-8')
                parsed.decompose()
                del parsed
                raise PixivException("Failed FANBOX Cloudflare CAPTCHA challenge, please check your cookie and user-agent settings.",
                                             errorCode=PixivException.CANNOT_LOGIN, htmlPage=fanboxErrorPage)
            parsed.decompose()
            del parsed

        if result:
            PixivHelper.print_and_log('info', 'FANBOX Login successful.')
        else:
            PixivHelper.print_and_log('info', 'Not logged in to FANBOX, trying to update FANBOX cookie...')
            result = self.updateFanboxCookie()
            self._is_logged_in_to_FANBOX = result

        return result

    def fanbox_is_logged_in(self):
        if not self._is_logged_in_to_FANBOX:
            if not self.fanboxLoginUsingCookie(self._config.cookieFanbox):
                raise Exception("Not logged in to FANBOX")

    def updateFanboxCookie(self):
        p_req = mechanize.Request("https://www.fanbox.cc/login?return_to=https%3A%2F%2Fwww.fanbox.cc%2F")
        p_req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        p_req.add_header('Referer', 'https://www.fanbox.cc')

        try:
            p_res = self.open_with_retry(p_req)
            page = p_res.read().decode("utf-8")
            p_res.close()
        except Exception:
            PixivHelper.get_logger().error('Error at updateFanboxCookie(): %s', sys.exc_info())
            return False

        match = re.search(r"(?<=pixivAccount\.postKey\":\").*?(?=\")", page)
        if not match:
            raise Exception("Could not get pixivAccount.postKey while trying to log into fanbox.cc with given pixiv.net cookie")

        data = {"return_to": "https://www.fanbox.cc/auth/start",
                "tt": match.group()}

        p_req = mechanize.Request("https://accounts.pixiv.net/account-selected", data, method="POST")
        try:
            p_res = self.open_with_retry(p_req)
            parsed = BeautifulSoup(p_res, features="html5lib")
            p_res.close()
        except Exception:
            PixivHelper.get_logger().error('Error at updateFanboxCookie(): %s', sys.exc_info())
            return False

        result = False
        if '"user":{"isLoggedIn":true' in str(parsed):
            result = True
            self._is_logged_in_to_FANBOX = True
        parsed.decompose()
        del parsed

        if result:
            for cookie in self._ua_handlers['_cookies'].cookiejar:
                if cookie.name == 'FANBOXSESSID':
                    PixivHelper.print_and_log(
                        'info', 'New FANBOX cookie value: ' + str(cookie.value))
                    self._config.cookieFanbox = cookie.value
                    if not self._use_browser_fanbox_cookies():
                        self._config.writeConfig(path=self._config.configFileLocation)
                    break
        else:
            PixivHelper.print_and_log('info', 'Could not update FANBOX cookie string.')
        return result

    def fanboxGetArtistList(self, via):
        self.fanbox_is_logged_in()
        url = None
        referer = ""
        if via == FanboxArtist.SUPPORTING:
            url = 'https://api.fanbox.cc/plan.listSupporting'
            PixivHelper.print_and_log('info', f'Getting supporting artists from {url}')
            referer = "https://www.fanbox.cc/"
        elif via == FanboxArtist.FOLLOWING:
            url = 'https://api.fanbox.cc/creator.listFollowing'
            PixivHelper.print_and_log('info', f'Getting following artists from {url}')
            referer = "https://www.fanbox.cc/"

        if url is not None:
            req = mechanize.Request(url)
            req.add_header('Accept', 'application/json, text/plain, */*')
            req.add_header('Referer', referer)
            req.add_header('Origin', 'https://www.fanbox.cc')
            req.add_header('User-Agent', self._config.useragent)

            res = self.open_with_retry(req)
            # read the json response
            response = res.read()
            res.close()

            ids = FanboxArtist.parseArtistCreatorIDs(page=response)
            return ids
        else:
            raise ValueError(f"Invalid via argument {via}")

    def fanboxGetArtistById(self, artist_id, for_suspended=False):
        self.fanbox_is_logged_in()
        if re.match(r"^\d+$", artist_id):
            id_type = "userId"
        else:
            id_type = "creatorId"

        url = f'https://api.fanbox.cc/creator.get?{id_type}={artist_id}'
        PixivHelper.print_and_log('info', f'Getting artist information from {url}')
        referer = "https://www.fanbox.cc"
        if id_type == "creatorId":
            referer += f"/@{artist_id}"

        req = mechanize.Request(url)
        req.add_header('Accept', 'application/json, text/plain, */*')
        req.add_header('Referer', referer)
        req.add_header('Origin', 'https://www.fanbox.cc')
        req.add_header('User-Agent', self._config.useragent)

        res = self.open_with_retry(req)
        # read the json response
        response = res.read()
        res.close()
        _tzInfo = None
        if self._config.useLocalTimezone:
            _tzInfo = PixivHelper.LocalUTCOffsetTimezone()

        js = PixivJson.decode(response)
        if "error" in js and js["error"]:
            raise PixivException("Error when requesting Fanbox", 9999, js)

        if "body" in js and js["body"] is not None:
            js_body = js["body"]
            artist = FanboxArtist(artist_id=js_body["user"]["userId"],
                                  artist_name=js_body["user"]["name"],
                                  creator_id=js_body["creatorId"],
                                  tzInfo=_tzInfo)

            if not for_suspended:
                # pixivArtist = PixivArtist(artist.artistId)
                # self.getMemberInfoWhitecube(artist.artistId, pixivArtist)
                # Issue #827, less efficient call, but it can avoid oAuth issue
                (pixivArtist, _) = self.getMemberPage(artist.artistId)

                artist.artistName = pixivArtist.artistName
                artist.artistToken = pixivArtist.artistToken
            return artist
        else:
            raise PixivException("Id does not exist", errorCode=PixivException.USER_ID_NOT_EXISTS)

    def fanboxGetPostsFromArtist(self, artist: FanboxArtist = None, next_url="") -> List[FanboxPost]:
        ''' get all posts from the supported user
        from https://fanbox.pixiv.net/api/post.listCreator?userId=1305019&limit=10 '''
        self.fanbox_is_logged_in()

        # Issue #641
        if next_url is None or next_url == "":
            url = f"https://api.fanbox.cc/post.paginateCreator?creatorId={artist.creatorId}"
            PixivHelper.print_and_log('info', 'Getting Pages from ' + url)
            referer = "https://www.fanbox.cc/"
            req = mechanize.Request(url)
            req.add_header('Accept', 'application/json, text/plain, */*')
            req.add_header('Referer', referer)
            req.add_header('Origin', 'https://www.fanbox.cc')

            res = self.open_with_retry(req)
            response = res.read()
            PixivHelper.log_payload('debug', 'FANBOX response', response)
            res.close()

            artist.setPages(response)

            # url = f"https://api.fanbox.cc/post.listCreator?userId={artist.artistId}&limit=10"
            # Issue #1094
            # https://api.fanbox.cc/post.listCreator?creatorId=onartworks&maxPublishedDatetime=2022-02-26%2015%3A57%3A17&maxId=3468213&limit=10
            # url = f"https://api.fanbox.cc/post.listCreator?creatorId={artist.creatorId}&limit=10"

            url = artist.Pages[artist.PageIndex]
        elif next_url.startswith("https://"):
            url = next_url
        else:
            url = "https://www.fanbox.cc" + next_url

        # Fix #494
        PixivHelper.print_and_log('info', 'Getting posts from ' + url)
        referer = "https://www.fanbox.cc/"
        req = mechanize.Request(url)
        req.add_header('Accept', 'application/json, text/plain, */*')
        req.add_header('Referer', referer)
        req.add_header('Origin', 'https://www.fanbox.cc')
        req.add_header('User-Agent', self._config.useragent)

        res = self.open_with_retry(req)
        response = res.read()
        PixivHelper.log_payload('debug', 'FANBOX response', response)
        res.close()
        posts = artist.parsePosts(response)
        return posts

    def fanboxUpdatePost(self, post: FanboxPost):
        js = self.fanboxGetPostJsonById(post.imageId, post.parent)
        post.parsePost(js["body"])
        post.parse_post_details(js["body"])

    def fanboxGetPostById(self, post_id):
        js = self.fanboxGetPostJsonById(post_id)
        _tzInfo = None
        if self._config.useLocalTimezone:
            _tzInfo = PixivHelper.LocalUTCOffsetTimezone()
        artist = self.fanboxGetArtistById(js["body"]["creatorId"])
        post = FanboxPost(post_id, artist, js["body"], _tzInfo)
        return post

    def fanboxGetPostJsonById(self, post_id, artist=None):
        self.fanbox_is_logged_in()
        # https://fanbox.pixiv.net/api/post.info?postId=279561
        # https://www.pixiv.net/fanbox/creator/104409/post/279561
        p_url = f"https://api.fanbox.cc/post.info?postId={post_id}"
        # referer doesn't seeem to be essential
        p_referer = f"https://www.fanbox.cc/@{artist.creatorId if artist else ''}/posts/{post_id}"
        PixivHelper.get_logger().debug('Getting post detail from %s', p_url)
        p_req = mechanize.Request(p_url)
        p_req.add_header('Accept', 'application/json, text/plain, */*')
        p_req.add_header('Referer', p_referer)
        p_req.add_header('Origin', 'https://www.fanbox.cc')
        p_req.add_header('User-Agent', self._config.useragent)
        impersonation = self._config.userAgentImpersonation or "firefox135" # default value

        p_response = None
        for attempt in range(2):
            p_req.add_header('Cookie', self._get_fanbox_cookie_header(force_refresh=attempt > 0))
            try:
                p_res = curl_cffi.get(p_url, impersonate=impersonation, headers=p_req.headers)
            except HTTPError as ex:
                if ex.code in [404]:
                    raise PixivException("Fanbox post not found!", PixivException.OTHER_ERROR)
                raise
            p_response = p_res.text
            PixivHelper.log_payload('debug', 'FANBOX post.info', p_response)
            p_res.close()
            if p_response.lstrip().startswith("{"):
                break
            if attempt == 0 and self._use_browser_fanbox_cookies():
                PixivHelper.print_and_log("info", "FANBOX API blocked, refreshing cookies from Firefox...")
                browser_cookies = self._get_fanbox_cookies_from_browser(force_refresh=True)
                self._sync_fanbox_auth_from_browser(browser_cookies)
            else:
                break

        js = PixivJson.decode(p_response)
        # Normalize body.post wrapper (post.info) and other shape variants.
        body = js.get("body")
        normalized = FanboxArtist.normalize_post_payload(body)
        if normalized is not None:
            js["body"] = normalized
        return js

