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


def menu_download_by_member_id(opisvalid, args, options):
    state.log.info('Member id mode (1).')
    current_member = 1
    page = 1
    end_page = 0
    include_sketch = False
    member_ids = list()

    if opisvalid and len(args) > 0:
        include_sketch = options.include_sketch
        if include_sketch:
            print("Including Pixiv Sketch.")

        (page, end_page) = state.get_start_and_end_page_from_options(options)

        for member_id in args:
            if member_id.isdigit():
                member_ids.append(int(member_id))
            else:
                print(f"Possible invalid member id = {member_id}")

    else:
        member_ids = input('Member ids: ').rstrip("\r")
        (page, end_page) = PixivHelper.get_start_and_end_number(total_number_of_page=options.number_of_pages)
        skipSketchPrompt = state.config.defaultSketchOption

        if skipSketchPrompt.lower() == 'y':
            print("Including Pixiv Sketch.")
            include_sketch = True
        elif skipSketchPrompt.lower() == 'n':
            print("Excluding Pixiv Sketch.")
        else:
            include_sketch_ask = input('Include Pixiv Sketch [y/n, default is no]? ').rstrip("\r") or 'n'
            if include_sketch_ask.lower() == 'y':
                include_sketch = True

        member_ids = PixivHelper.get_ids_from_csv(member_ids)
        PixivHelper.print_and_log('info', f"Member IDs: {member_ids}")

    for member_id in member_ids:
        try:
            prefix = f"[{current_member} of {len(member_ids)}] "
            PixivArtistHandler.process_member(state.get_caller(),
                                                state.config,
                                                member_id,
                                                page=page,
                                                end_page=end_page,
                                                title_prefix=prefix)
            # Issue #793
            if include_sketch:
                # fetching artist token...
                (artist_model, _) = state.br.getMemberPage(member_id)
                prefix = f"[{current_member} ({artist_model.artistToken}) of {len(member_ids)}] "
                PixivSketchHandler.process_sketch_artists(state.get_caller(),
                                                            state.config,
                                                            artist_model.artistToken,
                                                            page,
                                                            end_page,
                                                            title_prefix=prefix)

            current_member = current_member + 1
        except PixivException as ex:
            PixivHelper.print_and_log('error', f"Member ID: {member_id} is not valid")
            state.set_error_code(-1)
            continue


def menu_metadata_by_member_id(opisvalid, args, options):
    state.log.info('Member metadata mode (m1).')
    current_member = 1
    member_ids = list()

    if opisvalid and len(args) > 0:
        for member_id in args:
            if member_id.isdigit():
                member_ids.append(int(member_id))
            else:
                print(f"Possible invalid member id = {member_id}")
    else:
        member_ids = input('Member ids: ').rstrip("\r")
        member_ids = PixivHelper.get_ids_from_csv(member_ids)
        PixivHelper.print_and_log('info', f"Member IDs: {member_ids}")

    for member_id in member_ids:
        try:
            prefix = f"[{current_member} of {len(member_ids)}] "
            PixivArtistHandler.process_member_metadata(state.get_caller(),
                                                      state.config,
                                                      member_id,
                                                      title_prefix=prefix)
            current_member = current_member + 1
        except PixivException:
            PixivHelper.print_and_log('error', f"Member ID: {member_id} is not valid")
            state.set_error_code(-1)
            continue


