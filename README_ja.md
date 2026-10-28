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

各pkgバージョンの変更点は[CHANGELOG](CHANGELOG.md)を参照してください。

## 必要な構成

- WEXのREADMEに記載されたWEX・OpenCore構成を使用するIntel macOS。
- Liluと最新版のWhateverXe。
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

## WEXとの関係

WEXはOS・GPUへの適応処理と表示制御を担当します。本pkgはグラフィックスドライバー、
コンパイラー関連部品、およびドライバー共通サービスを提供するAppleIntelTGLCompatを含みます。
両者のリリース番号を揃える必要はありません。

両方とも最新版を使用してください。GPU・表示に必要な設定は
[WEXの設定ガイド](https://github.com/b00t0x/WhateverXe/blob/main/README_ja.md#設定)を参照してください。

## OCLPの他のroot patchとの併用

他のroot patchのためにOCLPを併用する場合は、
[独自ビルド版OCLP](https://github.com/b00t0x/OpenCore-Legacy-Patcher)を使用してください。
通常版OCLPとXeの資材ではAMFIPassのtrust anchorが異なり、1つのAMFIPassで
両方の署名に対応できません。独自版OCLPは本資材と同じMod署名チェーンを使用します。

## インストール

1. OpenCoreにWEX・Liluとリンク先の**Mod版**AMFIPassを設定します。
   旧Xe System patchが適用されている場合は、その復元手順で先に戻してください。
2. 導入先のmacOSを起動します。
3. [Releases](https://github.com/b00t0x/WhateverXe-Graphics/releases)からpkgをダウンロードし、Installerで開きます。導入成功後に再起動してください。

通常のInstaller payloadとreceiptを使用します。AuxKCを更新し、Tahoeでは
`CoreMedia / AllowOnePassMetalScaling`を無効化します。
EFI・起動引数・SIPは変更しません。pkg自体は未署名・未公証ですが、改変したpayloadには
Mod署名が付いています。導入エラーが出た場合は、問題を解決して再導入してから再起動してください。

## セットアップ前の自動インストール（実験的機能）

追加の`AutoPkg-Assets.pkg`は、新規macOSインストールの途中で同じGraphics資材を配置し、
AuxKC生成後の再起動を標準Installerに要求します。OCLPの
[AutoPkgInstaller.kext](https://github.com/dortania/OpenCore-Legacy-Patcher/tree/main/payloads/Kexts/Acidanthera)
を使用し、OCLPアプリの同梱・導入は不要です。初回起動時の加速をこの機能に任せる前に、
テスト用インストールで検証してください。

1. 上記のOSバージョン条件を満たすmacOSインストーラーUSBを作成します。
2. Lilu・WEX・**Mod版**AMFIPassに加え、本家AutoPkgInstaller 1.0.4をOpenCoreに設定します。
   Tahoeでは`-autopkgbeta`が必要です。この引数はOS上限を回避するもので、互換性の保証ではありません。
3. インストーラー起動前に`csr-active-config=030A0000`（値`0xA03`）を設定します。
   追加の`0x200`はPrivacy & Securityでの承認を省略するもので、WEXに限らず全kextに適用されます。
   インストール後に外しても承認が維持されるとは限りません。
4. `python3 tools/build.py --autopkg`で生成した`dist/autopkg/AutoPkg-Assets.pkg`を、
   USBルートの`Library/Packages/`へコピーします。同じpkgで上記6 OSに対応します。
   ファイル名は変更せず、OCLP本家のpkgとも置き換えないでください。
5. 通常どおりmacOSをインストールします。起動中のOS用資材を選択し、AuxKCを生成して、
   セットアップアシスタント前の追加再起動を要求します。最初のUSBインストーラー画面は加速されません。

AutoPkgはscriptだけの1 componentで構成します。内部資材としてCommonと全対応OS分を保持し、
Commonと検出したOSの資材だけを`/Library`へコピーします。内部資材はInstallerの一時領域に置かれます。
通常のGraphics pkgは標準payloadとInstaller UIによるOS選択を引き続き使用します。

AutoPkgを手動で開かないでください。セットアップ済みOS、起動中ではない対象ボリューム、
対応範囲外のOS、旧System-volume patch、既存Graphics bundle（導入途中の残存物を含む）を拒否します。
新規OSインストール専用であり、この判定は誤実行防止用で、セキュリティ境界ではありません。
上書きアップグレード、Software Update／OTA、同じUSBでのWEXとOCLP AutoPkgの併用は対象外です。
WEX資材のためのKDK.pkg・MetallibSupportPkg.pkgは不要です。導入失敗時は`/var/log/install.log`を確認してください。

完了処理と再起動要求はInstallerが扱います。scriptは強制再起動や未確定receiptの照会を行いません。
script-only componentの識別子は`org.b00t0x.WhateverXe.AutoGraphics`として導入ログに記録されます。
`--nopayload`で生成するため、package receiptは残りません。導入成功は`/var/log/install.log`と
`/Library/Receipts/InstallHistory.plist`で確認してください。
以下の共通の単独uninstallerで導入したGraphicsファイルを削除できます。

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
python3 tools/test.py dist/WhateverXe-Graphics-0.3.2.pkg
```

自動インストール用pkgの生成と検査：

```sh
python3 tools/build.py --autopkg
python3 tools/test.py dist/autopkg/AutoPkg-Assets.pkg
```

検証にはNode.jsと`rcodesign` 0.29.0も必要です。CIでは両方を用意します。
ビルダーはGit内の署名済み`payloads/Common`とOS別ディレクトリを使用し、
Apple原本の取得・バイナリ改変・署名鍵の使用は行いません。出力先は`dist/`です。
導入先MacにPython・Node.js・rcodesignを用意する必要はありません。

[ソース・署名情報](docs/SOURCES.md)。パッケージング用ツールのライセンスは第三者の
payloadには適用されません。[権利表記](THIRD_PARTY.md)を参照してください。
