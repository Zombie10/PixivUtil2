# -*- coding: utf-8 -*-
import os
import gc

import common.datetime_z as datetime_z
import common.PixivBrowserFactory as PixivBrowserFactory
import common.PixivConstant as PixivConstant
import common.PixivRunStats as PixivRunStats
import handler.PixivDownloadHandler as PixivDownloadHandler
import common.PixivHelper as PixivHelper
import model.PixivModelFanbox as PixivModelFanbox
from common.PixivException import PixivException
import handler.PixivArtistHandler as PixivArtistHandler


def process_fanbox_artist_by_id(caller, config, artist_id, end_page, title_prefix=""):
    config.loadConfig(path=caller.configfile)
    br: PixivBrowserFactory.PixivBrowser = PixivBrowserFactory.getBrowser()
    stats = PixivRunStats.get_stats()

    caller.set_console_title(title_prefix)
    try:
        artist = br.fanboxGetArtistById(artist_id)
    except PixivException as pex:
        PixivHelper.print_and_log("error", f"Error getting FANBOX artist by id: {artist_id} ==> {pex.message}")
        if pex.errorCode != PixivException.USER_ID_SUSPENDED:
            stats.record_artist_error(f"artist {artist_id}: {pex.message}")
            return False
        try:
            artist = br.fanboxGetArtistById(artist_id, for_suspended=True)
        except Exception as ex:
            PixivHelper.print_and_log("error", f"Error getting suspended FANBOX artist {artist_id}: {ex}")
            stats.record_artist_error(f"artist {artist_id}: {ex}")
            return False

        formats = f"{config.filenameFormatFanboxCover}{config.filenameFormatFanboxContent}{config.filenameFormatFanboxInfo}"
        name_flag = "%artist%" in formats
        token_flag = "%member_token%" in formats
        if name_flag or token_flag:
            result = caller.__dbManager__.selectMemberByMemberId(artist.artistId)
            if result:
                artist.artistName = result[1]
                artist.artistToken = result[7]
                PixivHelper.print_and_log("info", f"Using saved artist name and token from db: {artist.artistName}, {artist.artistToken}")
            else:
                PixivHelper.print_and_log("warn", "Artist name or token found in FANBOX filename formats, but not in db.")
                if name_flag:
                    if artist.artistName:
                        PixivHelper.print_and_log("info", f"Using FANBOX artist name: {artist.artistName}")
                    else:
                        artist.artistName = input(f"Please input %artist% for {artist_id}: ").strip()
                if token_flag:
                    if artist.artistToken:
                        PixivHelper.print_and_log("info", f"Using FANBOX artist token: {artist.artistToken}")
                    elif artist.creatorId:
                        artist.artistToken = artist.creatorId
                        PixivHelper.print_and_log("info", f"Using creatorId as member_token: {artist.artistToken}")
                    else:
                        artist.artistToken = input(f"Please input %member_token% for {artist_id}: ").strip()
    except Exception as ex:
        PixivHelper.print_and_log("error", f"Unexpected error getting FANBOX artist {artist_id}: {ex}")
        PixivHelper.get_logger().exception("FANBOX artist lookup failed for %s", artist_id)
        stats.record_artist_error(f"artist {artist_id}: {ex}")
        return False

    current_page = 1
    next_url = None
    image_count = 1
    updated_limit_count = 0
    artist_had_error = False
    while True:
        PixivHelper.print_and_log("info", "Processing {0}, page {1}".format(artist, current_page))
        caller.set_console_title(f"{title_prefix} {artist}, page {current_page}")
        try:
            posts = br.fanboxGetPostsFromArtist(artist, next_url)
        except PixivException as pex:
            PixivHelper.print_and_log("error", "Error getting FANBOX posts of artist: {0} ==> {1}".format(artist, pex.message))
            artist_had_error = True
            stats.record_error(f"posts {artist_id}: {pex.message}")
            break
        except Exception as ex:
            PixivHelper.print_and_log("error", f"Unexpected error getting FANBOX posts of {artist}: {ex}")
            PixivHelper.get_logger().exception("FANBOX posts fetch failed for %s", artist_id)
            artist_had_error = True
            stats.record_error(f"posts {artist_id}: {ex}")
            break

        if posts is None:
            posts = []

        for post in posts:
            print("#{0}".format(image_count))
            try:
                post.printPost()
            except Exception:
                PixivHelper.print_and_log("warn", f"Unable to print post summary for post {getattr(post, 'imageId', '?')}")

            # images
            if post.type in PixivModelFanbox.FanboxPost._supportedType:
                try:
                    result = process_fanbox_post(caller, config, post, artist)
                except KeyboardInterrupt:
                    choice = input("Keyboard Interrupt detected, continue to next post? (Y/N)").rstrip("\r")
                    if choice.upper() == 'N':
                        PixivHelper.print_and_log("info", f"FANBOX artist: {artist}, processing aborted")
                        stats.record_artist_error(f"artist {artist_id}: aborted by user")
                        return False
                    else:
                        continue
                except Exception as ex:
                    # Do not abort the whole artist/list on a single bad post.
                    artist_had_error = True
                    detail = f"post {getattr(post, 'imageId', '?')} artist {artist_id}: {ex}"
                    PixivHelper.print_and_log("error", f"Error processing FANBOX post, continuing: {detail}")
                    PixivHelper.get_logger().exception("FANBOX post failed: %s", detail)
                    stats.record_error(detail)
                    image_count += 1
                    PixivHelper.wait(config=config)
                    continue

                if result == PixivConstant.PIXIVUTIL_SKIP_DUPLICATE:
                    stats.record_skip()
                    updated_limit_count += 1
                    if (config.checkUpdatedLimitFanbox != 0 and updated_limit_count >= config.checkUpdatedLimitFanbox):
                        PixivHelper.print_and_log(
                                "info",
                                f"Skipping FANBOX member: {artist.artistId}\n" +
                                f"(reached checkUpdatedLimitFanbox={config.checkUpdatedLimitFanbox})")
                        PixivBrowserFactory.getBrowser().clear_history()
                        stats.record_artist_ok()
                        return True
                    gc.collect()
                elif result == PixivConstant.PIXIVUTIL_SKIP_BLACKLIST:
                    stats.record_restricted()
                elif result == PixivConstant.PIXIVUTIL_OK:
                    stats.record_ok()
                    updated_limit_count = 0
                elif result == PixivConstant.PIXIVUTIL_NOT_OK:
                    stats.record_error(f"post {getattr(post, 'imageId', '?')}: download not ok")
                    artist_had_error = True
                else:
                    stats.bump(f"result_{result}")
            else:
                PixivHelper.print_and_log("info", f"Unsupported post type: {post.imageId} => {post.type}")
                stats.bump("unsupported_type")
            image_count += 1
            PixivHelper.wait(config=config)

        if not artist.hasNextPage:
            PixivHelper.print_and_log("info", "No more post for {0}".format(artist))
            break
        current_page += 1
        if 0 < end_page < current_page:
            PixivHelper.print_and_log("info", "Reaching page limit for {0}, limit {1}".format(artist, end_page))
            break
        next_url = artist.nextUrl
        if next_url is None:
            PixivHelper.print_and_log("info", "No more next page for {0}".format(artist))
            break

    if artist_had_error:
        stats.record_artist_error(f"artist {artist_id}: completed with errors")
        return False
    stats.record_artist_ok()
    return True