def menu_download_by_member_bookmark(opisvalid, args, options):
    state.log.info('Member Bookmark mode (11).')
    page = 1
    end_page = 0
    i = 0
    current_member = 1
    if opisvalid and len(args) > 0:
        valid_ids = list()
        for member_id in args:
            print("%d/%d\t%f %%" % (i, len(args), 100.0 * i / float(len(args))))
            i += 1
            try:
                test_id = int(member_id)
                valid_ids.append(test_id)
            except Exception:
                PixivHelper.print_and_log('error', f"Member ID: {member_id} is not valid")
                state.set_error_code(-1)
                continue
        if state.br._myId in valid_ids:
            PixivHelper.print_and_log('error', f"Member ID: {state.br._myId} is your own id, use option 6 instead.")
        for mid in valid_ids:
            prefix = f"[{current_member} of {len(valid_ids)}] "
            PixivArtistHandler.process_member(state.get_caller(),
                                              state.config,
                                              mid,
                                              page=page,
                                              end_page=end_page,
                                              bookmark=True,
                                              tags=None,
                                              title_prefix=prefix)
            current_member = current_member + 1

    else:
        member_id = input('Member id: ').rstrip("\r")
        tags = input('Filter Tags: ').rstrip("\r")
        (page, end_page) = PixivHelper.get_start_and_end_number(total_number_of_page=options.number_of_pages)
        if state.br._myId == int(member_id):
            PixivHelper.print_and_log('error', f"Member ID: {member_id} is your own id, use option 6 instead.")
        else:
            PixivArtistHandler.process_member(state.get_caller(),
                                              state.config,
                                              member_id.strip(),
                                              page=page,
                                              end_page=end_page,
                                              bookmark=True,
                                              tags=tags)


def menu_download_by_image_id(opisvalid, args, options):
    state.log.info('Image id mode (2).')
    if opisvalid and len(args) > 0:
        for image_id in args:
            try:
                test_id = int(image_id)
                PixivImageHandler.process_image(state.get_caller(),
                                                state.config,
                                                artist=None,
                                                image_id=test_id,
                                                useblacklist=False)
            except Exception:
                PixivHelper.print_and_log('error', f"Image ID: {image_id} is not valid")
                state.set_error_code(-1)
                continue
    else:
        image_ids = input('Image ids: ').rstrip("\r")
        image_ids = PixivHelper.get_ids_from_csv(image_ids)
        for image_id in image_ids:
            PixivImageHandler.process_image(state.get_caller(),
                                            state.config,
                                            artist=None,
                                            image_id=int(image_id),
                                            useblacklist=False)


def menu_metadata_by_image_id(opisvalid, args, options):
    state.log.info('Image metadata mode (m2).')
    if opisvalid and len(args) > 0:
        for image_id in args:
            try:
                test_id = int(image_id)
                PixivImageHandler.process_image(state.get_caller(),
                                                state.config,
                                                artist=None,
                                                image_id=test_id,
                                                useblacklist=False,
                                                metadata_only=True)
            except Exception:
                PixivHelper.print_and_log('error', f"Image ID: {image_id} is not valid")
                state.set_error_code(-1)
                continue
    else:
        image_ids = input('Image ids: ').rstrip("\r")
        image_ids = PixivHelper.get_ids_from_csv(image_ids)
        for image_id in image_ids:
            PixivImageHandler.process_image(state.get_caller(),
                                            state.config,
                                            artist=None,
                                            image_id=int(image_id),
                                            useblacklist=False,
                                            metadata_only=True)


def menu_metadata_by_manga_series_id(opisvalid, args, options):
    state.log.info('Manga Series metadata mode (m3).')
    manga_series_ids = []

    if opisvalid and len(args) > 0:
        for manga_series_id in args:
            if manga_series_id.isdigit():
                manga_series_ids.append(int(manga_series_id))
            else:
                print(f"Possible invalid manga series id = {manga_series_id}")
    else:
        manga_series_ids = input('Manga Series IDs: ').rstrip("\r")
        manga_series_ids = PixivHelper.get_ids_from_csv(manga_series_ids)
        PixivHelper.print_and_log('info', f"Manga Series IDs: {manga_series_ids}")

    for manga_series_id in manga_series_ids:
        PixivImageHandler.process_manga_series_metadata(state.get_caller(),
                                                        state.config,
                                                        manga_series_id)


