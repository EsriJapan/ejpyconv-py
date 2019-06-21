# coding:utf-8
"""
Tool name : ラインでポリゴンを分断
Source    : CutPolyWithLine.py
Author    : Esri Japan Corporation
Created   : 2019/6/21
Updated   :
"""

class AlreadyExistError(Exception):
    pass


import arcpy
import sys
import os


# フィーチャクラスの作成と属性情報コピーの準備
def create_fieldinfo(in_poly_fc, out_poly_fc):
    """
    メソッド名 : create_fieldinfo メソッド
    引数 1     : 入力フィーチャ
    引数 2     : 出力フィーチャ
    概要       : カーソル作成に用いるフィールド情報を作成
    """
    # 出力パスの取得
    out_ws = os.path.dirname(out_poly_fc)
    out_fc_name = os.path.basename(out_poly_fc)

    # 入力データの情報を取得
    in_fc_name = os.path.basename(in_poly_fc)
    in_ws = os.path.dirname(in_poly_fc)
    in_desc = arcpy.Describe(in_poly_fc)
    in_fields = in_desc.Fields
    # ポリゴンから座標系を取得
    spref = in_desc.spatialReference

    # フィーチャクラスの作成
    arcpy.CreateFeatureclass_management(out_ws, out_fc_name, "POLYGON", in_poly_fc, "", "", spref)

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
            
    out_fields = arcpy.ListFields(out_poly_fc)

    # 出力がShape ファイルの場合
    if arcpy.Describe(out_ws).workspacetype == "FileSystem":

        # 入力もShape ファイルの場合はスルー。
        # Shape_Length、Shape_Area フィールドは削除
        if arcpy.Describe(in_desc.path).workspacetype != "FileSystem":
            if len(del_fields) != 0:
                del_fields_name = [out_fields[index].name for index in del_fields]
                arcpy.DeleteField_management(out_poly_fc, del_fields_name)

        # 属性情報コピーの対象とするフィールド名のリストを作成
        # （インデックス番号を用いて Shape ファイルで短くなった名前を取得）
        use_fields_name = [out_fields[index].name for index in use_fields]
        use_fields_name.append("SHAPE@")

    # 出力が GDB の場合は、入力データと同じフィールド構造を使用
    else:
        use_fields_name = search_fields_name

    search_fields_name.append("SHAPE@")

    return search_fields_name, search_fields_type, use_fields_name, spref


def recut(cutpoly, crossline, end):
    """
    メソッド名 : recut メソッド
    概要 　　　: ポリゴンをラインで切断（再帰処理）
    """
    # ポリゴンの数ループ
    for polygon in cutpoly:
        # ラインの数ループ
        for line in crossline:
            # ラインが重なっているかチェック
            if polygon.crosses(line):
                # 重なっていたらカット
                cutpoly1, cutpoly2 = polygon.cut(line)
                # カットしたポリゴンを配列に入れる
                cutpolyArray = []
                cutpolyArray.append(cutpoly1)
                cutpolyArray.append(cutpoly2)
                # カットしたポリゴンにさらに重なるラインがあるか再帰
                recut(cutpolyArray, crossline, end)

            # ラインが重なっていなかったら他のラインと重なっているかチェック
            else:
                flg = False
                for another_line in crossline:
                    if polygon.crosses(another_line):
                        flg = True

                # 他のラインとも重なっていなかったら最終系のポリゴンの配列に格納
                if flg == False:
                    end.append(polygon)
    return end


def cut_polygon():
    """
    メソッド名 : cut_polygon メソッド
    概要       : ポリゴンをラインで切断
    """
    try:
        arcpy.AddMessage(u"処理開始：")

        in_poly_fc = arcpy.GetParameterAsText(0)
        in_line_fc = arcpy.GetParameterAsText(1)
        out_poly_fc = arcpy.GetParameterAsText(2)

        # ワークスペース
        wstype = arcpy.Describe(os.path.dirname(out_poly_fc)).workspacetype

        # ワークスペースにすでに同一のフィーチャクラス名がないかチェック
        if arcpy.Exists(out_poly_fc):
            raise AlreadyExistError

        # カーソル作成に使用するフィールド情報を create_fieldinfo 関数を用いて取得
        search_fields_name, search_fields_type, use_fields_name, spref = create_fieldinfo(in_poly_fc, out_poly_fc)

        # フィーチャクラスの検索カーソル作成
        incur = arcpy.da.SearchCursor(in_poly_fc, search_fields_name)
        # フィーチャクラスの挿入カーソル作成
        outcur = arcpy.da.InsertCursor(out_poly_fc, use_fields_name)

        i = 0
        num = int(arcpy.GetCount_management(in_poly_fc).getOutput(0))

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

            cutpoly = []
            cutpoly.insert(0, newValue[-1])

            # 入力ラインのリストを作成
            lines = [row[0] for row in arcpy.da.SearchCursor(in_line_fc, "SHAPE@")]
            # ポリゴンと重なっているラインのみを配列に入れる
            crossline = []
            for line in lines:
                if newValue[-1].crosses(line):
                    crossline.append(line)

            # ポリゴンと重なっているラインが0個の場合
            if len(crossline) == 0:
                # 入力ポリゴンをそのまま出力
                outcur.insertRow(tuple(newValue))
            # ポリゴンと重なっているラインが1個の場合
            elif len(crossline) == 1:
                cutpoly1, cutpoly2 = newValue[-1].cut(crossline[0])
                newValue[-1] = cutpoly1
                # リストからタプルに変換してインサート
                outcur.insertRow(tuple(newValue))
                newValue[-1] = cutpoly2
                # リストからタプルに変換してインサート
                outcur.insertRow(tuple(newValue))
            # ポリゴンと重なっているラインが2個以上の場合
            else:
                end = []
                end = recut(cutpoly, crossline, end)

                # 最終系のポリゴンの配列から重複ポリゴンを削除
                unique_end = []
                for overlap_poly in end:
                    if overlap_poly not in unique_end:
                        unique_end.append(overlap_poly)

                for new_poly in unique_end:
                    newValue[-1] = new_poly
                    outcur.insertRow(tuple(newValue))

        # 後始末
        del outcur
        del incur

        arcpy.AddMessage(u"処理終了：")
    except AlreadyExistError:
        arcpy.AddError(u"{0}はすでに存在しています".format(out_poly_fc))
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


if __name__ == "__main__":
    cut_polygon()
