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


def menu_export_database_images(opisvalid, args, options):
    state.log.info('Export local database (l)')
    use_pixiv = "n"   # y|n|o
    use_fanbox = "n"  # y|n|o
    use_sketch = "n"  # y|n|o
    filename = "export-database.txt"

    if opisvalid:
        if options.export_filename is not None:
            filename = options.export_filename
        if options.use_pixiv is not None:
            use_pixiv = options.use_pixiv
            if use_pixiv not in ('y', 'n', 'o'):
                PixivHelper.print_and_log("error", f"Invalid args for Pixiv database: {use_pixiv}, valid values are [y/n/o].")
                return
        if options.use_fanbox is not None:
            use_fanbox = options.use_fanbox
            if use_fanbox not in ('y', 'n', 'o'):
                PixivHelper.print_and_log("error", f"Invalid args for Fanbox database: {use_fanbox}, valid values are [y/n/o].")
                return
        if options.use_sketch is not None:
            use_sketch = options.use_sketch
            if use_sketch not in ('y', 'n', 'o'):
                PixivHelper.print_and_log("error", f"Invalid args for Sketch database: {use_sketch}, valid values are [y/n/o].")
                return

    else:
        filename = input("Filename: ").rstrip("\r") or filename
        arg = input("Include Pixiv database [y/n/o, default is no]: ").rstrip("\r") or 'n'
        use_pixiv = arg.lower()
        if use_pixiv not in ('y', 'n', 'o'):
            PixivHelper.print_and_log("error", f"Invalid args for Fanbox database: {arg}, valid values are [y/n/o].")
            return
        arg = input("Include Fanbox database [y/n/o, default is no]: ").rstrip("\r") or 'n'
        use_fanbox = arg.lower()
        if use_fanbox not in ('y', 'n', 'o'):
            PixivHelper.print_and_log("error", f"Invalid args for Fanbox database: {arg}, valid values are [y/n/o].")
            return
        arg = input("Include Sketch database [y/n/o, default is no]: ").rstrip("\r") or 'n'
        use_sketch = arg.lower()
        if use_sketch not in ('y', 'n', 'o'):
            PixivHelper.print_and_log("error", f"Invalid args for Sketch database: {arg}, valid values are [y/n/o].")
            return
    PixivBookmarkHandler.export_image_table(state.get_caller(), filename, use_pixiv, use_fanbox, use_sketch)


def menu_export_online_bookmark(opisvalid, args, options):
    state.log.info('Export Followed Artists mode (e).')
    hide = "y"  # y|n|o
    filename = "export.txt"

    if opisvalid:
        if options.export_filename is not None:
            filename = options.export_filename
        if options.bookmark_flag is not None:
            hide = options.bookmark_flag.lower()
            if hide not in ('y', 'n', 'o'):
                PixivHelper.print_and_log("error", f"Invalid args for bookmark_flag: {hide}, valid values are [y/n/o].")
                return
    else:
        filename = input("Filename: ").rstrip("\r")
        arg = input("Include Private bookmarks [y/n/o, default is no]: ").rstrip("\r") or 'n'
        hide = arg.lower()
        if hide not in ('y', 'n', 'o'):
            PixivHelper.print_and_log("error", f"Invalid args for bookmark_flag: {arg}, valid values are [y/n/o].")
            return

    PixivBookmarkHandler.export_bookmark(state.get_caller(), state.config, filename, hide)


def menu_export_online_user_bookmark(opisvalid, args, options):
    state.log.info('Export Other\'s Followed Artist mode (m).')
    member_id = ''
    filename = "export-user.txt"

    if opisvalid and len(args) > 0:
        arg = args[0]  # member id
        if options.export_filename is not None:
            filename = options.export_filename
        else:
            filename = f"export-user-{arg}.txt"
    else:
        filename = input("Filename: ").rstrip("\r") or filename
        arg = input("Member Id: ").rstrip("\r") or ''
        arg = arg.lower()

    if arg.isdigit():
        member_id = arg
    else:
        print("Invalid args, member id is expected: ", arg)
        return

    PixivBookmarkHandler.export_bookmark(state.get_caller(), state.config, filename, 'n', 1, 0, member_id)