def menu_metadata_by_tag(opisvalid, args, options):
    state.log.info('Tag metadata mode (m4).')
    if opisvalid and len(args) > 0:
        tags = args
    else:
        tags = input('Tags (comma-separated): ').rstrip("\r")
    filter_mode = options.tag_metadata_filter
    if not opisvalid:
        filter_prompt = "Tag metadata filter [none/pixpedia/translation/pixpedia_or_translation, default is none]: "
        filter_mode = input(filter_prompt).rstrip("\r") or "none"
    PixivTagsHandler.process_tag_metadata(state.get_caller(), state.config, tags, filter_mode=filter_mode)


def menu_download_by_tags(opisvalid, args, options):
    state.log.info('Tags mode (3).')
    page = 1
    end_page = 0
    start_date = None
    end_date = None
    bookmark_count = None
    # oldest_first = False
    sort_order = 'date_d'
    wildcard = False
    type_mode = "a"

    if opisvalid and len(args) > 0:
        wildcard = options.use_wildcard_tag
        sort_order = options.tag_sort_order
        start_date = options.start_date
        end_date = options.end_date
        bookmark_count = options.bookmark_count_limit
        (page, end_page) = state.get_start_and_end_page_from_options(options)
        tags = " ".join(args)
    else:
        tags = input('Tags: ').rstrip("\r")
        bookmark_count = input('Bookmark Count: ').rstrip("\r") or None
        wildcard = input('Use Partial Match (s_tag) [y/n, default is no]: ').rstrip("\r") or 'n'
        if wildcard.lower() == 'y':
            wildcard = True
        else:
            wildcard = False

        # Issue #834
        if state.br._isPremium:
            msg = 'Sorting Order [date_d|date|popular_d|popular_male_d|popular_female_d]? '
            sort_order = input(msg).rstrip("\r") or 'date_d'
        else:
            oldest_first = input('Oldest first[y/n, default is no]: ').rstrip("\r") or 'n'
            if oldest_first.lower() == 'y':
                sort_order = 'date'

        (page, end_page) = PixivHelper.get_start_and_end_number(total_number_of_page=options.number_of_pages)
        (start_date, end_date) = PixivHelper.get_start_and_end_date()

        while True:
            type_mode = input("Search type [a-all|i-Illustration and Ugoira|m-manga, default is all: ").rstrip("\r") or "a"
            if type_mode in {'a', 'i', 'm'}:
                break
            else:
                print("Valid values are 'a', 'i', or 'm'.")

    if bookmark_count is not None and bookmark_count != -1 and len(bookmark_count) > 0:
        bookmark_count = int(bookmark_count)

    PixivTagsHandler.process_tags(state.get_caller(),
                                  state.config,
                                  tags.strip(),
                                  page=page,
                                  end_page=end_page,
                                  wild_card=wildcard,
                                  start_date=start_date,
                                  end_date=end_date,
                                  use_tags_as_dir=state.config.useTagsAsDir,
                                  bookmark_count=bookmark_count,
                                  sort_order=sort_order,
                                  type_mode=type_mode)


def menu_download_by_title_caption(opisvalid, args, options):
    state.log.info('Title/Caption mode (9).')
    page = 1
    end_page = 0
    start_date = None
    end_date = None
    if opisvalid and len(args) > 0:
        start_date = options.start_date
        end_date = options.end_date
        (page, end_page) = state.get_start_and_end_page_from_options(options)
        tags = " ".join(args)
    else:
        tags = input('Title/Caption: ').rstrip("\r")
        (page, end_page) = PixivHelper.get_start_and_end_number(total_number_of_page=options.number_of_pages)
        (start_date, end_date) = PixivHelper.get_start_and_end_date()

    PixivTagsHandler.process_tags(state.get_caller(),
                                  state.config,
                                  tags.strip(),
                                  page=page,
                                  end_page=end_page,
                                  wild_card=False,
                                  title_caption=True,
                                  start_date=start_date,
                                  end_date=end_date,
                                  use_tags_as_dir=state.config.useTagsAsDir)


