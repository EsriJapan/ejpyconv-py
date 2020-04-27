# coding:utf-8
"""
Tool name : ポイントでラインを分断
Source    : SplitLineAtPt.py
Author    : Esri Japan Corporation
Created   : 2019/6/21
Updated   : 2020/4/27
"""

class AlreadyExistError(Exception):
    pass


import arcpy
import sys
import os
sys.setrecursionlimit(10000)

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
    arcpy.CreateFeatureclass_management(out_ws, out_fc_name, "POLYLINE", in_line_fc, "", "", spref)

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


def cut_line(line, point):
    """
    メソッド名 : cut_line メソッド
    概要　 　　: ポイントでラインを分断
    """

    cutline1, cutline2 = line.cut(arcpy.Polyline(arcpy.Array(
        [arcpy.Point(point.centroid.X + 0.01, point.centroid.Y + 0.01),
         arcpy.Point(point.centroid.X - 0.01, point.centroid.Y - 0.01)])))

    return cutline1, cutline2


def recut_line(cutlines, overlap_pt, end, error_list):
    """
    メソッド名 : recut_line メソッド
    概要　 　　: ポイントでラインを分断(再帰処理)
    """
    # ラインの数ループ
    for line in cutlines:
        # ポイントの数ループ
        for point in overlap_pt:
            # ポイントが重なっているかチェック
            if line.contains(point[0][0]):
                cutline1, cutline2 = cut_line(line, point[0][0])
                # カットしたラインを配列に格納
                cutlineArray = []
                cutlineArray.insert(0, cutline2)
                cutlineArray.insert(0, cutline1)
                
                # カットに使用したポイントは削除
                overlap_pt.remove(point)
                
                # ポイントがなくなったら最後に切れたラインを最終系の配列に入れる
                if len(overlap_pt) == 0:
                    end.insert(-1, cutline2)
                    end.insert(-1, cutline1)
                # カットできなかったらポイントのOIDを格納
                if cutline1.length == 0 or cutline2.length == 0:
                     error_list.append(point[-1])
                # カットしたラインにさらに重なるポイントがあるか再帰処理
                recut_line(cutlineArray, overlap_pt, end, error_list)

            # ラインにポイントが重なっていなかったら他のポイントと重なっているかチェック
            else:
                flg = False
                for point2 in overlap_pt:
                    if line.contains(point2[0][0]):
                        flg = True

                # 他のポイントとも重なっていなかったら最終系のラインの配列に入れる
                if flg == False and line.length != 0:
                    end.insert(-1, line)       

    return end, error_list


def split_line_pt():
    """
    メソッド名 : SplitLineAtPoint メソッド
    概要       : ポイントでラインを分断
    """
    try:
        arcpy.AddMessage(u"処理開始：")

        in_line_fc = arcpy.GetParameterAsText(0)
        in_point_fc = arcpy.GetParameterAsText(1)
        out_pt_fc = arcpy.GetParameterAsText(2)


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

        for inrow in incur:

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

            cutlines = []
            cutlines.insert(0, newValue[-1])

            # 入力ポイントのリストを作成
            points = [row for row in arcpy.da.SearchCursor(in_point_fc, ["SHAPE@", "OID@"])]

            # ラインと重なっているポイントのみを配列に入れる
            overlap_pt = []
            for pt in points:
                if newValue[-1].contains(pt[0]):
                    a = newValue[-1].queryPointAndDistance(pt[0])
                    overlap_pt.append([a, pt[-1]])
            # ラインの始点から近い順に並べかえ
            overlap_pt.sort(key = lambda x: x[0][1])

            # cutできなかったポイントのOID格納用リスト
            error_list = []
            # ラインと重なっているポイントが0個の場合
            if len(overlap_pt) == 0:
                # 入力ラインをそのまま出力
                outcur.insertRow(newValue)
            # ラインと重なっているポイントが1個の場合 cut_line メソッドへ
            elif len(overlap_pt) == 1:
                cutline1, cutline2 = cut_line(newValue[-1], overlap_pt[0][0][0])
                
                # カットできなかったらポイントのOIDを格納
                if cutline1.length == 0 or cutline2.length == 0:
                     error_list.append(overlap_pt[0][-1]) 
                else:
                    newValue[-1] = cutline1
                    outcur.insertRow(newValue)
                    newValue[-1] = cutline2
                    outcur.insertRow(newValue)

            # ラインと重なっているポイントが2個以上の場合、再帰処理の recut_line メソッドへ
            else:
                end = []
                # ラインに対して再帰的にポイントでカットする
                end = recut_line(cutlines, overlap_pt, end, error_list)
                # 最終系のラインの配列から重複しているラインを削除
                unique_end = []
                for overlap_line in end[0]:
                    if overlap_line not in unique_end:
                        unique_end.append(overlap_line)
                # 最終系のラインの配列分繰り返して newValue に値を入れる
                for out_line in unique_end:
                    newValue[-1] = out_line
                    outcur.insertRow(newValue)

        # 後始末
        del outcur
        del incur

        if len(error_list) != 0:
            for error in error_list:
                arcpy.AddMessage(u"入力ポイント:{0}の OBJECTID:{1} のポイントでの分断に失敗しました。"
                                 u"手動で分断してください。".format(os.path.basename(in_point_fc), error))

        arcpy.AddMessage(u"処理終了：")
    except AlreadyExistError:
        arcpy.AddError(u"{0}はすでに存在しています".format(out_pt_fc))
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


if __name__ == "__main__":
    split_line_pt()
