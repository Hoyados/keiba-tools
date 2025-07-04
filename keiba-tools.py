import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.colors as mcolors
plt.rcParams["font.family"] = "Hiragino Sans"

# ファイル読み込み関数
def fileload():
    filename = input("ファイル名を入力して下さい（拡張子不要、csvファイルのみ）") or "競馬-結果リスト"
    try:
        df = pd.read_csv("data/" + filename + ".csv")
        return df
    except:
        print("ファイルがありません")
        exit()
# df = pd.read_csv("競馬-結果リスト.csv") # テスト用

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
    df = df[df.isna().sum(axis = 1) < 7]
    df["購入金額"] = df["購入金額"].replace("[¥,]", "", regex = True).astype(int)
    df["払い戻し"] = df["払い戻し"].replace("[¥,]", "", regex = True).astype(int)
    df["倍率"] = df["倍率"].replace("[――—]", None, regex = True).astype(float)
    df["倍率"].fillna(-1.0, inplace = True)
    df["馬券種別"] = df["馬券種別"].replace("[ ]", "", regex = True)
    df["馬券種別"] = df["馬券種別"].replace("[3 ３]", "三", regex = True)
    df["収支差"] = df["払い戻し"] - df["購入金額"]
    return df

def hitreturnrate(df):
    """
    馬券種別毎の的中率と平均収支を求める関数。
    引数: dataframe（クリーン済みデータ）
    戻り値: hitrate（的中率）、returnrate（平均収支）
    """
    hitrate = df.groupby("馬券種別")["的中"].mean().round(3) * 100
    returnrate = df.groupby("馬券種別")["収支差"].mean().round(1)
    return hitrate, returnrate

def oddsreturnrate(df):
    """
    倍率別の的中率と平均収支を求める関数。-1.0倍はデータなし扱いとして除外する。
    引数: dataframe（クリーン済みデータ）
    戻り値: hitbyodds（的中率）、returnbyodds（平均収支）
    """
    valid_df = df[df["倍率"] != -1.0].copy()
    bins = [0, 3, 8, float("inf")]
    labels = ["1~3倍", "3~8倍", "8倍以上"]
    valid_df["倍率区分け"] = pd.cut(valid_df["倍率"], bins = bins, labels = labels, right = False)
    hitbyodds = valid_df.groupby("倍率区分け")["的中"].mean().round(3) * 100
    returnbyodds = valid_df.groupby("倍率区分け")["収支差"].mean().round(1)
    return hitbyodds, returnbyodds

# 2軸グラフ描画関数
def plotgraph (temp1, temp2, xlabel, y1label, y2label):

    fig, ax1 = plt.subplots()

# 左Y軸
    yonecolor = input(y1label + "軸の色を英語入力（未入力または無効の場合は水色になります）") or "skyblue"
    if yonecolor not in mcolors.CSS4_COLORS:
        yonecolor = "skyblue"
        print ("色が存在しないため、水色にします")
    ax1.bar(temp1.index, temp1, color = yonecolor, label = y1label)
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(y1label, color = yonecolor)
    ax1.tick_params(axis="y", labelcolor = yonecolor)

# 右Y軸
    ytwocolor = input(y2label + "軸の色を英語入力（未入力または無効の場合は橙色になります）") or "orange"
    if ytwocolor not in mcolors.CSS4_COLORS:
        ytwocolor = "orange"
        print ("色が存在しないため、橙色にします")
    ax2 = ax1.twinx()
    ax2.plot(temp2.index, temp2, color = ytwocolor, marker="o", label = y2label)
    ax2.set_ylabel(y2label, color = ytwocolor)
    ax2.tick_params(axis="y", labelcolor = ytwocolor)

# タイトルとレイアウト
    plt.title(xlabel + "ごとの" + y1label + "と" + y2label)
    fig.tight_layout()
    plt.savefig("output/" + xlabel +".png")

def main():
    df = fileload()
    df = cleandata(df)
    df.to_csv("output/cleaned-keibadata.csv", index = False)
    hitrate, returnrate = hitreturnrate(df)
    plotgraph (hitrate, returnrate, "馬券種別", "的中率(%)", "収支差(円)")
    hitbyodds, returnbyodds = oddsreturnrate(df)
    plotgraph (hitbyodds, returnbyodds, "倍率", "的中率(%)", "収支差(円)")

if __name__ == "__main__":
    main()