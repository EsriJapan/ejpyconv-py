# coding:utf-8
"""
Tool name : ポリゴンを穴埋め
Source    : PolyFillingUp.py
Author    : Esri Japan Corporation
Created   : 2019/6/21
Updated   :
"""

class AlreadyExistError(Exception):
    pass


import arcpy
import sys
import os


def setup_poly_filling_up():
    """
    メソッド名 : setup_poly_filling_up メソッド
    概要       : ポリゴンの穴埋めに用いる入力情報の作成
    """
    in_poly_fc = arcpy.GetParameterAsText(0)
    out_poly_fc = arcpy.GetParameterAsText(1)

    poly_filling_up(in_poly_fc, out_poly_fc)


def poly_filling_up(in_poly_fc, out_poly_fc):
    """
    メソッド名 : poly_filling_up メソッド
    引数 1     : 入力フィーチャ
    引数 2     : 出力フィーチャ
    概要       : ポリゴンを穴埋め
    """
    try:
        arcpy.AddMessage(u"処理開始：")
        in_fc_name = os.path.basename(in_poly_fc)
        in_ws = os.path.dirname(in_poly_fc)
        out_fc_name = os.path.basename(out_poly_fc)
        out_ws = os.path.dirname(out_poly_fc)

        # 出力データの作成
        arcpy.CopyFeatures_management(in_poly_fc, out_poly_fc)

        outcur = arcpy.da.UpdateCursor(out_poly_fc, "SHAPE@")

        for inrow in outcur:
            polygon = arcpy.Array()
            for part in inrow[0]:
                new_part = arcpy.Array()
                # Nullになるポイント(interior ring の最初)を取得
                null_point = 0
                for i in range(len(part)):
                    if part[i] == None:
                        null_point = i
                        break
                # 穴あきポリゴンでない場合パートの数そのまま
                if null_point == 0:
                    polygon.add(part)
                # 穴あきポリゴンの場合パートの数をinterior ringの一つ前のポイントまでに
                else:
                    for j in range(null_point):
                        new_part.add(part[j])
                    polygon.add(new_part)
            if len(polygon) > 0:
                new_poly = arcpy.Polygon(polygon)
                inrow[0] = new_poly
                outcur.updateRow(inrow)

        # 後始末
        del outcur

        arcpy.AddMessage(u"処理終了：")
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


if __name__ == u'__main__':
    setup_poly_filling_up()
