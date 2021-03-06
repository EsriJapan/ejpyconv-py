﻿# coding:utf-8
"""
Tool name : ポイントをポリゴンへ変換
Source    : PtToPoly.py
Author    : Esri Japan Corporation
Created   : 2018/12/14
Updated   :
"""

class AlreadyExistError(Exception):
    pass


import arcpy
import sys
import os
from itertools import groupby


# フィーチャクラスの作成と属性情報コピーの準備
def create_fieldinfo(in_pt_fc, out_pt_fc, group_field_name, sort_field_name):
    """
    メソッド名 : create_fieldinfo メソッド
    引数 1     : 入力フィーチャ
    引数 2     : 出力フィーチャクラス
    引数 3     : グループフィールド
    引数 4     : 順序結合フィールド
    概要       : カーソル作成に用いるフィールド情報を作成
    """
    # 出力パスの取得
    out_dir = os.path.dirname(out_pt_fc)
    out_name = os.path.basename(out_pt_fc)

    # 入力データの情報を取得
    in_desc = arcpy.Describe(in_pt_fc)
    sr = in_desc.spatialReference
    shape_field = in_desc.ShapeFieldName
    oid_field = in_desc.OIDFieldName
    in_fields = in_desc.Fields

    # フィーチャクラスの作成
    arcpy.CreateFeatureclass_management(out_dir, out_name, "POLYGON", in_pt_fc, "", "", sr)

    # 変数定義
    search_fields_name = []
    search_fields_type = []
    del_fields = []
    use_fields = []
    sortindex = 0
    groupindex = 0
    indexcnt = 0

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
            
            # グループ化で使用するフィールドのインデックス番号を取得
            if field.name == group_field_name:
                groupindex = indexcnt

            # ソートで使用するフィールドのインデックス番号を取得
            if field.name == sort_field_name:
                sortindex = indexcnt

            indexcnt += 1


    out_fields = arcpy.ListFields(out_pt_fc)

    # 出力がShape ファイルの場合
    if arcpy.Describe(out_dir).workspacetype == "FileSystem":

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

    return search_fields_name, search_fields_type, use_fields_name, groupindex, sortindex


def point_polygon():
    """
    メソッド名 : point_polygon メソッド
    概要       : ポイントからポリゴンへ変換
    """
    try:
        in_pt_fc = arcpy.GetParameterAsText(0)
        out_pt_fc = arcpy.GetParameterAsText(1)
        group_field_name = arcpy.GetParameterAsText(2)
        sort_field_name = arcpy.GetParameterAsText(3)

        wstype = arcpy.Describe(os.path.dirname(out_pt_fc)).workspacetype

        # ワークスペースにすでに同一のフィーチャクラス名がないかチェック
        if wstype != "FileSystem":
            if arcpy.Exists(out_pt_fc):
                raise AlreadyExistError

        # カーソル作成に使用するフィールド情報を create_fieldinfo 関数を用いて取得
        search_fields_name, search_fields_type, use_fields_name, groupindex, sortindex = create_fieldinfo(in_pt_fc, out_pt_fc, group_field_name, sort_field_name)

        # フィーチャクラスの検索カーソル作成
        input_cur = arcpy.da.SearchCursor(in_pt_fc, search_fields_name)
        # フィーチャクラスの挿入カーソル作成
        output_cur = arcpy.da.InsertCursor(out_pt_fc, use_fields_name)

        # 処理件数表示用の変数
        i = 0        
        num = int(arcpy.GetCount_management(in_pt_fc).getOutput(0))

        # グループフィールドを指定しているか判定
        group_flg = True
        if (len(group_field_name) == 0):
            group_flg = False

        # ソートのフィールドが指定されている場合は指定フィールドでソートする
        if (len(sort_field_name) == 0):
            point_list = input_cur
        else:
            point_list = sorted(input_cur, key=lambda x: x[sortindex])

        # ジオメトリ作成処理
        if (group_flg == True):
            # 入力フィーチャのグループ分け
            for key, group in groupby(point_list, key=lambda x: x[groupindex]):

                group_list = list(group)
                geom = []

                for inrow in group_list:
                    i = i + 1 
                    if (i == 1) or (i == num) or (i % 1000 == 1):
                        s = u"{0}/{1}の処理中・・・".format(i, num)
                        arcpy.AddMessage(s)

                    newValue = []
                    # 出力がShape ファイルの場合、NULL 値を格納できないため
                    # フィールドのタイプに合わせて、空白や 0 を格納する
                    if wstype == "FileSystem":
                        for j, value in enumerate(inrow[:-1]):
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
                        newValue = list(inrow[:-1])

                    for pnt in inrow[-1]:
                        geom.append(pnt)

                # ジオメトリを格納
                newValue.append(arcpy.Polygon(arcpy.Array([coords for coords in geom])))
                # リストからタプルに変換してインサート
                output_cur.insertRow(tuple(newValue))
                del geom
        else:
            geom = []
            for inrow in point_list:
                i = i + 1 
                if (i == 1) or (i == num) or (i % 1000 == 1):
                    s = u"{0}/{1}の処理中・・・".format(i, num)
                    arcpy.AddMessage(s)

                newValue = []
                # 出力がShape ファイルの場合、NULL 値を格納できないため
                # フィールドのタイプに合わせて、空白や 0 を格納する
                if wstype == "FileSystem":
                    for j, value in enumerate(inrow[:-1]):
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
                    newValue = list(inrow[:-1])

                for pnt in inrow[-1]:
                    geom.append(pnt)

            # ジオメトリを格納
            newValue.append(arcpy.Polygon(arcpy.Array([coords for coords in geom])))
            # リストからタプルに変換してインサート
            output_cur.insertRow(tuple(newValue))
            del geom
            

        del input_cur
        del output_cur

        arcpy.AddMessage(u"処理終了：")

    except AlreadyExistError:
        arcpy.AddError(u"{0}に{1}はすでに存在しています".format(out_ws, out_fc_name))
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


if __name__ == "__main__":
    point_polygon()