def menu_download_by_tag_and_member_id(opisvalid, args, options):
    state.log.info('Tag and MemberId mode (10).')
    member_id = 0
    tags = None
    page = 1
    end_page = 0

    if opisvalid and len(args) >= 2:
        (page, end_page) = state.get_start_and_end_page_from_options(options)
        try:
            member_id = int(args[0])
        except Exception:
            PixivHelper.print_and_log('error', f"Member ID: {member_id} is not valid")
            state.set_error_code(-1)
            return

        tags = " ".join(args[1:])
        PixivHelper.safePrint(f"Looking tags: {tags} from memberId: {member_id}")
    else:
        member_id = input('Member Id: ').rstrip("\r")
        tags = input('Tag      : ').rstrip("\r")
        (page, end_page) = PixivHelper.get_start_and_end_number(total_number_of_page=options.number_of_pages)

    PixivTagsHandler.process_tags(state.get_caller(),
                                  state.config,
                                  tags.strip(),
                                  page=page,
                                  end_page=end_page,
                                  use_tags_as_dir=state.config.useTagsAsDir,
                                  member_id=int(member_id))


def menu_download_from_list(opisvalid, args, options):
    state.log.info('Batch mode from list (4).')
    include_sketch = False

    list_file_name = state.config.downloadListDirectory + os.sep + 'list.txt'
    tags = None
    if opisvalid:
        include_sketch = options.include_sketch
        list_file_name = state.get_list_file_from_options(options, list_file_name)
        # get one tag from input parameter
        if len(args) > 0:
            tags = args[0]
    else:
        test_tags = input('Tag : ').rstrip("\r")
        include_sketch_ask = input('Include Pixiv Sketch [y/n, default is no]? ').rstrip("\r") or 'n'
        if include_sketch_ask.lower() == 'y':
            include_sketch = True
        if len(test_tags) > 0:
            tags = test_tags

    PixivListHandler.process_list(state.get_caller(),
                                  state.config,
                                  list_file_name=list_file_name,
                                  tags=tags,
                                  include_sketch=include_sketch)


def menu_download_from_online_user_bookmark(opisvalid, args, options):
    state.log.info('User Bookmarked Artist mode (5).')
    start_page = 1
    end_page = 0
    hide = 'n'
    bookmark_count = None

    if opisvalid:
        if options.bookmark_flag is not None:
            hide = options.bookmark_flag.lower()
            if hide not in ('y', 'n', 'o'):
                PixivHelper.print_and_log("error", f"Invalid args for bookmark_flag: {args}, valid values are [y/n/o].")
                return
            (start_page, end_page) = state.get_start_and_end_page_from_options(options)
            bookmark_count = options.bookmark_count_limit
    else:
        arg = input("Include Private bookmarks [y/n/o, default is no]: ").rstrip("\r") or 'n'
        arg = arg.lower()
        if arg == 'y' or arg == 'n' or arg == 'o':
            hide = arg
        else:
            print("Invalid args: ", arg)
            return
        (start_page, end_page) = PixivHelper.get_start_and_end_number(total_number_of_page=options.number_of_pages)
        bookmark_count = input('Bookmark Count: ').rstrip("\r") or None

    if bookmark_count is not None and bookmark_count != -1 and len(bookmark_count) > 0:
        bookmark_count = int(bookmark_count)

    PixivBookmarkHandler.process_bookmark(state.get_caller(),
                                          state.config,
                                          hide,
                                          start_page,
                                          end_page,
                                          bookmark_count=bookmark_count)


def menu_download_from_online_image_bookmark(opisvalid, args, options):
    state.log.info("User's Image Bookmark mode (6).")
    start_page = 1
    end_page = 0
    hide = 'n'
    tag = ''
    use_image_tag = False

    if opisvalid:
        if len(args) > 0:
            tag = args[0]

        (start_page, end_page) = state.get_start_and_end_page_from_options(options)
        if options.bookmark_flag is not None:
            hide = options.bookmark_flag.lower()
            if hide not in ('y', 'n', 'o'):
                PixivHelper.print_and_log("error", f"Invalid args for bookmark_flag: {args}, valid values are [y/n/o].")
                return
        use_image_tag = options.use_image_tag
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

    PixivBookmarkHandler.process_image_bookmark(state.get_caller(),
                                                state.config,
                                                hide=hide,
                                                start_page=start_page,
                                                end_page=end_page,
                                                tag=tag,
                                                use_image_tag=use_image_tag)