def process_fanbox_post(caller, config, post: PixivModelFanbox.FanboxPost, artist):
    # caller: AppContext (or main module) — prefer explicit repository façade.
    from db.repositories import Repositories
    repos = Repositories.from_caller(caller)
    db = repos.raw
    br = PixivBrowserFactory.getBrowser()

    repos.fanbox.insert_post(artist.artistId, post.imageId, post.imageTitle, post.feeRequired, post.worksDate, post.type)

    post_files = []

    flag_processed = False
    if config.checkDBProcessHistory:
        result = repos.fanbox.select_post(post.imageId)
        if result:
            updated_date = result[5]
            if updated_date is not None and post.updatedDateDatetime <= datetime_z.parse_datetime(updated_date):
                flag_processed = True

    try:
        if not post.is_restricted and not flag_processed:
            br.fanboxUpdatePost(post)

        if ((not post.is_restricted) or config.downloadCoverWhenRestricted) and (not flag_processed) and config.downloadCover:
            # cover image
            if post.coverImageUrl:
                # fake the image_url for filename compatibility, add post id and pagenum
                fake_image_url = post.coverImageUrl.replace("{0}/cover/".format(post.imageId),
                                                            "{0}_".format(post.imageId))
                filename = PixivHelper.make_filename(config.filenameFormatFanboxCover,
                                                     post,
                                                     artistInfo=artist,
                                                     tagsSeparator=config.tagsSeparator,
                                                     tagsLimit=config.tagsLimit,
                                                     fileUrl=fake_image_url,
                                                     bookmark=None,
                                                     searchTags='',
                                                     useTranslatedTag=config.useTranslatedTag,
                                                     tagTranslationLocale=config.tagTranslationLocale)
                filename = PixivHelper.sanitize_filename(filename, config.rootDirectory)
                post.linkToFile[post.coverImageUrl] = filename

                print("Downloading cover from {0}".format(post.coverImageUrl))
                print("Saved to {0}".format(filename))

                referer = "https://www.pixiv.net/fanbox/creator/{0}/post/{1}".format(artist.artistId, post.imageId)
                (result, filename) = PixivDownloadHandler.download_image(caller,
                                                                         post.coverImageUrl,
                                                                         filename,
                                                                         referer,
                                                                         config.overwrite,
                                                                         config.retry,
                                                                         config.backupOldFile,
                                                                         image=post,
                                                                         page=-1,
                                                                         download_from=PixivConstant.DOWNLOAD_FANBOX)
                post_files.append((post.imageId, -1, filename))
                PixivHelper.get_logger().debug("Download %s result: %s", filename, result)
            else:
                PixivHelper.print_and_log("info", "No Cover Image for post: {0}.".format(post.imageId))

        if post.is_restricted:
            PixivHelper.print_and_log("info", "Skipping post: {0} due to restricted post.".format(post.imageId))
            return PixivConstant.PIXIVUTIL_SKIP_BLACKLIST

        if flag_processed:
            PixivHelper.print_and_log("info", "Skipping post: {0} because it was downloaded before.".format(post.imageId))
            return PixivConstant.PIXIVUTIL_SKIP_DUPLICATE

        if post.images is None or len(post.images) == 0:
            PixivHelper.print_and_log("info", "No Image available in post: {0}.".format(post.imageId))
        else:
            print("Image Count = {0}".format(len(post.images)))
            referer = "https://www.pixiv.net/fanbox/creator/{0}/post/{1}".format(artist.artistId, post.imageId)
            jobs = []
            for current_page, image_url in enumerate(post.images):
                # fake the image_url for filename compatibility, add post id and pagenum
                fake_image_url = image_url.replace("{0}/".format(post.imageId),
                                                   "{0}_p{1}_".format(post.imageId, current_page))
                filename = PixivHelper.make_filename(config.filenameFormatFanboxContent,
                                                     post,
                                                     artistInfo=artist,
                                                     tagsSeparator=config.tagsSeparator,
                                                     tagsLimit=config.tagsLimit,
                                                     fileUrl=fake_image_url,
                                                     bookmark=None,
                                                     searchTags='',
                                                     useTranslatedTag=config.useTranslatedTag,
                                                     tagTranslationLocale=config.tagTranslationLocale)

                filename = PixivHelper.sanitize_filename(filename, config.rootDirectory)
                post.linkToFile[image_url] = filename
                print("Downloading image {0} from {1}".format(current_page, image_url))
                print("Saved to {0}".format(filename))
                jobs.append({
                    "url": image_url,
                    "filename": filename,
                    "referer": referer,
                    "page": current_page,
                })

            # filesize detection and overwrite issue
            _oldvalue = config.alwaysCheckFileSize
            config.alwaysCheckFileSize = False
            try:
                results = PixivDownloadHandler.download_image_list(
                    caller,
                    jobs,
                    config,
                    overwrite=False,
                    max_retry=config.retry,
                    backup_old_file=config.backupOldFile,
                    image=post,
                    download_from=PixivConstant.DOWNLOAD_FANBOX,
                )
            finally:
                config.alwaysCheckFileSize = _oldvalue

            for result, filename, page in results:
                if result == PixivConstant.PIXIVUTIL_KEYBOARD_INTERRUPT:
                    raise KeyboardInterrupt()
                post_files.append((post.imageId, page, filename))
                PixivHelper.get_logger().debug("Download %s result: %s", filename, result)

        # Implement #447
        filename = PixivHelper.make_filename(config.filenameFormatFanboxInfo,
                                             post,
                                             artistInfo=artist,
                                             tagsSeparator=config.tagsSeparator,
                                             tagsLimit=config.tagsLimit,
                                             fileUrl="{0}".format(post.imageId),
                                             bookmark=None,
                                             searchTags='',
                                             useTranslatedTag=config.useTranslatedTag,
                                             tagTranslationLocale=config.tagTranslationLocale)

        filename = PixivHelper.sanitize_filename(filename, config.rootDirectory)
        if config.writeImageInfo:
            post.WriteInfo(filename + ".txt")
        if config.writeHtml:
            if post.type == "article" or (len(post.images) >= config.minImageCountForNonArticle and len(post.body_text) > config.minTextLengthForNonArticle):
                html_template = PixivConstant.HTML_TEMPLATE
                if os.path.isfile("template.html"):
                    reader = PixivHelper.open_text_file("template.html")
                    html_template = reader.read()
                    reader.close()
                post.WriteHtml(html_template, config.useAbsolutePathsInHtml, filename + ".html")

        if config.writeUrlInDescription:
            PixivHelper.write_url_in_description(post, config.urlBlacklistRegex, config.urlDumpFilename)
    finally:
        if len(post_files) > 0:
            repos.fanbox.insert_post_images(post_files)

    repos.fanbox.update_post_date(post.imageId, post.updatedDate)
    return PixivConstant.PIXIVUTIL_OK


def process_pixiv_by_fanbox_id(caller, config, artist_id, start_page=1, end_page=0, tags=None, title_prefix=""):
    # Implement #1005
    config.loadConfig(path=caller.configfile)
    br = PixivBrowserFactory.getBrowser()

    caller.set_console_title(title_prefix)
    artist = br.fanboxGetArtistById(artist_id)
    PixivArtistHandler.process_member(caller,
                                      config,
                                      artist.artistId,
                                      user_dir='',
                                      page=start_page,
                                      end_page=end_page,
                                      bookmark=False,
                                      tags=tags,
                                      title_prefix=title_prefix)
