# -*- coding: utf-8 -*-
"""CLI UI helpers and utility menus."""
from __future__ import annotations

import os

from colorama import Back, Fore, Style

import common.PixivConstant as PixivConstant
import common.PixivHelper as PixivHelper
import handler.PixivListHandler as PixivListHandler
from model.PixivTags import PixivTags
from cli import state


def get_start_and_end_page_from_options(options):
    ''' Try to parse start and end page from options.'''
    page_num = 1
    if options.start_page is not None:
        try:
            page_num = int(options.start_page)
            print(f"Start Page = {page_num}")
        except Exception:
            print(f"Invalid page number: {options.start_page}")
            raise

    end_page_num = 0
    if options.end_page is not None:
        try:
            end_page_num = int(options.end_page)
            print(f"End Page = {end_page_num}")
        except Exception:
            print(f"Invalid end page number: {options.end_page}")
            raise
    elif options.number_of_pages is not None:
        end_page_num = options.number_of_pages
    else:
        end_page_num = state.config.numberOfPage

    if page_num > end_page_num and end_page_num != 0:
        print(f"Start Page ({page_num}) is bigger than End Page ({end_page_num}), assuming as page count ({page_num + end_page_num}).")
        end_page_num = page_num + end_page_num

    return page_num, end_page_num


def get_list_file_from_options(options, default_list_file):
    list_file_name = default_list_file
    if options.list_file is not None:
        if os.path.isabs(options.list_file):
            test_file_name = options.list_file
        else:
            test_file_name = state.config.downloadListDirectory + os.sep + options.list_file
        test_file_name = os.path.abspath(test_file_name)
        if os.path.exists(test_file_name):
            list_file_name = test_file_name
        else:
            PixivHelper.print_and_log("warn", f"The given list file [{test_file_name}] doesn't exists, using default list file [{list_file_name}].")

    return list_file_name


def header():
    PADDING = 60
    print("┌" + "".ljust(PADDING - 2, "─") + "┐")
    print("│ " + Fore.YELLOW + Back.BLACK + Style.BRIGHT + f"PixivDownloader2 version {PixivConstant.PIXIVUTIL_VERSION}".ljust(PADDING - 3, " ") + Style.RESET_ALL + "│")
    print("│ " + Fore.CYAN + Back.BLACK + Style.BRIGHT + PixivConstant.PIXIVUTIL_LINK.ljust(PADDING - 3, " ") + Style.RESET_ALL + "│")
    print("│ " + Fore.YELLOW + Back.BLACK + Style.BRIGHT + f"Donate at {Fore.CYAN}{Style.BRIGHT}{PixivConstant.PIXIVUTIL_DONATE}".ljust(PADDING + 6, " ") + Style.RESET_ALL + "│")
    print("└" + "".ljust(PADDING - 2, "─") + "┘")


def menu():
    PADDING = 60
    set_console_title()
    header()
    print(Style.BRIGHT + '── Pixiv '.ljust(PADDING, "─") + Style.RESET_ALL)
    print(' 1.  Download by member_id')
    print(' 2.  Download by image_id')
    print(' 3.  Download by tags')
    print(' 4.  Download from list')
    print(' 5.  Download from followed artists (/bookmark.php?type=user)')
    print(' 6.  Download from bookmarked images (/bookmark.php)')
    print(' 7.  Download from tags list')
    print(' 8.  Download new illust from bookmarked members (/bookmark_new_illust.php)')
    print(' 9.  Download by Title/Caption')
    print(' 10. Download by Tag and Member Id')
    print(' 11. Download Member Bookmark (/bookmark.php?id=)')
    print(' 12. Download by Group Id')
    print(' 13. Download by Manga Series Id')
    print(' 14. Download by Novel Id')
    print(' 15. Download by Novel Series Id')
    print(' 16. Download by Rank')
    print(' 17. Download by Rank R-18')
    print(' 18. Download by New Illusts')
    print(' 19. Download by Unlisted image_id')
    print(' m1. Metadata by member_id')
    print(' m2. Metadata by image_id')
    print(' m3. Metadata by manga series id')
    print(' m4. Metadata by tag')
    print(Style.BRIGHT + '── FANBOX '.ljust(PADDING, "─") + Style.RESET_ALL)
    print(' f1. Download from supporting list (FANBOX)')
    print(' f2. Download by artist/creator id (FANBOX)')
    print(' f3. Download by post id (FANBOX)')
    print(' f4. Download from following list (FANBOX)')
    print(' f5. Download from custom list (FANBOX)')
    print(' f6. Download Pixiv by FANBOX Artist ID')
    print(Style.BRIGHT + '── Sketch '.ljust(PADDING, "─") + Style.RESET_ALL)
    print(' s1. Download by creator id (Sketch)')
    print(' s2. Download by post id (Sketch)')
    print(Style.BRIGHT + '── Batch Download '.ljust(PADDING, "─") + Style.RESET_ALL)
    print(' b. Batch Download from batch_job.json (experimental)')
    print(Style.BRIGHT + '── Others '.ljust(PADDING, "─") + Style.RESET_ALL)
    print(' d. Manage database')
    print(' l. Export local database.')
    print(' e. Export online followed artist.')
    print(' m. Export online other\'s followed artist.')
    print(' p. Export online image bookmarks.')
    print(' z. Export userId bookmarks.')
    print(' i. Import list file')
    print(' u. Ugoira re-encode')
    print(' r. Reload config.ini')
    print(' c. Print config.ini')
    print(' x. Exit')

    read_lists()

    sel = input('Input: ').rstrip("\r")
    return sel


def set_console_title(title=''):
    set_title = f'PixivDownloader {PixivConstant.PIXIVUTIL_VERSION} {title}'
    PixivHelper.set_console_title(set_title)


def read_lists():
    # Implement #797
    if state.config.useBlacklistTags:
        state.set_blacklist_tags(PixivTags.parseTagsList("blacklist_tags.txt"))
        PixivHelper.print_and_log('info', 'Using Blacklist Tags: ' + str(len(state.blacklist_tags)) + " items.")

    if state.config.useBlacklistMembers:
        state.set_blacklist_members(PixivTags.parseTagsList("blacklist_members.txt"))
        PixivHelper.print_and_log('info', 'Using Blacklist Members: ' + str(len(state.blacklist_members)) + " members.")

    if state.config.useBlacklistTitles:
        state.set_blacklist_titles(PixivTags.parseTagsList("blacklist_titles.txt"))
        PixivHelper.print_and_log('info', 'Using Blacklist Titles: ' + str(len(state.blacklist_titles)) + " items.")

    if state.config.useSuppressTags:
        state.set_suppress_tags(PixivTags.parseTagsList("suppress_tags.txt"))
        PixivHelper.print_and_log('info', 'Using Suppress Tags: ' + str(len(state.suppress_tags)) + " items.")


def menu_reload_config():
    state.log.info('Manual Reload Config (r).')
    state.config.loadConfig(path=state.configfile)


def menu_print_config():
    state.log.info('Print Current Config (p).')
    state.config.printConfig()


def menu_import_list():
    state.log.info('Import List mode (i).')
    list_name = input("List filename = ").rstrip("\r")
    if len(list_name) == 0:
        list_name = "list.txt"
    PixivListHandler.import_list(state.get_caller(), state.config, list_name)
# Register helpers with cli.state (avoid circular imports at call time).
state.register_helpers(
    menu=menu,
    read_lists=read_lists,
    set_console_title=set_console_title,
    get_start_and_end_page_from_options=get_start_and_end_page_from_options,
    get_list_file_from_options=get_list_file_from_options,
)
