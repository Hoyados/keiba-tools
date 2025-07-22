import pandas as pd
import argparse
import time
from logging import getLogger, StreamHandler, FileHandler, Formatter, INFO, ERROR

import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import matplotlib.colors as mcolors
plt.rcParams["font.family"] = "Hiragino Sans"

# ログ作成用のおまじない
logger = getLogger(__name__)
logger.setLevel(INFO)

console_handler = StreamHandler()
console_handler.setLevel(ERROR)
console_handler.setFormatter(Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

file_handler = FileHandler("output/log.txt", encoding = "utf-8")
file_handler.setLevel(INFO)
file_handler.setFormatter(Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.propagate = False

start_time = time.perf_counter()
logger.info ("処理開始")

# CLI用引数作成
parser = argparse.ArgumentParser(description = "競馬結果分析")
parser.add_argument("-f", "--filename", type = str, default = "競馬-結果リスト")
args = parser.parse_args()

# ファイル読み込み関数
def fileload():
    try:
        df = pd.read_csv("data/" + args.filename + ".csv")
        logger.info(f"読み込みファイル: data/{args.filename}.csv")
        return df
    except:
        logger.error("ファイルがありません")
        exit()

def cleandata(df):
    """
    データのクリーニングを行う関数。
        - 欠損が多すぎる行の削除
        - 金額、倍率の整形、型変換（倍率データなしを-1.0倍にする）
        - 馬券種別の表記揺れ修正
        - 収支差列を作成
    引数: dataframe（元データ）
    戻り値: dataframe（クリーン済みデータ）
    """
    df = df.copy()
    df = df[df.isna().sum(axis = 1) < 7]
    df["購入金額"] = df["購入金額"].replace("[¥,]", "", regex = True).astype(int)
    df["払い戻し"] = df["払い戻し"].replace("[¥,]", "", regex = True).astype(int)
    df["倍率"] = df["倍率"].replace("[――—]", None, regex = True).astype(float)
    df["倍率"] = df["倍率"].fillna(-1.0)
    df["馬券種別"] = df["馬券種別"].replace("[ ]", "", regex = True)
    df["馬券種別"] = df["馬券種別"].replace("[3 ３]", "三", regex = True)
    df["収支差"] = df["払い戻し"] - df["購入金額"]
    return df

def add_feature(df):
    """
    データに特徴量を追加する
    - 日付を月単位分類
    - 倍率を1倍区切りで分類
    - 回収率を追加
    """
    df["日付"] = df["日付"].astype(str).str.strip()
    df["日付"] = pd.to_datetime(df["日付"])
    df["月"] = df["日付"].dt.to_period("M")

    df["倍率帯"] = pd.cut(df["倍率"], bins=[0, 4, 8, 12, 100], labels=["1〜4倍", "4〜8倍", "8〜12倍", "12倍以上"])

    return df

def summarize_by (df, key_col, target_col, agg_func, sort = True):
    """
    汎用集計関数
    引数: 
    - dataframe(クリーン済み)
    - 集計軸
    - 集計対象
    - 集計方式（平均mean, 総和sumなど）
    """
    summary = df.groupby(key_col)[target_col].agg(agg_func)
    if sort:
        summary = summary.sort_index()
    return summary

def heatmap_data (df, index, columns, values, aggfunc = "count"):
    """
    ピボットテーブルにより、ヒートマップ用dfを作成する
    引数
    - index: 縦
    - columns: 横
    - values: 値
    - aggfunc: 関数（平均mean、総和sum、回数countなど）
    """
    pivot_data = df.pivot_table(index = index, columns = columns, values = values, aggfunc = aggfunc, observed = False)
    return pivot_data

# 2軸グラフ描画関数
def plotgraph (temp1, temp2, xlabel, y1label, y2label):

    fig, ax1 = plt.subplots()

# 左Y軸
    ax1.bar(temp1.index.astype(str), temp1, label = y1label, color = "blue")
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(y1label, color = "blue")
    ax1.tick_params(axis="y")

# 右Y軸
    ax2 = ax1.twinx()
    ax2.plot(temp2.index.astype(str), temp2, marker="o", label = y2label, color = "red")
    ax2.set_ylabel(y2label, color = "red")
    ax2.tick_params(axis="y")

# タイトルとレイアウト
    plt.title(xlabel + "ごとの" + y1label + "と" + y2label)
    fig.tight_layout()
    plt.savefig("output/" + xlabel +".png")

# 棒グラフ描画関数
def bargraph (temp1):
    fig, ax = plt.subplots()
    ax.bar(temp1.index.astype(str), temp1.values)
    xlabel = "月毎の結果"
    plt.savefig("output/" + xlabel +".png")

# ヒートマップ描画関数
def heatmapgraph (pivot_table, label1, label2, value, max = 100, min = 0):
    fig, ax = plt.subplots(figsize = (8, 8))
    sns.heatmap(pivot_table, annot = True, cmap = "coolwarm", ax = ax, fmt = ".0f", square = True, vmax = max, vmin = min)
    plt.title(f"{label1}と{label2}による{value}ヒートマップ")
    fig.tight_layout()
    plt.savefig(f"output/{label1}x{label2}_{value}.png")

def main():
    df = fileload()
    df = cleandata(df)
    df = add_feature(df)
    df.to_csv("output/cleaned-keibadata.csv", index = False)
    df = df[df["日付"] > "2025-05-31"]
    hitrate = summarize_by(df, "馬券種別", "的中", "mean", False) * 100
    returnrate = summarize_by(df, "馬券種別", "収支差", "sum", False)
    plotgraph (hitrate, returnrate, "馬券種別", "的中率(%)", "収支差(円)")
    hitrate = summarize_by(df, "倍率帯", "的中", "mean", False) * 100
    returnrate = summarize_by(df, "倍率帯", "収支差", "sum", False)
    plotgraph (hitrate, returnrate, "倍率帯", "的中率(%)", "収支差(円)")
    hitrate = summarize_by(df, "月", "的中", "mean", True) * 100
    returnrate = summarize_by(df, "月", "収支差", "sum", True)
    plotgraph (hitrate, returnrate, "月", "的中率(%)", "収支差(円)")
    pivot_table = heatmap_data(df, "馬券種別", "倍率帯", "収支差", "sum")
    heatmapgraph (pivot_table, "馬券種別", "倍率帯", "収支", 1200, -1200)
    pivot_table = heatmap_data(df, "馬券種別", "倍率帯", "的中", "mean") * 100
    heatmapgraph (pivot_table, "馬券種別", "倍率帯", "的中率", 100, 0)
    pivot_table = heatmap_data(df, "馬券種別", "倍率帯", "的中", "count")
    heatmapgraph (pivot_table, "馬券種別", "倍率帯", "購入回数", 30, 0)
    pivot_table = heatmap_data(df, "馬券種別", "倍率帯", "的中", "sum")
    heatmapgraph (pivot_table, "馬券種別", "倍率帯", "的中回数", 30, 0)
    returnmoney = heatmap_data(df, "馬券種別", "倍率帯", "払い戻し", "sum")
    buymoney = heatmap_data(df, "馬券種別", "倍率帯", "購入金額", "sum")
    counts = heatmap_data(df, "馬券種別", "倍率帯", "的中", "count")
    pivot_table = returnmoney / buymoney * 100
    heatmapgraph (pivot_table, "馬券種別", "倍率帯", "回収率", 300, 0)
    pivot_table = (returnmoney - buymoney) / counts
    heatmapgraph (pivot_table, "馬券種別", "倍率帯", "一回あたりの収支", 300, -300)

if __name__ == "__main__":
    main()
    end_time = time.perf_counter()
    logger.info(f"処理終了: {round(end_time - start_time, 2)}秒")