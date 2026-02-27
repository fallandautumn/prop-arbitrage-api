from sqlalchemy.orm import Session
from app.models.property import Property
from app.schemas.property import PropertyCreate
from typing import List

def create_property(db: Session, property_in: PropertyCreate):
    # Pydanticモデルを辞書に変換してSQLAlchemyモデルを作成
    db_property = Property(**property_in.model_dump())
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property

def get_properties(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Property).offset(skip).limit(limit).all()

def create_properties_bulk(db: Session, properties_in: List[PropertyCreate]):
    # PydanticモデルのリストをSQLAlchemyモデルのリストに一括変換
    db_properties = [Property(**p.model_dump()) for p in properties_in]
    
    db.add_all(db_properties) # 一括追加
    db.commit() # 1回の通信でまとめて確定
    
    # 追加された後のデータをリフレッシュ（IDなどが付与される）
    for p in db_properties:
        db.refresh(p)
    return db_properties