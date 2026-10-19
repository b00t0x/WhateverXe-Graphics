# WhateverXe Graphics

[English](README.md)

[WhateverXe](https://github.com/b00t0x/WhateverXe)用の署名済みグラフィックス資材と、
通常のmacOSインストーラーです。1つのpkgが起動中macOS用のpayloadを選び、
`/Library`へ配置してAuxKCを更新します。Systemファイルやsnapshotへのパッチは行いません。
OpenCore・EFIの設定は別途必要です。

対応GPU・機能・設定・既知の問題は[WhateverXe](https://github.com/b00t0x/WhateverXe)を
参照してください。WEXと本pkgのリリース番号は独立しています。
AppleIntelTGLCompatはpkgに含まれますが、ソースと共有ヘッダーはWEXリポジトリで管理します。

## 必要な構成

- WEXのREADMEに記載されたWEX・OpenCore構成を使用するIntel macOS。
- LiluとWhateverXe **0.3.0以上**。
- OpenCoreから読み込む[AMFIPass 1.4.1 Mod](https://github.com/b00t0x/WhateverXe-Graphics/releases/latest/download/AMFIPass-v1.4.1-Mod-RELEASE.zip)。通常のupstream版AMFIPassでは、本資材の署名チェーンに対応できません。
- SIP設定`csr-active-config=03080000`（値`0x803`）。本pkgはSIP全面有効化には対応していません。

| macOS | インストーラーの受付範囲 |
| --- | --- |
| Big Sur | 11.7.11以上、12未満 |
| Monterey | 12.7.6以上、13未満 |
| Ventura | 13.7.8以上、14未満 |
| Sonoma | 14.8.9以上、15未満 |
| Sequoia | 15.8.x |
| Tahoe | 26.7以上、27未満 |

受付範囲は将来のOS更新での動作保証ではありません。現在の資材の対象buildは
20G1443、21H1320、22H730、23J631、24H32、25G241です。
macOS更新前にWEXの説明とリリースノートを確認してください。
`amfi=0x80`と`ipc_control_port_options=0`は不要です。

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

同じReleaseの`uninstall.sh`をダウンロードし、次を実行します。

```sh
sudo bash uninstall.sh
```

削除成功後に再起動してください。追加したXeグラフィックス資材とscalingの上書き設定を
削除し、AuxKCを更新して本pkgのreceiptを解除します。他のCoreMedia設定は維持します。
EFI内のWEX・Lilu・AMFIPassの削除や、以前のグラフィックス構成の復元は行いません。

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
