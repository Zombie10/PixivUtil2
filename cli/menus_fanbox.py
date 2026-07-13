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


def menu_fanbox_download_from_list(op_is_valid, via, args, options):
    via_type = ""
    if via == PixivModelFanbox.FanboxArtist.SUPPORTING:
        via_type = "supporting"
    elif via == PixivModelFanbox.FanboxArtist.FOLLOWING:
        via_type = "following"
    elif via == PixivModelFanbox.FanboxArtist.CUSTOM:
        via_type = "custom"

    state.log.info(f'Download FANBOX {via_type.capitalize()} list mode (f1/f4/f5).')

    if op_is_valid:
        (page, end_page) = state.get_start_and_end_page_from_options(options)
    else:
        end_page = int(input("End Page (default is 0) = ").rstrip("\r") or 0)

    import common.PixivCheckpoint as PixivCheckpoint
    import common.PixivRunStats as PixivRunStats

    stats = PixivRunStats.reset_stats(mode=f"fanbox_{via_type}")

    ids = list()
    if via in [PixivModelFanbox.FanboxArtist.SUPPORTING, PixivModelFanbox.FanboxArtist.FOLLOWING]:
        ids = state.br.fanboxGetArtistList(via)
    elif via == PixivModelFanbox.FanboxArtist.CUSTOM:
        list_file_name = state.config.listPathFanbox
        if op_is_valid:
            list_file_name = state.get_list_file_from_options(options, list_file_name)
        if os.path.isfile(list_file_name):
            with PixivHelper.open_text_file(list_file_name) as reader:
                while True:
                    line = reader.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line.startswith("#"):
                        continue
                    ids.append(line)

    if not ids:
        PixivHelper.print_and_log("info", f"No artist in {via_type} list!")
        return
    PixivHelper.print_and_log("info", f"Found {len(ids)} artist(s) in {via_type} list")
    PixivHelper.print_and_log(None, f"{ids}")

    # Optional checkpoint/resume for long FANBOX list runs.
    checkpoint = None
    use_checkpoint = getattr(state.config, "enableCheckpoint", True)
    if use_checkpoint:
        checkpoint_path = getattr(state.config, "checkpointPathFanbox", "") or f"./checkpoint_fanbox_{via_type}.json"
        checkpoint = PixivCheckpoint.PixivCheckpoint(checkpoint_path, mode=f"fanbox_{via_type}")
        resume = True
        if op_is_valid and getattr(options, "no_resume", False):
            resume = False
            checkpoint.clear()
            checkpoint = PixivCheckpoint.PixivCheckpoint(checkpoint_path, mode=f"fanbox_{via_type}")
        if resume and checkpoint.completed:
            pending = checkpoint.filter_pending(ids)
            PixivHelper.print_and_log(
                "info",
                f"Resuming FANBOX {via_type}: {len(checkpoint.completed)} done, {len(pending)} pending "
                f"(checkpoint: {checkpoint_path})",
            )
            ids = pending
            if not ids:
                PixivHelper.print_and_log("info", "All artists already completed in checkpoint.")
                PixivRunStats.finish_stats(PixivHelper.print_and_log)
                return

    total = len(ids)
    for index, artist_id in enumerate(ids, start=1):
        # Issue #567 — never abort the whole list on a single artist failure.
        try:
            ok = PixivFanboxHandler.process_fanbox_artist_by_id(
                state.get_caller(),
                state.config,
                artist_id,
                end_page,
                title_prefix=f"{index} of {total}",
            )
            if checkpoint is not None:
                if ok is False:
                    checkpoint.mark_failed(artist_id)
                else:
                    checkpoint.mark_done(artist_id)
        except KeyboardInterrupt:
            choice = input("Keyboard Interrupt detected, continue to next artist (Y/N)").rstrip("\r")
            if choice.upper() == 'N':
                PixivHelper.print_and_log("info", f"Artist id: {artist_id}, processing aborted")
                if checkpoint is not None:
                    checkpoint.mark_failed(artist_id)
                break
            else:
                continue
        except PixivException as pex:
            PixivHelper.print_and_log(
                "error",
                f"Error processing FANBOX Artist in {via_type} list: {artist_id} ==> {pex.message}",
            )
            stats.record_artist_error(f"{artist_id}: {pex.message}")
            if checkpoint is not None:
                checkpoint.mark_failed(artist_id)
            continue
        except Exception as ex:
            PixivHelper.print_and_log(
                "error",
                f"Unexpected error processing FANBOX Artist in {via_type} list: {artist_id} ==> {ex}",
            )
            state.log.exception("FANBOX list artist failed: %s", artist_id)
            stats.record_artist_error(f"{artist_id}: {ex}")
            if checkpoint is not None:
                checkpoint.mark_failed(artist_id)
            continue

    PixivRunStats.finish_stats(PixivHelper.print_and_log)