def menu_download_from_tags_list(opisvalid, args, options):
    state.log.info('Taglist mode (7).')
    page = 1
    end_page = 0
    sort_order = 'date_d'
    wildcard = False
    bookmark_count = None
    start_date = None
    end_date = None

    if opisvalid:
        filename = state.get_list_file_from_options(options=options, default_list_file='./tags.txt')
        sort_order = options.tag_sort_order
        wildcard = options.use_wildcard_tag
        start_date = options.start_date
        end_date = options.end_date
        (page, end_page) = state.get_start_and_end_page_from_options(options)
        bookmark_count = options.bookmark_count_limit
    else:
        filename = input("Tags list filename [tags.txt]: ").rstrip("\r") or './tags.txt'
        wildcard = input('Use Wildcard[y/n, default is no]: ').rstrip("\r") or 'n'
        if wildcard.lower() == 'y':
            wildcard = True
        else:
            wildcard = False

        # Issue #834
        if state.br._isPremium:
            msg = 'Sorting Order [date_d|date|popular_d|popular_male_d|popular_female_d, default is date_d]? '
            sort_order = input(msg).rstrip("\r") or 'date_d'
        else:
            oldest_first = input('Oldest first [y/n, default is no]: ').rstrip("\r") or 'n'
            if oldest_first.lower() == 'y':
                sort_order = 'date'

        bookmark_count = input('Bookmark Count: ').rstrip("\r") or None
        (page, end_page) = PixivHelper.get_start_and_end_number(total_number_of_page=options.number_of_pages)
        (start_date, end_date) = PixivHelper.get_start_and_end_date()

    if bookmark_count is not None and bookmark_count != -1 and len(bookmark_count) > 0:
        bookmark_count = int(bookmark_count)

    PixivListHandler.process_tags_list(state.get_caller(),
                                       state.config,
                                       filename,
                                       page,
                                       end_page,
                                       wild_card=wildcard,
                                       sort_order=sort_order,
                                       bookmark_count=bookmark_count,
                                       start_date=start_date,
                                       end_date=end_date)


def menu_download_new_illust_from_bookmark(opisvalid, args, options):
    state.log.info('New Illust from Bookmark mode (8).')
    bookmark_count = None

    if opisvalid:
        (page_num, end_page_num) = state.get_start_and_end_page_from_options(options)
        bookmark_count = options.bookmark_count_limit
    else:
        (page_num, end_page_num) = PixivHelper.get_start_and_end_number(total_number_of_page=options.number_of_pages)
        bookmark_count = input('Bookmark Count: ').rstrip("\r") or None

    if bookmark_count is not None and bookmark_count != -1 and len(bookmark_count) > 0:
        bookmark_count = int(bookmark_count)

    PixivBookmarkHandler.process_new_illust_from_bookmark(state.get_caller(),
                                                          state.config,
                                                          page_num=page_num,
                                                          end_page_num=end_page_num,
                                                          bookmark_count=bookmark_count)


def menu_download_by_manga_series_id(opisvalid, args, options):
    state.log.info('Manga Series mode (13).')
    manga_series_ids = []
    start_page = 1
    end_page = 0

    if opisvalid:
        (start_page, end_page) = state.get_start_and_end_page_from_options(options)
        for manga_series_id in args:
            if manga_series_id.isdigit():
                manga_series_ids.append(int(manga_series_id))
            else:
                print(f"Possible invalid manga series id = {manga_series_id}")
    else:
        manga_series_ids = input('Manga Series IDs: ').rstrip("\r")
        (start_page, end_page) = PixivHelper.get_start_and_end_number(total_number_of_page=options.number_of_pages)
        manga_series_ids = PixivHelper.get_ids_from_csv(manga_series_ids)
        PixivHelper.print_and_log('info', f"Manga Series IDs: {manga_series_ids}")

    for manga_series_id in manga_series_ids:
        PixivImageHandler.process_manga_series(state.get_caller(),
                                               state.config,
                                               manga_series_id=manga_series_id,
                                               start_page=start_page,
                                               end_page=end_page)


