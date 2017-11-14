#!/usr/bin/env python
import json
import time
import os  # for path
import selenium
import boto3
import random  # for tmp file name
import string  # for tmp file name
import shutil  # for remove tmp file and dir

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from PIL import Image


def webshot(event, context):
    """
    lambda実行するmain関数
    """
    # ------ 計測用 start ------ #
    start = time.time()
    # ------ 計測用 end ------ #

    # for sls invoke local -f THIS_FUNCTION
    if os.environ.get('IS_LOCAL') and os.path.exists('invoke_local.json'):
        f = open('invoke_local.json', 'r')
        data = json.load(f)
        os.environ.update(data)

    # ワーキングディレクトリの作成とテンポラリファイルの情報取得
    tmp_info = make_work_dir()

    # selenium + phantomjsでスクリーンショット
    screenshot_website(event, tmp_info)

    # スクリーンショットの加工
    resize_screenshot(tmp_info)

    # S3へput
    put_s3_scr_thumb(event, tmp_info)

    # ------ 計測用 start ------ #
    print ("webshot_time:{0}".format(time.time() - start) + "[sec]")
    # ------ 計測用 end ------ #

    # tmp配下の一時保存ディレクトリをファイル毎削除
    shutil.rmtree(tmp_info["tmp_dir_path"])

    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }
    return response


def make_work_dir():
    """
    ワーキングディレクトリとスクリーンショットを保存するパスを作成する関数
    @return dict ワーキングディレクトリと保存先のパス
    """
    # tmpファイル名をランダムハッシュ化し一時保存先のファイルパスを作成
    ram_hash = ''.join(
        random.sample(
            ''.join([string.ascii_lowercase, string.digits]),
            int(os.environ.get("TMP_FILENAME_RAM_SIZE"))
        )
    )

    # 一時保存先ディレクトリとファイル名
    tmp_dir_path = os.path.join(os.environ.get("TMP_DIST"), ram_hash)

    # tmp_dir作成
    if not os.path.exists(tmp_dir_path):
        try:
            os.makedirs(tmp_dir_path)
        except OSError as e:
            raise Exception("tmp_dir create error", e)

    # 一時保存先ファイルパス宣言
    # ウェブショット(PhantomJS用)
    tmp_file_path_web = os.path.join(tmp_dir_path, "".join(
        [ram_hash, "_web", ".", os.environ.get("SCR_EXTENTION")]
    ))
    # スクリーンショット(加工後)
    tmp_file_path_screen = os.path.join(tmp_dir_path, "".join(
        [ram_hash, "_screen", ".", os.environ.get("SCR_EXTENTION")]
    ))
    # サムネイル(加工後)
    tmp_file_path_thumb = os.path.join(tmp_dir_path, "".join(
        [ram_hash, "_thumb", ".", os.environ.get("SCR_EXTENTION")]
    ))
    return {
        "tmp_dir_path": tmp_dir_path,
        "tmp_file_path_web": tmp_file_path_web,
        "tmp_file_path_screen": tmp_file_path_screen,
        "tmp_file_path_thumb": tmp_file_path_thumb
    }


def screenshot_website(event, tmp_info):
    """
    selenium + phantomjsで対象のウェブサイトをスクリーンショットする関数
    @param  event lambdaが受け取ったevent
    @param  tmp_info ワーキングディレクトリと保存先のパス
    """

    pahtonmjs_conf = json.loads(os.environ.get("PHANTOMJS_CONF"))

    # set user agent
    user_agent = os.environ.get("SELENIUM_USER_AGENT")

    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = user_agent
    dcap["phantomjs.page.settings.javascriptEnabled"] = True
    phantompath = os.getcwd() + "/phantomjs"

    try:
        browser = webdriver.PhantomJS(
            service_log_path=os.path.devnull,
            executable_path=phantompath,
            service_args=['--ignore-ssl-errors=true'],
            desired_capabilities=dcap
        )

        browser.set_window_position(
            pahtonmjs_conf["POSTION_TOP"],
            pahtonmjs_conf["POSTION_LEFT"]
        )
        browser.set_window_size(
            pahtonmjs_conf["VIEWPORT_WIDTH"],
            pahtonmjs_conf["VIEWPORT_HEIGHT"]
        )

        # スクリーンショット作成
        browser.get(event["url"])
        browser.save_screenshot(os.path.join(tmp_info["tmp_file_path_web"]))
        # 一応seleniumは終了させておく
        browser.quit()

    except Exception as e:
        # tmp配下の一時保存ディレクトリをファイル毎削除
        shutil.rmtree(tmp_info["tmp_dir_path"])
        raise Exception("selenium error", e)
    return


def resize_screenshot(tmp_info):
    """
    スクリーンショットをリサイズし一時ディレクトリに保存する関数
    @param  tmp_info ワーキングディレクトリと保存先のパス
    """

    pil_conf = json.loads(os.environ.get("PIL_CONF"))

    try:
        img = Image.open(tmp_info["tmp_file_path_web"], 'r')
        # スクリーンショット加工 img.crop(left=left, top=top, right=right, bottom=bottom)
        screen_img = img.crop((
            pil_conf["IMG_CROP_LEFT"],
            pil_conf["IMG_CROP_TOP"],
            pil_conf["IMG_CROP_RIGHT"],
            pil_conf["IMG_CROP_BOTTOM"]
        )).resize((
            pil_conf["SCR_RESIZE_WIDTH"],
            pil_conf["SCR_RESIZE_HEIGHT"]
        ), Image.ANTIALIAS)

        # サムネイル加工
        thumb_img = screen_img.resize((
            pil_conf["THUMB_RESIZE_WIDTH"],
            pil_conf["THUMB_RESIZE_HEIGHT"]
        ), Image.ANTIALIAS)

        # スクリーンショット保存
        screen_img.save(
            tmp_info["tmp_file_path_screen"],
            os.environ.get("SCR_EXTENTION"),
            quality=100
        )
        # サムネイル保存
        thumb_img.save(
            tmp_info["tmp_file_path_thumb"],
            os.environ.get("SCR_EXTENTION"),
            quality=100
        )
    except Exception as e:
        # tmp配下の一時保存ディレクトリをファイル毎削除
        shutil.rmtree(tmp_info["tmp_dir_path"])
        raise Exception("PIL Image error", e)
    return


def put_s3_scr_thumb(event, tmp_info):
    """
    加工したスクリーンショットをS3にputする関数
    @param  event lambdaが受け取ったevent
    @param  tmp_info ワーキングディレクトリと保存先のパス
    """

    try:
        session = boto3.session.Session()
        s3_client = session.client(
            service_name='s3',
            endpoint_url=os.environ.get("S3_ENDPOINT_URL")
        )
        s3_client.upload_file(
            Filename=tmp_info["tmp_file_path_screen"],
            Bucket=os.environ.get("S3_BUCKET"),
            Key=event["screenshotPath"]
        )
        s3_client.upload_file(
            Filename=tmp_info["tmp_file_path_thumb"],
            Bucket=os.environ.get("S3_BUCKET"),
            Key=event["thumbnailPath"]
        )
    except Exception as e:
        # tmp配下の一時保存ディレクトリをファイル毎削除
        shutil.rmtree(tmp_info["tmp_dir_path"])
        raise Exception("aws s3 error", e)
    return