def menu_fanbox_download_by_post_id(op_is_valid, args, options):
    state.log.info('Download FANBOX by post id mode (f3).')
    if op_is_valid and len(args) > 0:
        post_ids = args
    else:
        post_ids = input("Post ids = ").rstrip("\r")
        post_ids = PixivHelper.get_ids_from_csv(post_ids)

    for post_id in post_ids:
        try:
            post = state.br.fanboxGetPostById(post_id)
            PixivFanboxHandler.process_fanbox_post(state.get_caller(), state.config, post, post.parent)
            del post
        except KeyboardInterrupt:
            choice = input("Keyboard Interrupt detected, continue to next post (Y/N)").rstrip("\r")
            if choice.upper() == 'N':
                PixivHelper.print_and_log("info", f"Post id: {post_id}, processing aborted")
                break
            else:
                continue
        except PixivException as pex:
            PixivHelper.print_and_log("error", f"Error processing FANBOX post: {post_id} ==> {pex.message}")


def menu_fanbox_download_by_id(op_is_valid, args, options):
    state.log.info('Download FANBOX by Artist or Creator ID mode (f2).')

    if op_is_valid and len(args) > 0:
        (page, end_page) = state.get_start_and_end_page_from_options(options)
        member_ids = args

    else:
        member_ids = input("Artist/Creator IDs = ").rstrip("\r")
        end_page = int(input("End page (default is 0) = ").rstrip("\r") or 0)
        member_ids = PixivHelper.get_ids_from_csv(member_ids, is_string=True)

    PixivHelper.print_and_log('info', f"Member IDs: {member_ids}")

    for index, member_id in enumerate(member_ids, start=1):
        try:
            PixivFanboxHandler.process_fanbox_artist_by_id(state.get_caller(),
                                                           state.config,
                                                           member_id,
                                                           end_page,
                                                           title_prefix=f"{index} of {len(member_ids)}")
        except KeyboardInterrupt:
            choice = input("Keyboard Interrupt detected, continue to next artist (Y/N)").rstrip("\r")
            if choice.upper() == 'N':
                PixivHelper.print_and_log("info", f"Artist id: {member_id}, processing aborted")
                break
            else:
                continue
        except PixivException as pex:
            PixivHelper.print_and_log("error", f"Error processing FANBOX Artist: {member_id} ==> {pex.message}")


def menu_fanbox_download_pixiv_by_fanbox_id(op_is_valid, args, options):
    state.log.info('Download FANBOX by Artist or Creator ID mode (f6).')

    if op_is_valid and len(args) > 0:
        (start_page, end_page) = state.get_start_and_end_page_from_options(options)
        member_ids = args
    else:
        member_ids = input("Artist/Creator IDs = ").rstrip("\r")
        start_page = int(input("Start page (default is 0) = ").rstrip("\r") or 0)
        end_page = int(input("End page (default is 0) = ").rstrip("\r") or 0)

    member_ids = PixivHelper.get_ids_from_csv(member_ids, is_string=True)
    PixivHelper.print_and_log('info', f"Member IDs: {member_ids}")

    for index, member_id in enumerate(member_ids, start=1):
        try:
            PixivFanboxHandler.process_pixiv_by_fanbox_id(state.get_caller(),
                                                           state.config,
                                                           member_id,
                                                           start_page=start_page,
                                                           end_page=end_page,
                                                           title_prefix=f"{index} of {len(member_ids)}")
        except KeyboardInterrupt:
            choice = input("Keyboard Interrupt detected, continue to next artist (Y/N)").rstrip("\r")
            if choice.upper() == 'N':
                PixivHelper.print_and_log("info", f"Artist id: {member_id}, processing aborted")
                break
            else:
                continue
        except PixivException as pex:
            PixivHelper.print_and_log("error", f"Error processing FANBOX Artist: {member_id} ==> {pex.message}")


