# lambda-python3-PhantomJS
python3のlambdaでphantomjsをつかったwebshotのサンプルです。日本語文字化け対策としてfontconfigの設定しています。

実行環境：
- Ubuntu 16.04.2
- python 3.6
- Serverless framework 1.24.1

# fontconfig依存ライブラリインストール
```sh
１・fontconfigの依存ライブラリをインストール
$ sudo apt-get update
$ sudo apt-get install gperf python-lxml libtool autoconf automake libfreetype6-dev
$ sudo apt-get install libfontconfig1-dev
$ sudo mkdir -p /var/task
$ cd /var/task

$ git clone http://anongit.freedesktop.org/git/fontconfig
$ cd fontconfig
$ sudo ./autogen.sh --sysconfdir=/var/task/fontconfig/etc --prefix=/var/task/fontconfig/usr --mandir=/var/task/fontconfig/usr/share/man --enable-libxml2

# freetype2のバージョンが低い場合下記を実施
# 参考url:http://ubuntuhandbook.org/index.php/2017/06/install-freetype-2-8-in-ubuntu-16-04-17-04/
$ sudo add-apt-repository ppa:glasen/freetype2
$ sudo apt update && sudo apt install freetype2-demos

# libxml-2.0のバージョンが低い場合下記を実施
# 参考url:http://libxmlplusplus.sourceforge.net/docs/manual/html/
$sudo apt-get install libxml++2.6-dev libxml++2.6-doc

$ sudo make
$ sudo make install

# local.confの作成
$sudo vim /var/task/fontconfig/etc/fonts/local.conf
'''
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>/var/task/fontconfig/usr/share/fonts</dir>
</fontconfig>
'''

# ipaフォント配置
$ cd  /var/task/fontconfig/usr/share/fonts/
$ curl http://dl.ipafont.ipa.go.jp/IPAexfont/ipaexg00301.zip > ipaexg00301.zip
$ unzip ipaexg00301.zip
$ sudo cp ipaexg00301/ipaexg.ttf ./

# font cacheクリア
$ sudo /var/task/fontconfig/fc-cache/fc-cache
$ sudo /var/task/fontconfig/fc-list/fc-list
※以下が反映されていることを確認
'''
~~~省略~~~
/var/task/fontconfig/usr/share/fonts/ipaexg.ttf: IPAexGothic:style=Regular
~~~省略~~~
'''

# fontconfigをワーキングディレクトリへコピー
$ sudo cp -frL /var/task/fontconfig/etc  /{ワーキングディレクトリ}/fontconfig/
$ sudo cp -frL /var/task/fontconfig/usr  /{ワーキングディレクトリ}/fontconfig/
```

# 実行例
```sh
 sls invoke local -f webshot -p event.json
```
※ローカルで動かす時はS3サーバを立ててください。
参考：https://github.com/jamhall/s3rver

# デプロイ
```sh
 sls deploy -s {{stage}}
```
※serverless.ymlの設定で任意にステージを分けてください。
