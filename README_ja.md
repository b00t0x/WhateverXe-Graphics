# WhateverXe Graphics

[English](README.md)

[WhateverXe](https://github.com/b00t0x/WhateverXe)用の署名済みグラフィックス資材と、
通常のmacOSインストーラーです。1つのpkgが起動中macOS用のpayloadを選び、
`/Library`へ配置してAuxKCを更新します。Systemファイルやsnapshotへのパッチは行いません。
OpenCore・EFIの設定は別途必要です。

対応GPU・機能・設定・既知の問題は[WhateverXe](https://github.com/b00t0x/WhateverXe)を
参照してください。WEXと本pkgのリリース番号は独立しています。
AppleIntelTGLCompatはpkgに含まれますが、ソースと共有ヘッダーはWEXリポジトリで管理します。
全対応macOSで単一ビルドを使用し、Common payloadに収録しています。

## 必要な構成

- WEXのREADMEに記載されたWEX・OpenCore構成を使用するIntel macOS。
- LiluとWhateverXe **0.3.0以上**。
- OpenCoreから読み込む[AMFIPass 1.4.1 Mod](extras/AMFIPass-v1.4.1-Mod-RELEASE.zip)。通常のupstream版AMFIPassでは、本資材の署名チェーンに対応できません。
- SIP設定`csr-active-config=03080000`（値`0x803`）。本pkgはSIP全面有効化には対応していません。

| macOS | 必要バージョン |
| --- | --- |
| Big Sur | 11.7.11 |
| Monterey | 12.7.6 |
| Ventura | 13.7.8 |
| Sonoma | 14.8.9 |
| Sequoia | 15.8.x |
| Tahoe | 26.7以上 |

受付範囲は将来のOS更新での動作保証ではありません。現在の資材の対象buildは
20G1443、21H1320、22H730、23J631、24H32、25G241です。
macOS更新前にWEXの説明とリリースノートを確認してください。
`amfi=0x80`と`ipc_control_port_options=0`は不要です。

## OCLPの他のroot patchとの併用

他のroot patchのためにOCLPを併用する場合は、
[独自ビルド版OCLP](https://github.com/b00t0x/OpenCore-Legacy-Patcher)を使用してください。
通常版OCLPとXeの資材ではAMFIPassのtrust anchorが異なり、1つのAMFIPassで
両方の署名に対応できません。独自版OCLPは本資材と同じMod署名チェーンを使用します。
併用の準備として独自版OCLPからXe root patchを除去する必要があり、この変更は後続で行います。

## インストール

1. OpenCoreにWEX・Liluとリンク先の**Mod版**AMFIPassを設定します。
   旧Xe System patchが適用されている場合は、その復元手順で先に戻してください。
2. 導入先のmacOSを起動します。
3. [Releases](https://github.com/b00t0x/WhateverXe-Graphics/releases)からpkgをダウンロードし、Installerで開きます。導入成功後に再起動してください。

通常のInstaller payloadとreceiptを使用します。AuxKCを更新し、Tahoeでは
`CoreMedia / AllowOnePassMetalScaling`を無効化します。
EFI・起動引数・SIPは変更しません。pkg自体は未署名・未公証ですが、改変したpayloadには
Mod署名が付いています。導入エラーが出た場合は、問題を解決して再導入してから再起動してください。

## アンインストール

このリポジトリの最新の[`uninstall.sh`](uninstall.sh)をダウンロードし、次を実行します。

```sh
sudo bash uninstall.sh
```

削除成功後に再起動してください。本プロジェクトが配布するグラフィックス資材と
scalingの上書き設定を削除し、AuxKCを更新してグラフィックスpkgのreceiptを解除します。
導入したpkgのバージョンによらず最新のスクリプトを使用します。他のCoreMedia設定は維持します。
EFI内のWEX・Lilu・AMFIPassの削除や、以前のグラフィックス構成の復元は行いません。

AMFIPassと削除スクリプトは、グラフィックスpkgとは独立してリポジトリで管理します。
Releaseに添付するのはpkgとそのチェックサムです。

## ビルド

Xcode Command Line ToolsとPython 3.10以上を用意したmacOSで実行します。

```sh
python3 tools/build.py
python3 tools/test.py dist/WhateverXe-Graphics-0.1.0.pkg
```

検証にはNode.jsと`rcodesign` 0.29.0も必要です。CIでは両方を用意します。
ビルダーはGit内の署名済み`payloads/Common`とOS別ディレクトリを使用し、
Apple原本の取得・バイナリ改変・署名鍵の使用は行いません。出力先は`dist/`です。
導入先MacにPython・Node.js・rcodesignを用意する必要はありません。

[ソース・署名情報](docs/SOURCES.md)。パッケージング用ツールのライセンスは第三者の
payloadには適用されません。[権利表記](THIRD_PARTY.md)を参照してください。
