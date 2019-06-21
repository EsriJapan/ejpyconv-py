# coding:utf-8
"""
Tool name : ポリゴン同士重なる領域を削除
Source    : DelOverlapPoly.py
Author    : Esri Japan Corporation
Created   : 2019/6/21
Updated   :
"""

class AlreadyExistError(Exception):
    pass


import arcpy
import sys
import os


def setup_del_overlap_poly():
    """
    メソッド名 : setup_del_overlap_poly メソッド
    概要       : ポリゴン同士重なる領域を削除に用いる入力情報の作成
    """
    in_poly_fc1 = arcpy.GetParameterAsText(0)
    in_poly_fc2 = arcpy.GetParameterAsText(1)
    out_poly_fc = arcpy.GetParameterAsText(2)

    del_overlap_poly(in_poly_fc1, in_poly_fc2, out_poly_fc)


def del_overlap_poly(in_poly_fc1, in_poly_fc2, out_poly_fc):
    """
    メソッド名 : del_overlap_poly メソッド
    引数 1     : 入力フィーチャ
    引数 2     : 参照ポリゴンフィーチャ
    引数 3     : 出力フィーチャ
    概要       : ポリゴンの重なる領域を削除
    """
    try:
        arcpy.AddMessage(u"処理開始：")
        in_fc_name = os.path.basename(in_poly_fc1)
        in_ws = os.path.dirname(in_poly_fc1)
        out_fc_name = os.path.basename(out_poly_fc)
        out_ws = os.path.dirname(out_poly_fc)

        # 出力データの作成
        arcpy.CopyFeatures_management(in_poly_fc1, out_poly_fc)

        # ディゾルブ
        arcpy.Dissolve_management(in_poly_fc2, r"memory/dissolve")

        polygons = [row[0] for row in arcpy.da.SearchCursor(r"memory/dissolve", "SHAPE@")]
        outcur = arcpy.da.UpdateCursor(out_poly_fc, "SHAPE@")

        for inrow in outcur:
            for polygon in polygons:
                # ポリゴンが重なっていたら重なる部分を削除
                if inrow[0].overlaps(polygon):
                    outcur.updateRow([inrow[0].difference(polygon)])
                else:
                    pass

        # 後始末
        del outcur

        arcpy.AddMessage(u"処理終了：")
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


if __name__ == u'__main__':
    setup_del_overlap_poly()