def menu_export_from_online_image_bookmark(opisvalid, args, options):
    state.log.info("Export User's Image Bookmark mode (p).")
    start_page = 1
    end_page = 0
    hide = 'n'
    tag = ''
    use_image_tag = False
    filename = "Exported_images.txt"

    if opisvalid:
        if len(args) > 0:
            tag = args[0]

        (start_page, end_page) = state.get_start_and_end_page_from_options(options)
        if options.bookmark_flag is not None:
            hide = options.bookmark_flag.lower()
            if hide not in ('y', 'n', 'o'):
                PixivHelper.print_and_log("error", f"Invalid args for bookmark_flag: {options.bookmark_flag}, valid values are [y/n/o].")
                return
        use_image_tag = options.use_image_tag
        if options.export_filename is not None:
            filename = options.export_filename
    else:
        hide = input("Include Private bookmarks [y/n/o, default is no]: ").rstrip("\r") or 'n'
        hide = hide.lower()
        if hide not in ('y', 'n', 'o'):
            print("Invalid args: ", hide)
            return
        tag = input("Tag (press enter for all images): ").rstrip("\r") or ''
        (start_page, end_page) = PixivHelper.get_start_and_end_number(total_number_of_page=options.number_of_pages)
        if tag != '':
            use_image_tag = input("Use Image Tags as the filter [y/n, default is no]? ").rstrip("\r") or 'n'
            use_image_tag = use_image_tag.lower()
            use_image_tag = True if use_image_tag == 'y' else False
        filename = input(f"Filename (default is '{filename}'): ").rstrip("\r") or filename

    PixivBookmarkHandler.export_image_bookmark(state.get_caller(),
                                                state.config,
                                                hide=hide,
                                                start_page=start_page,
                                                end_page=end_page,
                                                tag=tag,
                                                use_image_tag=use_image_tag,
                                                filename=filename)


def menu_export_userId_bookmark(opisvalid, args, options):
    state.log.info("Export User's Bookmark mode (z).")

    # === Parámetro --b para páginas de bookmarks ===
    bookmark_pages = state.config.numberOfPage
    if opisvalid and hasattr(options, 'bookmark_pages') and options.bookmark_pages is not None:
        bookmark_pages = int(options.bookmark_pages)

    start_page = 1
    end_page = bookmark_pages            # ←←← Esto es lo que controla --b
    hide = 'n'                           # siempre sin bookmarks privados
    tag = ''
    use_image_tag = False
    filename = "Exported_userId_bookmark.txt"
    copy_clipboard = True                # siempre copiar al portapapeles
    download_userId_bookmark = True      # always download after exporting to clipboard

    if opisvalid:
        if len(args) > 0:
            tag = args[0]
        #(start_page, end_page) = state.get_start_and_end_page_from_options(options)
        if options.bookmark_flag is not None:
            hide = options.bookmark_flag.lower()
            if hide not in ('y', 'n', 'o'):
                PixivHelper.print_and_log("error", f"Invalid args for bookmark_flag: {options.bookmark_flag}, valid values are [y/n/o].")
                return
        use_image_tag = options.use_image_tag
        if options.export_filename is not None:
            filename = options.export_filename

    PixivBookmarkHandler.export_userId_bookmark(state.get_caller(),
                                                state.config,
                                                hide=hide,
                                                start_page=start_page,
                                                end_page=end_page,
                                                tag=tag,
                                                use_image_tag=use_image_tag,
                                                filename=filename,
                                                copy_clipboard=copy_clipboard)

    if download_userId_bookmark:
        paste_clipboard_download_by_member_id(opisvalid, args, options)


def paste_clipboard_download_by_member_id(opisvalid, args, options):
    state.log.info('Member id mode from clipboard (z → download).')
    current_member = 1
    include_sketch = False   # siempre False (no se pregunta)

    # Usar valores de línea de comandos si existen, sino preguntar
    if opisvalid:
        start_page = int(options.start_page) if options.start_page else 1
        end_page = int(options.end_page) if options.end_page else state.config.numberOfPage
    else:
        try:
            start_page = int(input('Start Page (default=1): ').rstrip("\r") or "1")
        except ValueError:
            start_page = 1

        end_page = state.config.numberOfPage
        try:
            end_input = input(f'End Page (default= {end_page}, 0 for no limit): ').rstrip("\r")
            if end_input:
                end_page = int(end_input)
        except ValueError:
            pass

    member_ids = PixivHelper.get_ids_from_csv(pyperclip.paste())
    PixivHelper.print_and_log('info', f"Member IDs: {member_ids}")

    import common.PixivRunStats as PixivRunStats
    stats = PixivRunStats.reset_stats(mode="clipboard_member_ids")

    for member_id in member_ids:
        try:
            prefix = f"[{current_member} of {len(member_ids)}] "
            PixivArtistHandler.process_member(state.get_caller(),
                                              state.config,
                                              member_id,
                                              page=start_page,
                                              end_page=end_page,
                                              title_prefix=prefix)
            stats.record_artist_ok()
            current_member = current_member + 1
        except PixivException as ex:
            PixivHelper.print_and_log('error', f"Member ID: {member_id} is not valid")
            state.set_error_code(-1)
            stats.record_artist_error(f"{member_id}: {ex}")
            continue
        except Exception as ex:
            PixivHelper.print_and_log('error', f"Member ID: {member_id} failed: {ex}")
            state.log.exception("clipboard member download failed: %s", member_id)
            state.set_error_code(-1)
            stats.record_artist_error(f"{member_id}: {ex}")
            continue
    PixivRunStats.finish_stats(PixivHelper.print_and_log)
    print("\n✅ Download completed.")


