import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split

def load_and_preprocess_data(db_url: str):
    """データベースから物件データを読み込み、基本的な前処理を行う"""
    engine = create_engine(db_url)
    df = pd.read_sql("SELECT * FROM properties", engine)
    
    # 実質家賃の算出
    df['total_fee'] = (df['price'] + df['admin_fee'])*10000
    df = df[df['age'] > 0]


    # フィルタリング（部分一致）
    df = df[df['building_type'].str.contains('マンション|アパート', na=False)].copy()
    
    
    
    # 分析に必須なカラムの欠損値を削除
    required_cols = ['age', 'liv_area', 'station_distance', 'floor', 'total_fee']
    df = df.dropna(subset=required_cols)
    
    # 対数変換
    df['log_total_fee'] = np.log1p(df['total_fee'])
    df['log_liv_area'] = np.log1p(df['liv_area'])

    mean = df['log_total_fee'].mean()
    std = df['log_total_fee'].std()

    df = df[np.abs(df['log_total_fee'] - mean) <= 3 * std].copy()
    
    return df

def get_train_val_test_split(df: pd.DataFrame):
    """データを学習用(60%)、検証用(20%)、テスト用(20%)に分割する"""
    train_df, temp_df = train_test_split(df, test_size=0.4, random_state=42)
    val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)
    return train_df, val_df, test_df