def menu_download_by_novel_id(opisvalid, args, options):
    state.log.info('Novel mode (14).')
    novel_ids = input('Novel IDs: ').rstrip("\r")
    novel_ids = PixivHelper.get_ids_from_csv(novel_ids)
    PixivHelper.print_and_log('info', f"Novel IDs: {novel_ids}")

    for novel_id in novel_ids:
        PixivNovelHandler.process_novel(state.get_caller(),
                                        state.config,
                                        novel_id)


def menu_download_by_novel_series_id(opisvalid, args, options):
    state.log.info('Novel Series mode (15).')
    start_page = 1
    end_page = 0

    novel_series_ids = input('Novel Series IDs: ').rstrip("\r")
    (start_page, end_page) = PixivHelper.get_start_and_end_number(total_number_of_page=options.number_of_pages)
    novel_series_ids = PixivHelper.get_ids_from_csv(novel_series_ids)
    PixivHelper.print_and_log('info', f"Novel Series IDs: {novel_series_ids}")

    for novel_series_id in novel_series_ids:
        PixivNovelHandler.process_novel_series(state.get_caller(),
                                               state.config,
                                               novel_series_id,
                                               start_page=start_page,
                                               end_page=end_page)


def menu_download_by_group_id(opisvalid, args, options):
    state.log.info('Group mode (12).')
    process_external = False
    limit = 0

    if opisvalid and len(args) > 0:
        group_id = args[0]
        limit = int(args[1])
        if args[2].lower() == 'y':
            process_external = True
    else:
        group_id = input("Group Id: ").rstrip("\r")
        limit = int(input("Limit: ").rstrip("\r"))
        arg = input("Process External Image [y/n, default is no]: ").rstrip("\r") or 'n'
        arg = arg.lower()
        if arg == 'y':
            process_external = True

    PixivBookmarkHandler.process_from_group(state.get_caller(),
                                            state.config,
                                            group_id,
                                            limit=limit,
                                            process_external=process_external)


def menu_download_by_unlisted_image_id(opisvalid, args, options):
    state.log.info('Unlisted ID mode (19).')
    if opisvalid and len(args) > 0:
        for image_id in args:
            try:
                PixivImageHandler.process_image(state.get_caller(),
                                                state.config,
                                                artist=None,
                                                image_id=image_id,
                                                useblacklist=False,
                                                is_unlisted=True)
            except Exception:
                PixivHelper.print_and_log('error', f"Image ID: {image_id} is not valid")
                state.set_error_code(-1)
                continue
    else:
        image_ids = input('Image ids: ').rstrip("\r")
        image_ids = PixivHelper.get_ids_from_csv(image_ids, is_string=True)
        for image_id in image_ids:
            PixivImageHandler.process_image(state.get_caller(),
                                            state.config,
                                            artist=None,
                                            image_id=image_id,
                                            useblacklist=False,
                                            is_unlisted=True)


