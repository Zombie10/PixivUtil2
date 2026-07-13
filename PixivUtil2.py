#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import gc
import getpass
import os
import platform
import re
import subprocess
import sys
import traceback
import pyperclip
from optparse import OptionParser

import colorama
from colorama import Back, Fore, Style

import common.PixivAppContext as PixivAppContext
import common.PixivBrowserFactory as PixivBrowserFactory
import common.PixivConfig as PixivConfig
import common.PixivConstant as PixivConstant
import common.PixivHelper as PixivHelper
import cli.helpers  # registers helpers with cli.state
from cli import state
from cli.main_loop import doLogin, main_loop
from cli.option_parser import setup_option_parser
from cli.helpers import (
    get_list_file_from_options,
    get_start_and_end_page_from_options,
    header,
    menu,
    menu_import_list,
    menu_print_config,
    menu_reload_config,
    read_lists,
    set_console_title,
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
    paste_clipboard_download_by_member_id,
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
from PixivDBManager import PixivDBManager

colorama.init()
DEBUG_SKIP_PROCESS_IMAGE = False
DEBUG_SKIP_DOWNLOAD_IMAGE = False

if platform.system() == "Windows":
    # patch getpass.getpass() for windows to show '*'
    def win_getpass_with_mask(prompt='Password: ', stream=None):
        """Prompt for password with echo off, using Windows getch()."""
        if sys.stdin is not sys.__stdin__:
            return getpass.fallback_getpass(prompt, stream)
        import msvcrt
        for c in prompt:
            msvcrt.putch(c.encode())
        pw = ""
        while 1:
            c = msvcrt.getch().decode()
            if c == '\r' or c == '\n':
                break
            if c == '\003':
                raise KeyboardInterrupt
            if c == '\b':
                pw = pw[:-1]
                print("\b \b", end="")
            else:
                pw = pw + c
                print("*", end="")
        msvcrt.putch('\r'.encode())
        msvcrt.putch('\n'.encode())
        return pw

    getpass.getpass = win_getpass_with_mask
    platform_encoding = 'utf-8-sig'
else:
    platform_encoding = 'utf-8'


script_path = PixivHelper.module_path()

op = ''
ERROR_CODE = 0
UTF8_FS = None

__config__ = PixivConfig.PixivConfig()
configfile = "./config.ini"
__dbManager__ = None
__br__: PixivBrowserFactory.PixivBrowser = None
__blacklistTags = list()
__suppressTags = list()
__log__ = None
__errorList = list()
__blacklistMembers = list()
__blacklistTitles = list()
__valid_options = ()
__seriesDownloaded = []

start_iv = False
dfilename = ""

# Explicit handler context (proxies this module; avoids passing sys.modules everywhere).
__app_context__: PixivAppContext.AppContext | None = None


def get_caller():
    """Return AppContext for handlers (legacy-compatible replacement for sys.modules[__name__])."""
    global __app_context__
    if __app_context__ is None:
        __app_context__ = PixivAppContext.AppContext.bind(sys.modules[__name__])
    return __app_context__

# Main thread #


def main():
    # Bind CLI package to this module before any menu uses state.*
    state.bind(sys.modules[__name__])
    set_console_title()
    header()

    # Option Parser
    global start_iv  # used in download_image
    global dfilename
    global op
    global __br__
    global configfile
    global ERROR_CODE
    global __dbManager__
    global __valid_options
    global __log__

    parser = setup_option_parser()
    (options, args) = parser.parse_args()

    op = options.start_action
    # Re-read after setup_option_parser() (writes via state.set_valid_options).
    valid = __valid_options or getattr(state, "valid_options", ())
    if op in valid:
        op_is_valid = True
        __valid_options = valid
    elif op is None:
        op_is_valid = False
    else:
        op_is_valid = False
        parser.error('%s is not valid operation (valid: %s)' % (op, ", ".join(valid) if valid else "none configured"))
        # Yavos: use print option instead when program should be running even with this error

    ewd = options.exit_when_done
    configfile = options.configlocation

    try:
        if options.number_of_pages is not None:
            options.number_of_pages = int(options.number_of_pages)
            np_is_valid = True
        else:
            np_is_valid = False
    except Exception:
        np_is_valid = False
        parser.error('Value %s used for numberOfPage is not an integer.' % options.number_of_pages)
        # Yavos: use print option instead when program should be running even with this error
        # end new lines by Yavos

    # load the configuration before start using logging!
    try:
        __config__.loadConfig(path=configfile)
        PixivHelper.set_config(__config__)
        __log__ = PixivHelper.get_logger(reload=True)
    except Exception:
        PixivHelper.print_and_log("error", f'Failed to read configuration from {configfile}.')

    __log__.info('###############################################################')
    if len(sys.argv) == 0:
        __log__.info('Starting with no argument..')
    else:
        __log__.info('Starting with argument: [%s].', " ".join(sys.argv))

    PixivHelper.set_log_level(__config__.logLevel)
    if __br__ is None:
        __br__ = PixivBrowserFactory.getBrowser(config=__config__)

    if __config__.checkNewVersion:
        PixivHelper.check_version(__br__, config=__config__)

    selection = None

    # Yavos: adding File for downloadlist
    now = datetime.date.today()
    dfilename = __config__.downloadListDirectory + os.sep + 'Downloaded_on_' + now.strftime('%Y-%m-%d') + '.txt'
    if not re.match(r'[a-zA-Z]:', dfilename):
        dfilename = sys.path[0] + os.sep + dfilename
        # dfilename = sys.path[0].rsplit('\\',1)[0] + '\\' + dfilename #Yavos: only useful for myself
    dfilename = dfilename.replace('\\\\', '\\')
    dfilename = dfilename.replace('\\', os.sep)
    dfilename = dfilename.replace(os.sep + 'library.zip' + os.sep + '.', '')

    directory = os.path.dirname(dfilename)
    if not os.path.exists(directory):
        os.makedirs(directory)
        __log__.info('Creating directory: %s', directory)

    # Yavos: adding IrfanView-Handling
    start_irfan_slide = False
    start_irfan_view = False
    if __config__.startIrfanSlide or __config__.startIrfanView:
        start_iv = True
        start_irfan_slide = __config__.startIrfanSlide
        start_irfan_view = __config__.startIrfanView
    elif options.start_iv is not None:
        start_iv = options.start_iv
        start_irfan_view = True
        start_irfan_slide = False

    if __config__.enablePostProcessing and len(__config__.postProcessingCmd) > 0:
        PixivHelper.print_and_log("warn", f"Post Processing after download is enabled: {__config__.postProcessingCmd}")

    try:
        __dbManager__ = PixivDBManager(root_directory=__config__.rootDirectory, target=__config__.dbPath)
        __dbManager__.createDatabase()
        # Bind handler context after core runtime objects exist.
        global __app_context__
        __app_context__ = PixivAppContext.AppContext.bind(sys.modules[__name__])

        # Housekeeping: prune old url dumps / rotated logs (safe no-op when disabled).
        if getattr(__config__, "enableStartupCleanup", True):
            try:
                import common.PixivCleanup as PixivCleanup
                report = PixivCleanup.run_startup_cleanup(
                    script_path,
                    url_list_keep_days=getattr(__config__, "urlListKeepDays", 30),
                    log_keep_count=getattr(__config__, "logKeepCount", 10),
                )
                if report["url_lists_removed"] or report["logs_removed"]:
                    PixivHelper.print_and_log(
                        "info",
                        f"Startup cleanup: removed {report['url_lists_removed']} url list(s), "
                        f"{report['logs_removed']} old log file(s).",
                    )
            except Exception as cleanup_ex:
                PixivHelper.print_and_log("warn", f"Startup cleanup skipped: {cleanup_ex}")

        if __config__.useList:
            PixivListHandler.import_list(get_caller(), __config__, 'list.txt')

        if __config__.overwrite:
            msg = 'Overwrite enabled.'
            PixivHelper.print_and_log('info', msg)

        if __config__.dayLastUpdated != 0 and __config__.processFromDb:
            PixivHelper.print_and_log('info', 'Only process members where the last update is >= ' + str(__config__.dayLastUpdated) + ' days ago')

        if __config__.dateDiff > 0:
            PixivHelper.print_and_log('info', 'Only process image where day last updated >= ' + str(__config__.dateDiff))

        read_lists()

        # check ffmpeg if ugoira conversion is enabled
        if __config__.createGif or \
           __config__.createApng or \
           __config__.createWebm or \
           __config__.createWebp:

            # if not os.path.exists(os.path.abspath(__config__.ffmpeg)):
            #     raise PixivException(f"Cannot find ffmpeg executables at {os.path.abspath(__config__.ffmpeg)}, please update the path (including.exe) in config.ini")

            import shlex
            cmd = f"{__config__.ffmpeg} -encoders"
            ffmpeg_args = shlex.split(cmd, posix=False)
            try:
                p = subprocess.run(ffmpeg_args, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, check=True)
                buff = p.stdout
                if buff.find(__config__.ffmpegCodec) == 0:
                    __config__.createWebm = False
                    PixivHelper.print_and_log('error', f'{"#" * 80}')
                    PixivHelper.print_and_log('error', f'Missing {__config__.ffmpegCodec} encoder, createWebm disabled.')
                    PixivHelper.print_and_log('error', f'Command used: {cmd}')
                    PixivHelper.print_and_log('info', f'Please download ffmpeg with {__config__.ffmpegCodec} encoder enabled.')
                    PixivHelper.print_and_log('error', f'{"#" * 80}')
                if p.returncode != 0:
                    PixivHelper.print_and_log('warn', f'Failed to run ffmpeg succesfully, returned exit code = {p.returncode}, expected to return 0.')
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                PixivHelper.print_and_log('error', f'{"#" * 80}')
                PixivHelper.print_and_log('error', f'Failed to load ffmpeg: {exc_value}')
                PixivHelper.print_and_log('error', f'Command used: [{cmd}]')
                ffmpeg_url = Back.LIGHTWHITE_EX + Fore.BLUE + "https://ffmpeg.org/download.html#get-packages" + Style.RESET_ALL
                PixivHelper.print_and_log('info', f'Please update your config.ini and/or download latest ffmpeg executables from {ffmpeg_url}.')
                PixivHelper.print_and_log('error', f'{"#" * 80}')
                return

        if __config__.useLocalTimezone:
            PixivHelper.print_and_log("info", f"Using local timezone: {PixivHelper.LocalUTCOffsetTimezone()}")

        print(f"{Fore.RED}{Style.BRIGHT}Username login is broken, use Cookies to log in.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}See Q3. at {Fore.CYAN}{Style.BRIGHT}https://github.com/Nandaka/PixivUtil2?tab=readme-ov-file#a-usage{Style.RESET_ALL}")

        username = __config__.username
        password = __config__.password
        if not username or not password:
            print(f"{Fore.RED}{Style.BRIGHT}No username and/or password found in config.ini{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{Style.BRIGHT}See {Fore.CYAN}{Style.BRIGHT}https://github.com/Nandaka/PixivUtil2?tab=readme-ov-file#authentication{Style.RESET_ALL}")

        if np_is_valid and options.number_of_pages != 0:  # Yavos: overwrite config-data
            PixivHelper.print_and_log("info", f'Limit up to: {options.number_of_pages} page(s). (set via commandline)')
        elif __config__.numberOfPage != 0:
            PixivHelper.print_and_log("info", f'Limit up to: {__config__.numberOfPage} page(s).')

        result = doLogin(password, username)

        if result:
            # Pass CLI start_action as selection (main_loop used to read global `op`).
            selection = op
            np_is_valid, op_is_valid, selection = main_loop(ewd, op_is_valid, selection, np_is_valid, args, options)

            if start_iv:  # Yavos: adding start_irfan_view-handling
                PixivHelper.start_irfanview(dfilename, __config__.IrfanViewPath, start_irfan_slide, start_irfan_view)
        else:
            ERROR_CODE = PixivException.NOT_LOGGED_IN
    except PixivException as pex:
        PixivHelper.print_and_log('error', pex.message)
        ERROR_CODE = pex.errorCode
    except Exception as ex:
        if __config__.logLevel == "DEBUG":
            import traceback
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            __log__.exception('Unknown Error: %s', str(exc_value))
        PixivHelper.print_and_log("error", f"Unknown Error, please check the log file: {sys.exc_info()}")
        ERROR_CODE = getattr(ex, 'errorCode', -1)
    finally:
        __dbManager__.close()
        if not ewd:  # Yavos: prevent input on exit_when_done
            if selection is None or selection != 'x':
                input('press enter to exit.').rstrip("\r")
        __log__.setLevel("INFO")
        __log__.info('EXIT: %s', ERROR_CODE)
        __log__.info('###############################################################')
        sys.exit(ERROR_CODE)


if __name__ == '__main__':
    if not sys.version_info >= (3, 7):
        print("Require Python 3.7++")
    else:
        gc.enable()
        # gc.set_debug(gc.DEBUG_STATS)
        main()
        gc.collect()
        gc.collect()
