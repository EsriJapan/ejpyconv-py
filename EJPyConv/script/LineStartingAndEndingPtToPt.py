﻿# coding:utf-8
"""
Tool name : ラインの始終点をポイントへ変換
Source    : LineStartingAndEndingPtToPt.py
Author    : Esri Japan Corporation
Created   : 2018/12/14
Updated   : 2024/08/20
"""

class AlreadyExistError(Exception):
    pass


import arcpy
import sys
import os


# フィーチャクラスの作成と属性情報コピーの準備
def create_fieldinfo(in_line_fc, out_pt_fc):
    """
    メソッド名 : create_fieldinfo メソッド
    引数 1     : 入力フィーチャ
    引数 2     : 出力フィーチャクラス
    概要       : カーソル作成に用いるフィールド情報を作成
    """
    # 出力パスの取得
    out_ws = os.path.dirname(out_pt_fc)
    out_fc_name = os.path.basename(out_pt_fc)

    # 入力データの情報を取得
    in_fc_name = os.path.basename(in_line_fc)
    in_ws = os.path.dirname(in_line_fc)
    in_desc = arcpy.Describe(in_line_fc)
    in_fields = in_desc.Fields
    # ポリゴンから座標系を取得
    spref = in_desc.spatialReference

    # フィーチャクラスの作成
    arcpy.CreateFeatureclass_management(out_ws, out_fc_name, "POINT", in_line_fc, "", "", spref)

    # 変数定義
    search_fields_name = []
    search_fields_type = []
    del_fields = []
    use_fields = []

    # 属性情報コピーの準備
    for i, field in enumerate(in_fields):
        if (field.type == u"OID") or (field.type == u"Geometry"):
            pass
        # 出力が Shape ファイルの場合は、削除対象
        elif field.name.lower() == "shape_length" or field.name.lower() == "shape_area":
            del_fields.append(i)
        else:
            search_fields_name.append(field.name)
            search_fields_type.append(field.type)
            # 属性情報コピーの対象となるフィールドのインデックス番号を取得
            use_fields.append(i)
            
    out_fields = arcpy.ListFields(out_pt_fc)

    # 出力がShape ファイルの場合
    if arcpy.Describe(out_ws).workspacetype == "FileSystem":

        # 入力もShape ファイルの場合はスルー。
        # Shape_Length、Shape_Area フィールドは削除
        if arcpy.Describe(in_desc.path).workspacetype != "FileSystem":
            if len(del_fields) != 0:
                del_fields_name = [out_fields[index].name for index in del_fields]
                arcpy.DeleteField_management(out_pt_fc, del_fields_name)

        # 属性情報コピーの対象とするフィールド名のリストを作成
        # （インデックス番号を用いて Shape ファイルで短くなった名前を取得）
        use_fields_name = [out_fields[index].name for index in use_fields]
        use_fields_name.append("SHAPE@")

    # 出力が GDB の場合は、入力データと同じフィールド構造を使用
    else:
        use_fields_name = search_fields_name

    search_fields_name.append("SHAPE@")

    return search_fields_name, search_fields_type, use_fields_name, spref


def lineendpoint_point():
    """
    メソッド名 : lineendpoint_point メソッド
    概要       : ラインの終始点からポイントへ変換
    """
    try:
        arcpy.AddMessage(u"処理開始：")

        in_line_fc = arcpy.GetParameterAsText(0)
        out_pt_fc = arcpy.GetParameterAsText(1)
        out_type = arcpy.GetParameterAsText(2)

        # ワークスペース
        wstype = arcpy.Describe(os.path.dirname(out_pt_fc)).workspacetype

        # ワークスペースにすでに同一のフィーチャクラス名がないかチェック
        if arcpy.Exists(out_pt_fc):
            raise AlreadyExistError

        # カーソル作成に使用するフィールド情報を create_fieldinfo 関数を用いて取得
        search_fields_name, search_fields_type, use_fields_name, spref = create_fieldinfo(in_line_fc, out_pt_fc)

        # フィーチャクラスの検索カーソル作成
        incur = arcpy.da.SearchCursor(in_line_fc, search_fields_name)
        # フィーチャクラスの挿入カーソル作成
        outcur = arcpy.da.InsertCursor(out_pt_fc, use_fields_name)

        i = 0
        num = int(arcpy.GetCount_management(in_line_fc).getOutput(0))

        # フィーチャ(ジオメトリ)の数
        for inrow in incur:
            i = i + 1
            if (i == 1) or (i == num) or (i % 1000 == 1):
                s = u"{0}/{1}の処理中・・・".format(i, num)
                arcpy.AddMessage(s)

            newValue = []
            # 出力がShape ファイルの場合、NULL 値を格納できないため
            # フィールドのタイプに合わせて、空白や 0 を格納する
            if wstype == "FileSystem":
                for j, value in enumerate(inrow):
                    if value == None:
                        if search_fields_type[j] == "String":
                            newValue.append("")
                        elif search_fields_type[j] in ["Double", "Integer", "Single", "SmallInteger"]:
                            newValue.append(0)
                        else:
                            newValue.append(value)
                    else:
                        newValue.append(value)
            # GDB は NULL 値を格納可能
            else:
                newValue = list(inrow)

            # パートの数
            for part in inrow[-1]:
                if out_type == 'BOTH' or out_type == 'START':
                    # ジオメトリにラインの始点ポイントを格納
                    newValue[-1] = arcpy.PointGeometry(part[0], spref)
                    # リストからタプルに変換してインサート
                    outcur.insertRow(tuple(newValue))
                if out_type == 'BOTH' or out_type == 'END':
                    # ジオメトリにラインの終点ポイントを格納
                    newValue[-1] = arcpy.PointGeometry(part[part.count - 1], spref)
                    # リストからタプルに変換してインサート
                    outcur.insertRow(tuple(newValue))
        # 後始末
        del outcur
        del incur

        arcpy.AddMessage(u"処理終了：")
    except AlreadyExistError:
        arcpy.AddError(u"{0}はすでに存在しています".format(out_pt_fc))
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


if __name__ == "__main__":
    lineendpoint_point()
