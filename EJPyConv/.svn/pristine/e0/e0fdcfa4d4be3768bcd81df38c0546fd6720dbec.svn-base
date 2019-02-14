# coding:utf-8
"""
Tool name : 内向きバッファーの作成
Source    : CreateInsideBuffer.py
Author    : Esri Japan Corporation
Created   : 2018/12/14
Updated   :
"""

class AlreadyExistError(Exception):
    pass


import arcpy
import sys
import os


def setup_create_inside_buffer():
    """
    メソッド名 : setup_create_inside_buffer メソッド
    概要       : バッファー作成に用いる入力情報の作成
    """
    in_poly_fc = arcpy.GetParameterAsText(0)
    out_poly_fc = arcpy.GetParameterAsText(1)
    buffer_distace = arcpy.GetParameter(2)

    create_inside_buffer(in_poly_fc, out_poly_fc, buffer_distace)


def create_inside_buffer(in_poly_fc, out_poly_fc, buffer_distace):
    """
    メソッド名 : create_inside_buffer メソッド
    引数 1     : 入力フィーチャ
    引数 2     : 出力フィーチャ
    引数 3     : バッファーの距離
    概要       : 内向きバッファーの作成
    """
    try:
        arcpy.AddMessage(u"処理開始：")
        in_fc_name = os.path.basename(in_poly_fc)
        in_ws = os.path.dirname(in_poly_fc)
        out_fc_name = os.path.basename(out_poly_fc)
        out_ws = os.path.dirname(out_poly_fc)

        # 出力データの作成
        arcpy.CopyFeatures_management(in_poly_fc,out_poly_fc)

        outcur = arcpy.da.UpdateCursor(out_poly_fc,["SHAPE@"])
        
        i = 0
        num = int(arcpy.GetCount_management(out_poly_fc).getOutput(0))
        ngcnt = 0

        # バッファ作成
        for inrow in outcur:
            i = i + 1
            if (i == 1) or (i == num) or (i % 1000 == 1):
                s = u"{0}/{1}の処理中・・・".format(i, num)
                arcpy.AddMessage(s)

            inbuffer = inrow[0].buffer(float(buffer_distace) * -1)
            if inbuffer.area == 0.0:
                ngcnt += 1
            else:
                outcur.updateRow([inrow[0].difference(inbuffer)])

        if ngcnt != 0:
            arcpy.AddWarning("内向きバッファのサイズが元のポリゴンの範囲を超えていたため、作成できなかったデータがあります")

        # 後始末
        del outcur

        arcpy.AddMessage(u"処理終了：")

    except AlreadyExistError:
        arcpy.AddError(u"{0}に{1}はすでに存在しています".format(out_ws, out_fc_name))
    except arcpy.ExecuteError:
        # print arcpy.GetMessages(2)
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        # print e.args[0]
        arcpy.AddError(e.args[0])


if __name__ == u'__main__':
    setup_create_inside_buffer()
