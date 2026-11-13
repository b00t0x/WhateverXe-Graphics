# WhateverXe Graphics

[English](README.md)

[WhateverXe](https://github.com/b00t0x/WhateverXe)用の署名済みグラフィックスドライバーとmacOSインストーラーです。`/Library`への配置とAuxKC生成を行い、Systemファイルやsnapshotにはパッチしません。
WEXとGraphicsは両方とも最新版を使用してください。対応GPU・設定・既知の問題は[WEX](https://github.com/b00t0x/WhateverXe/blob/main/README_ja.md)、pkgの変更点は[CHANGELOG](CHANGELOG.md)を参照してください。

## 必要な構成

- Lilu・最新版WEX・[AMFIPass 1.4.1 Mod](extras/AMFIPass-v1.4.1-Mod-RELEASE.zip)を設定したOpenCore。本家AMFIPassでは代用できません。
- SIP設定`csr-active-config=03080000`（`0x803`）。SIP全面有効には対応していません。

| macOS | 必要バージョン |
| --- | --- |
| Big Sur | 11.7.11 |
| Monterey | 12.7.6 |
| Ventura | 13.7.8 |
| Sonoma | 14.8.9 |
| Sequoia | 15.8.x |
| Tahoe | 26.7以上 |

OCLPの他のroot patchを併用する場合は、同じMod署名に対応した[独自ビルド版OCLP](https://github.com/b00t0x/OpenCore-Legacy-Patcher)を使用してください。

## インストール

1. [WEXの手順](https://github.com/b00t0x/WhateverXe/blob/main/README_ja.md#インストール)に従ってOpenCoreを設定し、旧Xe System patchがあれば先に復元します。
2. 対象macOSを起動し、[Releases](https://github.com/b00t0x/WhateverXe-Graphics/releases)の`WhateverXe-Graphics-*.pkg`を開きます。
3. 導入成功後に再起動します。エラーが出た場合は解決してから再起動してください。

インストーラーはEFI・SIPを変更しません。pkg自体は未署名・未公証ですが、改変したグラフィックス資材にはMod署名が付いています。

## セットアップ前の自動インストール

AutoPkgは**新規macOSインストール中**にグラフィックス加速を有効にします。SequoiaとTahoeで実機確認済みです。

1. 対応するmacOSのインストーラーUSBを作成し、Releasesから[`AutoPkg-Assets.pkg`](https://github.com/b00t0x/WhateverXe-Graphics/releases/latest/download/AutoPkg-Assets.pkg)をダウンロードします。
2. ファイル名を変えず、USB内の`Library/Packages/`へコピーします。`Packages`がなければ作成してください。不可視の`Library`を開くには、USBのボリューム名に合わせて次を実行します。

   ```sh
   open "/Volumes/Install macOS Tahoe/Library"
   ```

3. Lilu・WEX・Mod AMFIPassに加え、本家[AutoPkgInstaller 1.0.4](https://github.com/dortania/OpenCore-Legacy-Patcher/blob/main/payloads/Kexts/Acidanthera/AutoPkgInstaller-v1.0.4-RELEASE.zip)をOpenCoreに追加します。`csr-active-config=030A0000`（`0xA03`）を設定し、Tahoeでは`-autopkgbeta`も追加します。
4. 通常どおりmacOSをインストールします。追加再起動を経てセットアップアシスタントから加速が有効になります。最初のUSBインストーラー画面は加速されません。

AutoPkgを手動で開かないでください。既存環境・更新には通常pkgを使用し、同じUSBでWEXとOCLPのAutoPkgを併用しないでください。OCLPアプリ・KDK・MetallibSupportPkgは不要です。
`0xA03`は未承認kextのロードを許可する設定で、追加の`0x200`を後から外しても承認が維持されるとは限りません。

## アンインストール

最新版の[`uninstall.sh`](uninstall.sh)をダウンロードし、実行後に再起動します。

```sh
sudo bash uninstall.sh
```

どちらの方法で導入したGraphicsも削除し、AuxKCを生成し直します。EFIの部品は削除せず、以前のグラフィックス構成も復元しません。導入エラーは`/var/log/install.log`で確認できます。

## ビルド

macOS、Xcode Command Line Tools、Python 3.10以上が必要です。検査にはNode.jsと`rcodesign` 0.29.0も使用します。

```sh
python3 tools/build.py
python3 tools/test.py dist/WhateverXe-Graphics-0.4.4.pkg
```

AutoPkgはビルド時に`--autopkg`を追加し、`dist/autopkg/AutoPkg-Assets.pkg`を検査します。
検査コマンドに`--native-history`を追加すると、展開したpayloadで過去版のPCI dispatchとGL URB補正を再生します。ネイティブまたはRosetta経由のx86_64実行環境が必要です。
Git内の署名済み資材を使用するため、Apple原本の取得や署名鍵は不要です。

[ソース・署名情報](docs/SOURCES.md) · [第三者の権利表記](THIRD_PARTY.md)
