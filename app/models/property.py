from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)        # 物件名
    address = Column(String)                      # 住所
    price = Column(Float)                         # 価格（万円）
    liv_area = Column(Float)                      # 専有面積（m2）
    age = Column(Integer)                         # 築年数
    station_distance = Column(Integer)            # 最寄り駅からの徒歩分
    floor_plan = Column(String)                   # 間取り（1K, 2LDKなど）
    admin_fee = Column(Float)                     #管理費
    floor = Column(Integer)                       #階数
    building_type = Column(String)                #マンション・アパート・戸建てなど
    # 統計・AI用（理論価格と乖離率）
    estimated_price = Column(Float, nullable=True) # 重回帰で算出した理論価格
    divergence_rate = Column(Float, nullable=True) # 乖離率（（理論-実際）/理論）
    monthly_fee = Column(Float,nullable=True)      #家賃+管理費
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())