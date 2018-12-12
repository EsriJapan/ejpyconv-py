# EJPyConv

  ArcPy で書かれた ArcGIS Pro 用の複数の便利なツールが含まれている「サンプル ジオプロセシングツールボックス」です。
  ArcGIS Pro へツールボックスを追加することで、各種ジオプロセシング ツールとして利用が可能です。
  ツールボックスの追加方法は以下のヘルプ ページをご覧ください。また、コンパイル済みのものは[こちら](https://github.com/EsriJapan/ejpyconv-py/releases)にあります。

ツールボックスへの接続  
https://pro.arcgis.com/ja/pro-app/help/projects/connect-to-a-toolbox.htm

## ジオプロセシング ツールボックスの内容

  各種ジオプロセシング ツール として、次のものが含まれています（2018/12/xx 現在）。
  
  [ジオメトリ操作 - ツール ボックス]
  * ポイントをポリゴンへ変換（PtToPoly）
  * ポリゴンの重心点をポイントへ変換（PolyCenterToPt）
  * ポリゴンの頂点をポイントへ変換（PolyVertexToPt）
  * ポリゴンをラインへ変換（PolyToLine）
  * ラインの始終点をポイントへ変換（LineStartingAndEndingPtToPt）
  * ラインの共有点をポイントへ変換（LineJunctionPtToPt）
  * ラインの中間点をポイントへ変換（LineMidPtToPt）
  * ラインの頂点をポイントへ変換（LineVertexToPt）
  * 凸包の作成（CreateConvexhull）
  * 内向きバッファーの作成（CreateInsideBuffer）

## 動作確認環境

  ジオプロセシング ツールの動作確認を行った環境は、次の通りです。
  * [ArcGIS Pro 2.2](https://www.esrij.com/products/arcgis-desktop/environments/arcgis-pro/)

## ArcGIS Pro への適用方法

使い方は [EJPyConv_setup_wiki](https://github.com/EsriJapan/ejpyconv-py/wiki/EJPyConv_setup_wiki) をご覧ください。

## 免責事項
  
  * 本ツールボックスに含まれるジオプロセシング ツールはサンプルとして提供しているものであり、Esri 製品の計画をサポートするための保証、サービスレベルアグリーメント（SLA）、製品ライフサイクルを提供しておりません。
  * ツールボックスに含まれるジオプロセシング ツールによって生じた損害等の一切の責任を負いかねますのでご了承ください。
  * 弊社で提供しているEsri 製品サポートサービスでは、本ツールに関しての Ｑ＆Ａ サポートの受付を行っておりませんので、予めご了承の上、ご利用ください。詳細は[
ESRIジャパン GitHub アカウントにおけるオープンソースへの貢献について](https://github.com/EsriJapan/contributing)をご参照ください。



## ライセンス
Copyright 2018 Esri Japan Corporation.

Apache License Version 2.0（「本ライセンス」）に基づいてライセンスされます。あなたがこのファイルを使用するためには、本ライセンスに従わなければなりません。
本ライセンスのコピーは下記の場所から入手できます。

> http://www.apache.org/licenses/LICENSE-2.0

適用される法律または書面での同意によって命じられない限り、本ライセンスに基づいて頒布されるソフトウェアは、明示黙示を問わず、いかなる保証も条件もなしに「現状のまま」頒布されます。本ライセンスでの権利と制限を規定した文言については、本ライセンスを参照してください。

ライセンスのコピーは本リポジトリの[ライセンス ファイル](./LICENSE)で利用可能です。