def menu_ugoira_reencode(opisvalid, args, options):
    state.log.info('Re-encode Ugoira (u)')
    msg = Fore.YELLOW + Style.NORMAL + 'WARNING: THIS ACTION CANNOT BE UNDO !' + Style.RESET_ALL
    PixivHelper.print_and_log(None, msg)
    msg = Fore.YELLOW + Style.NORMAL + 'You are about to re-encode and overwrite all of your stored ugoira and its related files (gif, webm ...).' + Style.RESET_ALL
    PixivHelper.print_and_log(None, msg)
    arg = input(Fore.YELLOW + Style.BRIGHT + 'Do you really want to proceed ? [y/n, default is no]: ' + Style.RESET_ALL).rstrip("\r") or 'n'
    sure = arg.lower()
    if sure not in ('y', 'n'):
        PixivHelper.print_and_log("error", f"Invalid args for ugoira reencode: {arg}, valid values are [y/n].")
        return
    if state.config.overwrite:
        arg = input(Fore.YELLOW + Style.BRIGHT + 'Overwrite option is set to True, all animated files will be re-download from Pixiv and not re-encode locally. Do you still want to proceed ? [y/n, default is no]: ' + Style.RESET_ALL).rstrip("\r") or 'n'
        sure = arg.lower()
        if sure not in ('y', 'n'):
            PixivHelper.print_and_log("error", f"Invalid args for ugoira reencode: {arg}, valid values are [y/n].")
            return
    if sure == 'y':
        PixivImageHandler.process_ugoira_local(state.get_caller(), state.config)


def menu_download_by_rank(op_is_valid, args, options, valid_modes=None):
    if valid_modes is None:
        state.log.info('Download Ranking by Post ID mode (15).')
        valid_modes = ["daily", "weekly", "monthly", "rookie", "original", "male", "female"]
    valid_contents = ["all", "illust", "ugoira", "manga"]
    mode = ""
    date = ""
    content = "all"
    start_page = 1
    end_page = 0

    if op_is_valid and len(args) > 0:
        (start_page, end_page) = state.get_start_and_end_page_from_options(options)
        mode = options.rank_mode
        if mode not in valid_modes:
            print(f"Invalid mode: {mode}, valid modes are {', '.join(valid_modes)}.")
        content = options.rank_content
        if content not in valid_contents:
            print(f"Invalid type: {content}, valid content types are {', '.join(valid_contents)}.")
    else:
        while True:
            print(f"Valid Modes are: {', '.join(valid_modes)}")
            mode = input('Mode: ').rstrip("\r").lower()
            if mode in valid_modes:
                break
            else:
                print("Invalid mode.")
        while True:
            print(f"Valid Content Types are: {', '.join(valid_contents)}")
            content = input('Type: ').rstrip("\r").lower()
            if content in valid_contents:
                break
            else:
                print("Invalid Content Type.")
        while True:
            print(f"Specify the ranking date, valid type is YYYYMMDD (default: today)")
            date = input('Date: ').rstrip("\r").lower()
            try:
                if date != '':
                    datetime.datetime.strptime(date, "%Y%m%d")
            except Exception as ex:
                PixivHelper.print_and_log("error", f"Invalid format for ranking date: {date}.")
            else:
                break
        (start_page, end_page) = PixivHelper.get_start_and_end_number()

    PixivRankingHandler.process_ranking(state.get_caller(),
                                        state.config,
                                        mode,
                                        content,
                                        start_page,
                                        end_page,
                                        date=date,
                                        filter=None)


def menu_download_by_rank_r18(op_is_valid, args, options):
    state.log.info('Download R-18 Ranking by Post ID mode (16).')
    valid_modes = ["daily_r18", "weekly_r18", "male_r18", "female_r18"]
    menu_download_by_rank(op_is_valid, args, options, valid_modes)


def menu_download_new_illusts(op_is_valid, args, options):
    state.log.info('Download New Illust mode (17).')
    valid_modes = ["illust", "manga"]
    type_mode = "illusts"
    max_page = 0

    if op_is_valid and len(args) > 0:
        mode = options.rank_mode
        if mode not in valid_modes:
            print(f"Invalid mode: {mode}, valid modes are {', '.join(valid_modes)}.")
        max_page = options.end_page
    else:
        while True:
            print(f"Valid Modes are: {', '.join(valid_modes)}")
            type_mode = input('Mode: ').rstrip("\r").lower()
            if type_mode in valid_modes:
                break
            else:
                print("Invalid mode.")
        max_page = int(input('Max Page: ').rstrip("\r").lower()) or 0

    PixivRankingHandler.process_new_illusts(state.get_caller(),
                                            state.config,
                                            type_mode,
                                            max_page)


