# -*- coding: utf-8 -*-
"""Main interactive loop and login."""
from __future__ import annotations

import sys
import traceback

import common.PixivBrowserFactory as PixivBrowserFactory
import common.PixivHelper as PixivHelper
import handler.PixivBatchHandler as PixivBatchHandler
import model.PixivModelFanbox as PixivModelFanbox
from common.PixivException import PixivException
from cli import state
from cli.helpers import (
    menu,
    menu_import_list,
    menu_print_config,
    menu_reload_config,
)
from cli.menus_download import (
    menu_download_by_group_id,
    menu_download_by_image_id,
    menu_download_by_manga_series_id,
    menu_download_by_member_bookmark,
    menu_download_by_member_id,
    menu_download_by_novel_id,
    menu_download_by_novel_series_id,
    menu_download_by_rank,
    menu_download_by_rank_r18,
    menu_download_by_tag_and_member_id,
    menu_download_by_tags,
    menu_download_by_title_caption,
    menu_download_by_unlisted_image_id,
    menu_download_from_list,
    menu_download_from_online_image_bookmark,
    menu_download_from_online_user_bookmark,
    menu_download_from_tags_list,
    menu_download_new_illust_from_bookmark,
    menu_download_new_illusts,
    menu_metadata_by_image_id,
    menu_metadata_by_manga_series_id,
    menu_metadata_by_member_id,
    menu_metadata_by_tag,
    menu_ugoira_reencode,
)
from cli.menus_export import (
    menu_export_database_images,
    menu_export_from_online_image_bookmark,
    menu_export_online_bookmark,
    menu_export_online_user_bookmark,
    menu_export_userId_bookmark,
)
from cli.menus_fanbox import (
    menu_fanbox_download_by_id,
    menu_fanbox_download_by_post_id,
    menu_fanbox_download_from_list,
    menu_fanbox_download_pixiv_by_fanbox_id,
)
from cli.menus_sketch import (
    menu_sketch_download_by_artist_id,
    menu_sketch_download_by_post_id,
)


