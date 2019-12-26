# coding:utf-8
"""
Tool name : スパイダーグラフの作成
Source    : SpiderGraph.py
Author    : Esri Japan Corporation
Created   : 2019/12/26
Updated   :
"""

import sys
import os
import arcpy


class AlreadyExistError(Exception):
    pass

class FeatureCountError(Exception):
    pass


#スパイダーグラフに用いる入力情報の作成
    
IN_PT_FC = arcpy.GetParameterAsText(0)
REF_PT_FC = arcpy.GetParameterAsText(1)
OUT_LINE_FC = arcpy.GetParameterAsText(2)
LIMIT = 10000

def check():

    # 同一のフィーチャクラス名がないかチェック
    if arcpy.Exists(OUT_LINE_FC):
        raise AlreadyExistError

    # 入力ポイントの数が10000件以上の場合メッセージを出す
    count = int(arcpy.GetCount_management(IN_PT_FC).getOutput(0))
    if count > LIMIT:
        raise FeatureCountError

    return count

def spider_graph():
    """
    メソッド名： spider_graph メソッド
    引数 1    : 入力ポイント
    引数 2    : 参照ポイント
    引数 4    : 出力フィーチャクラス
    概要　　　： スパイダーグラフの作成
    """
    try:
        arcpy.AddMessage("処理開始：")
        
        # 同一フィーチャクラス名、入力フィーチャ数のチェック
        count = check()
    
        # 出力フィーチャクラスの作成
        arcpy.CreateFeatureclass_management(os.path.dirname(OUT_LINE_FC), os.path.basename(OUT_LINE_FC), "POLYLINE", "", "", "", arcpy.Describe(IN_PT_FC).spatialReference)

        # 入力ポイントのOIDを始点ID、参照ポイントのOIDを終点IDとしてフィールドの追加
        arcpy.AddField_management(OUT_LINE_FC, "始点ID" , "LONG")
        arcpy.AddField_management(OUT_LINE_FC, "終点ID" , "LONG")

        # スパイダーグラフの作成
        with arcpy.da.InsertCursor(OUT_LINE_FC, ["SHAPE@", "始点ID", "終点ID"]) as outcur:
            with arcpy.da.SearchCursor(IN_PT_FC, ["OID@", "SHAPE@"]) as incur:
                # 入力ポイント分繰り返し
                for n, inrow in enumerate(incur, start=1):   
                    arcpy.AddMessage("{0}/{1}の処理中・・・".format(n, count)) 
                    
                    with arcpy.da.SearchCursor(REF_PT_FC, ["OID@","SHAPE@"]) as refcur:
                        newvalue_list = None
                        # 参照ポイント分繰り返し
                        for refrow in refcur:
                            #入力と参照ポイントの距離
                            distance = inrow[-1].distanceTo(refrow[-1])                         

                            # newvalue_list に値が入っていない、または距離が小さい場合に値を格納
                            if newvalue_list is None or distance < newvalue_list[-1]:
                                newvalue_list = [inrow, refrow, distance]
                         
                        # 出力するラインがない(参照ポイントが空)場合、処理終了
                        if newvalue_list == None:
                            break
                        # 入力ポイントと参照ポイントの距離が０でない場合、ラインを作成
                        elif newvalue_list[-1] != 0:
                            in_point = newvalue_list[0][-1].centroid
                            ref_point = newvalue_list[1][-1].centroid
                            out_line = arcpy.Polyline(arcpy.Array([in_point, ref_point]))
                            # 作成したラインと入力ポイント・参照ポイントのOIDを出力
                            outcur.insertRow((out_line, newvalue_list[0][0], newvalue_list[1][0]))

        
        arcpy.AddMessage("処理終了：")
    except AlreadyExistError:
        arcpy.AddError("{0}はすでに存在しています".format(OUT_LINE_FC))
    except FeatureCountError:
        arcpy.AddError("処理の対象件数が上限{0}件を超えています。".format(LIMIT))
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError(e.args[0])


if __name__ == u'__main__':
    spider_graph()