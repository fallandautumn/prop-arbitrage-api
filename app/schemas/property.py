from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# 共通の物件データ定義
class PropertyBase(BaseModel):
    title: str
    address: str
    building_type: str = Field(..., description="建物種別（マンション、アパート等）")
    price: float = Field(..., description="賃料（万円）")
    admin_fee: float = Field(default=0.0, description="管理費（万円）") # デフォルトを0.0に設定
    liv_area: float = Field(..., description="専有面積（m2）")
    age: int = Field(..., description="築年数（年）")
    station_distance: int = Field(..., description="駅徒歩（分）")
    floor: int = Field(default=1, description="所在階") # 1階をデフォルトに
    floor_plan: str

# スクレイピング時に作成するためのスキーマ
class PropertyCreate(PropertyBase):
    pass

# APIから返却する時のスキーマ（IDや日付を含む）
class PropertyRead(PropertyBase):
    id: int
    monthly_fee: Optional[float] = Field(None, description="賃料+管理費の合計")
    estimated_price: Optional[float] = None
    divergence_rate: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True # SQLAlchemyのモデルをPydanticに変換可能にする