def main_loop(ewd, op_is_valid, selection, np_is_valid_local, args, options):

    while True:
        try:
            if len(state.error_list) > 0:
                print("Unknown errors from previous operation")
                for err in state.error_list:
                    message = err["type"] + ": " + str(err["id"]) + " ==> " + err["message"]
                    PixivHelper.print_and_log('error', message)
                state.error_list = list()
                state.set_error_code(1)

            if op_is_valid:  # Yavos (next 3 lines): if commandline then use it
                selection = op
            else:
                selection = state.menu()

            if selection == '1':
                menu_download_by_member_id(op_is_valid, args, options)
            elif selection == '2':
                menu_download_by_image_id(op_is_valid, args, options)
            elif selection == '3':
                menu_download_by_tags(op_is_valid, args, options)
            elif selection == '4':
                menu_download_from_list(op_is_valid, args, options)
            elif selection == '5':
                menu_download_from_online_user_bookmark(op_is_valid, args, options)
            elif selection == '6':
                menu_download_from_online_image_bookmark(op_is_valid, args, options)
            elif selection == '7':
                menu_download_from_tags_list(op_is_valid, args, options)
            elif selection == '8':
                menu_download_new_illust_from_bookmark(op_is_valid, args, options)
            elif selection == '9':
                menu_download_by_title_caption(op_is_valid, args, options)
            elif selection == '10':
                menu_download_by_tag_and_member_id(op_is_valid, args, options)
            elif selection == '11':
                menu_download_by_member_bookmark(op_is_valid, args, options)
            elif selection == '12':
                menu_download_by_group_id(op_is_valid, args, options)
            elif selection == '13':
                menu_download_by_manga_series_id(op_is_valid, args, options)
            elif selection == '14':
                menu_download_by_novel_id(op_is_valid, args, options)
            elif selection == '15':
                menu_download_by_novel_series_id(op_is_valid, args, options)
            elif selection == '16':
                menu_download_by_rank(op_is_valid, args, options)
            elif selection == '17':
                menu_download_by_rank_r18(op_is_valid, args, options)
            elif selection == '18':
                menu_download_new_illusts(op_is_valid, args, options)
            elif selection == '19':
                menu_download_by_unlisted_image_id(op_is_valid, args, options)
            elif selection == 'm1':
                menu_metadata_by_member_id(op_is_valid, args, options)
            elif selection == 'm2':
                menu_metadata_by_image_id(op_is_valid, args, options)
            elif selection == 'm3':
                menu_metadata_by_manga_series_id(op_is_valid, args, options)
            elif selection == 'm4':
                menu_metadata_by_tag(op_is_valid, args, options)
            elif selection == "l":
                menu_export_database_images(op_is_valid, args, options)
            elif selection == 'b':
                PixivBatchHandler.process_batch_job(state.get_caller(), batch_file=options.batch_file)
            elif selection == 'e':
                menu_export_online_bookmark(op_is_valid, args, options)
            elif selection == 'm':
                menu_export_online_user_bookmark(op_is_valid, args, options)
            elif selection == 'p':
                menu_export_from_online_image_bookmark(op_is_valid, args, options)
            elif selection == 'u':
                menu_ugoira_reencode(op_is_valid, args, options)
            elif selection == 'd':
                PixivHelper.clearScreen()
                state.db.main()
            elif selection == 'r':
                menu_reload_config()
            elif selection == 'c':
                menu_print_config()
            elif selection == 'z':
                menu_export_userId_bookmark(op_is_valid, args, options)
            elif selection == 'i':
                menu_import_list()

            # PIXIV FANBOX
            elif selection == 'f1':
                menu_fanbox_download_from_list(op_is_valid, PixivModelFanbox.FanboxArtist.SUPPORTING, args, options)
            elif selection == 'f2':
                menu_fanbox_download_by_id(op_is_valid, args, options)
            elif selection == 'f3':
                menu_fanbox_download_by_post_id(op_is_valid, args, options)
            elif selection == 'f4':
                menu_fanbox_download_from_list(op_is_valid, PixivModelFanbox.FanboxArtist.FOLLOWING, args, options)
            elif selection == 'f5':
                menu_fanbox_download_from_list(op_is_valid, PixivModelFanbox.FanboxArtist.CUSTOM, args, options)
            elif selection == 'f6':
                menu_fanbox_download_pixiv_by_fanbox_id(op_is_valid, args, options)
            # END PIXIV FANBOX
            # PIXIV Sketch
            elif selection == 's1':
                menu_sketch_download_by_artist_id(op_is_valid, args, options)
            elif selection == 's2':
                menu_sketch_download_by_post_id(op_is_valid, args, options)
            # END PIXIV Sketch
            elif selection == '-all':
                if not np_is_valid_local:
                    np_is_valid_local = True
                    options.number_of_pages = 0
                    print('download all mode activated')
                else:
                    np_is_valid_local = False
                    print(f'download mode reset to {state.config.numberOfPage} pages')
            elif selection == 'x':
                break

            if ewd:  # Yavos: added lines for "exit when done"
                break
            op_is_valid = False  # Yavos: needed to prevent endless loop
        except KeyboardInterrupt:
            PixivHelper.print_and_log("info", f"Keyboard Interrupt pressed, selection: {selection}")
            PixivHelper.clearScreen()
            print("Restarting...")
            selection = state.menu()
        except EOFError:
            selection = 'x'
            break
        except PixivException as ex:
            if ex.htmlPage is not None:
                filename = f"Dump for {PixivHelper.sanitize_filename(ex.value)}.html"
                PixivHelper.dump_html(filename, ex.htmlPage)
            raise  # keep old behaviour

    return np_is_valid_local, op_is_valid, selection


def doLogin(password, username):
    result = False
    # store username/password for oAuth in case not stored in config.ini
    if username is not None and len(username) > 0:
        state.br._username = username
    if password is not None and len(password) > 0:
        state.br._password = password

    try:
        if len(state.config.cookie) > 0:
            result = state.br.loginUsingCookie()

        # if not result:
        #     result = state.br.login(username, password)

    except Exception:
        PixivHelper.print_and_log('error', f'Error at doLogin(): {sys.exc_info()}')
        PixivHelper.print_and_log('error', f'{traceback.format_exc()}')
        raise PixivException("Cannot Login!", PixivException.CANNOT_LOGIN)
    return result


