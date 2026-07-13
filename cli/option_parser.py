# -*- coding: utf-8 -*-
"""CLI option parser."""
from __future__ import annotations

from optparse import OptionParser
from cli import state


def setup_option_parser():
    valid_options = (
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
        'm1', 'm2', 'm3', 'm4',
        'f1', 'f2', 'f3', 'f4', 'f5', 'f6',
        's1', 's2',
        'l', 'd', 'e', 'm', 'b', 'p', 'c', 'z', 'i', 'u', 'r',
    )
    # Must write through to PixivUtil2.__valid_options (state.attr= does NOT).
    state.set_valid_options(valid_options)
    parser = OptionParser()

    # need to keep the whitespace to adjust the output for --help
    parser.add_option('-s', '--start_action', dest='start_action',
                      help='''Action you want to load your program with:          \n
1  - Download by member_id                          \n
2  - Download by image_id                           \n
3  - Download by tags                               \n
4  - Download from list                             \n
5  - Download from user bookmark                    \n
6  - Download from user's image bookmark            \n
7  - Download from tags list                        \n
8  - Download new illust from bookmark              \n
9  - Download by Title/Caption                      \n
10 - Download by Tag and Member Id                  \n
11 - Download images from Member Bookmark           \n
12 - Download images by Group Id                    \n
m1 - Metadata by member_id                          \n
m2 - Metadata by image_id                           \n
m3 - Metadata by manga series id                    \n
m4 - Metadata by tag                                \n
f1 - Download from supporting list (FANBOX)         \n
f2 - Download by artist/creator id (FANBOX)         \n
f3 - Download by post id (FANBOX)                   \n
f4 - Download from following list (FANBOX)          \n
f5 - Download from custom list (FANBOX)             \n
s1 - Download by creator id (Sketch)')              \n
s2 - Download by post id (Sketch)')                 \n
b  - Batch Download from batch_job.json             \n
l  - Export local database (image_id)               \n
e  - Export online bookmark                         \n
m  - Export online user bookmark                    \n
p  - Export online image bookmark                   \n
d  - Manage database''')
    parser.add_option('-x', '--exit_when_done',
                      dest='exit_when_done',
                      default=False,
                      help='Exit program when done. (only useful when not using DB-Manager)',
                      action='store_true')
    parser.add_option('-i', '--irfanview',
                      dest='start_iv',
                      default=False,
                      help='Start IrfanView after downloading images using downloaded_on_%date%.txt',
                      action='store_true')
    parser.add_option('-n', '--number_of_pages',
                      dest='number_of_pages',
                      help='Temporarily overwrites numberOfPage set in config.ini')
    parser.add_option('-c', '--config', dest='configlocation',
                      default=None,
                      help='Load the config file from a custom location')
    parser.add_option('-z', '--userId_bookmark', dest='userId_bookmark',
                      default=None,
                      help='Load the userId from your bookmark')
    parser.add_option('--bf', '--batch_file',
                      dest='batch_file',
                      default=None,
                      help='Json file for batch job (b).')
    parser.add_option('--sp', '--start_page',
                      dest='start_page',
                      default=None,
                      help='''Starting page in integer.                             \n
Used in option 1, 3, 5, 6, 7, 8, 9, and 10.''')
    parser.add_option('--ep', '--end_page',
                      dest='end_page',
                      default=None,
                      help='''End page in integer.                                  \n
If start page is given and it is larger than end page, it will be assumed as
number of page instead (start page + end page).
This take priority from '-n', '--number_of_pages' for calculation.
Used in option 1, 3, 5, 6, 7, 8, 9, and 10.
See state.get_start_and_end_page_from_options()''')
    parser.add_option('--b', '--bookmark_pages',
                      dest='bookmark_pages',
                      default=None,
                      help='Number of bookmark pages to export (used with -s z). Overrides config.ini')
    parser.add_option('--is', '--include_sketch',
                      dest='include_sketch',
                      default=False,
                      action='store_true',
                      help='''Include Pixiv Sketch when processing member id (1). Default is False.''')
    parser.add_option('--wt', '--use_wildcard_tag',
                      dest='use_wildcard_tag',
                      default=False,
                      help='Use wildcard when downloading by tag (3) or tag list (7). Default is False.',
                      action='store_true')
    parser.add_option('-f', '--list_file',
                      dest='list_file',
                      default=None,
                      help='''List file for download by list (4) or tag list (7).   \n
If using relative path, it will be prefixed with [downloadlistdirectory] in config.ini.''')
    parser.add_option('-p', '--bookmark_flag',
                      dest='bookmark_flag',
                      default=None,
                      help='''Include private bookmark flag for option 5 and 6.     \n
 y - include private bookmark.                      \n
 n - don't include private bookmark.                \n
 o - only get from private bookmark.''')
    parser.add_option('-o', '--sort_order',
                      dest='sort_order',
                      default=None,
                      help='''Sorting order for option 6.                           \n
 asc - sort by bookmark.                            \n
 desc - sort by bookmark in descending order.       \n
 date - sort by date.                               \n
 date_d - sort by date in descending order.''')

    parser.add_option('--tag_sort_order',
                      dest='tag_sort_order',
                      default='date_d',
                      help='''Sorting order for option 3 and 7.                     \n
 date - sort by date.                               \n
 date_d - sort by date in descending order.         \n
 PREMIUM ONLY:                                      \n
 popular_d - overall popularity                     \n
 popular_male_d - popular among male users          \n
 popular_female_d - popular among female users''')

    parser.add_option('--start_date',
                      dest='start_date',
                      default=None,
                      help='''Start Date for option 3, 7 and 9.                     \n
 Format must follow YYYY-MM-DD.''')
    parser.add_option('--end_date',
                      dest='end_date',
                      default=None,
                      help='''End Date for option 3, 7 and 9.                       \n
 Format must follow YYYY-MM-DD.''')
    parser.add_option('--uit', '--use_image_tag',
                      dest='use_image_tag',
                      default=False,
                      action='store_true',
                      help='''Use Image Tag for filtering in option (6). Default is False.''')
    parser.add_option('--bcl', '--bookmark_count_limit',
                      dest='bookmark_count_limit',
                      default=-1,
                      help='''Bookmark count limit in integer.                       \n
Used in option 3, 5, 7, and 8.''')
    parser.add_option('--rm', '--rank_mode',
                      dest='rank_mode',
                      default="daily",
                      help='''Ranking Mode.''')
    parser.add_option('--rc', '--rank_content',
                      dest='rank_content',
                      default="all",
                      help='''Ranking Content Type.''')
    parser.add_option('--ef', '--export_filename',
                      dest='export_filename',
                      default="export.txt",
                      help='''Filename for exporting members/images.                    \n
Used in option e, m, p''')
    parser.add_option('--up', '--use_pixiv',
                      dest='use_pixiv',
                      default=None,
                      help='''Use Pixiv table for export.                               \n
 y - include pixiv database.                        \n
 n - don't include pixiv database.                     \n
 o - only export pixiv database.''')
    parser.add_option('--uf', '--use_fanbox',
                      dest='use_fanbox',
                      default=None,
                      help='''Use Fanbox table for export.                              \n
 y - include fanbox database.                       \n
 n - don't include fanbox database.                 \n
 o - only export fanbox database.''')
    parser.add_option('--us', '--use_sketch',
                      dest='use_sketch',
                      default=None,
                      help='''Use Sketch table for export.                              \n
 y - include sketch database.                       \n
 n - don't include sketch database.                 \n
 o - only export sketch database.''')
    parser.add_option('--tmf', '--tag_metadata_filter',
                      dest='tag_metadata_filter',
                      default='none',
                      help='''Filter for tag metadata (m4). Valid: none, pixpedia, translation, pixpedia_or_translation.''')
    parser.add_option('--no-resume',
                      dest='no_resume',
                      default=False,
                      action='store_true',
                      help='Ignore existing FANBOX checkpoint and start the list from scratch.')
    return parser


