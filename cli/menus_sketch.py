# -*- coding: utf-8 -*-
"""Menus split from PixivUtil2 — runtime deps via cli.state."""
from __future__ import annotations

import os
import sys

from colorama import Back, Fore, Style

import common.PixivBrowserFactory as PixivBrowserFactory
import common.PixivConstant as PixivConstant
import common.PixivHelper as PixivHelper
import handler.PixivArtistHandler as PixivArtistHandler
import handler.PixivBatchHandler as PixivBatchHandler
import handler.PixivBookmarkHandler as PixivBookmarkHandler
import handler.PixivFanboxHandler as PixivFanboxHandler
import handler.PixivImageHandler as PixivImageHandler
import handler.PixivListHandler as PixivListHandler
import handler.PixivNovelHandler as PixivNovelHandler
import handler.PixivRankingHandler as PixivRankingHandler
import handler.PixivSketchHandler as PixivSketchHandler
import handler.PixivTagsHandler as PixivTagsHandler
import model.PixivModelFanbox as PixivModelFanbox
from common.PixivException import PixivException
from model.PixivTags import PixivTags
from cli import state


def menu_sketch_download_by_artist_id(opisvalid, args, options):
    state.log.info('Download Sketch by Artist ID mode (s1).')
    current_member = 1
    page = 1
    end_page = 0

    if opisvalid and len(args) > 0:
        for member_id in args:
            try:
                prefix = f"Pixiv Sketch [{current_member} of {len(args)}] "
                PixivSketchHandler.process_sketch_artists(state.get_caller(),
                                                          state.config,
                                                          member_id,
                                                          page,
                                                          end_page,
                                                          title_prefix=prefix)
                current_member = current_member + 1
            except PixivException as ex:
                PixivHelper.print_and_log("error", f"Error when processing Pixiv Sketch:{member_id}", ex)
                continue
    else:
        member_ids = input('Artist ids: ').rstrip("\r")
        (page, end_page) = PixivHelper.get_start_and_end_number(total_number_of_page=options.number_of_pages)

        member_ids = PixivHelper.get_ids_from_csv(member_ids, is_string=True)
        PixivHelper.print_and_log('info', f"Artist IDs: {member_ids}")
        for member_id in member_ids:
            try:
                prefix = f"Pixiv Sketch [{current_member} of {len(member_ids)}] "
                PixivSketchHandler.process_sketch_artists(state.get_caller(),
                                                          state.config,
                                                          member_id,
                                                          page,
                                                          end_page,
                                                          title_prefix=prefix)
                current_member = current_member + 1
            except PixivException as ex:
                PixivHelper.print_and_log("error", f"Error when processing Pixiv Sketch:{member_id}", ex)


def menu_sketch_download_by_post_id(opisvalid, args, options):
    state.log.info('Download Sketch by Post ID mode (s2).')
    if opisvalid and len(args) > 0:
        for image_id in args:
            try:
                test_id = int(image_id)
                PixivSketchHandler.process_sketch_post(state.get_caller(),
                                                        state.config,
                                                        image_id)
            except Exception:
                PixivHelper.print_and_log('error', f"Image ID: {image_id} is not valid")
                state.set_error_code(-1)
                continue
    else:
        image_ids = input('Post ids: ').rstrip("\r")
        image_ids = PixivHelper.get_ids_from_csv(image_ids)
        for image_id in image_ids:
            PixivSketchHandler.process_sketch_post(state.get_caller(),
                                                   state.config,
                                                   image_id)


