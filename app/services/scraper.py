import logging
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from app.schemas.property import PropertyCreate

logger = logging.getLogger(__name__)

class SuumoScraper:
    def __init__(self):
        self.base_url = "https://suumo.jp/chintai/tokyo/sc_shinjuku/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }

    def _extract_text(self, element, selector, default="") -> str:
        found = element.select_one(selector)
        return found.text.strip() if found else default

    def fetch_page(self, page: int = 1) -> list[PropertyCreate]:
        params = {"pn": page} 
        try:
            res = requests.get(self.base_url, headers=self.headers, params=params, timeout=15)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
        except Exception as e:
            logger.error(f"Page {page} fetch failed: {e}")
            return []

        properties = []
        cassettes = soup.select(".cassetteitem")
        
        for cassette in cassettes:
            title = self._extract_text(cassette, ".cassetteitem_content-title")
            address = self._extract_text(cassette, ".cassetteitem_detail-col1")
            age_str = self._extract_text(cassette, ".cassetteitem_detail-col3 div:nth-child(1)")
            walk_text = self._extract_text(cassette, ".cassetteitem_detail-col2 .cassetteitem_detail-text")
            b_type = self._extract_text(cassette, ".ui-pct--util1") # 種別ラベルのセレクタ
            
            # 部屋リストの行を取得
            rooms = cassette.select(".cassetteitem_other tbody tr") 
            
            for room in rooms:
                try:
                    # 数値抽出（賃料、面積、管理費、階数）
                    price_val = self._clean_numeric(self._extract_text(room, ".cassetteitem_other-emphasis"))
                    admin_fee_val = self._clean_numeric(self._extract_text(room, ".cassetteitem_price--administration")) / 10000  # 円を万円に変換
                    liv_area_val = self._clean_numeric(self._extract_text(room, ".cassetteitem_menseki"))
                    floor_val = self._parse_floor(self._extract_text(room, "td:nth-child(3)")) # 3番目のtdが階数

                    properties.append(PropertyCreate(
                        title=title,
                        address=address,
                        price=price_val,
                        admin_fee=admin_fee_val, 
                        liv_area=liv_area_val,
                        age=self._parse_age(age_str),
                        station_distance=self._parse_walk_time(walk_text),
                        floor=floor_val, 
                        floor_plan=self._extract_text(room, ".cassetteitem_madori"),
                        building_type=b_type
                    ))
                except Exception as e:
                    logger.warning(f"Room parse failed in '{title}': {e}")
                    continue
        
        logger.info(f"Page {page}: {len(properties)} properties extracted.")
        return properties

    def _clean_numeric(self, text: str) -> float:
        """数値だけを抽出（'15.5万円' -> 15.5, '15000円' -> 15000.0）"""
        if not text or text == "-" or "別" in text: return 0.0
        match = re.search(r"(\d+\.?\d*)", text.replace(",", ""))
        return float(match.group(1)) if match else 0.0

    def _parse_floor(self, text: str) -> int:
        """'1-2階' -> 1, 'B1階' -> -1, 'B1-2階' -> -1 への変換"""
        if not text or text == "-": return 1
        
        # 範囲指定（1-2階など）の場合、最初の数字を抽出
        first_part = text.split('-')[0]
        
        match = re.search(r"(\d+)", first_part)
        val = int(match.group(1)) if match else 1
        
        # 地下判定
        if "B" in first_part or "地下" in first_part:
            return -val
        return val

    def _parse_walk_time(self, text: str) -> int:
        match = re.search(r"(\d+)分", text)
        return int(match.group(1)) if match else 0

    def _parse_age(self, text: str) -> int:
        if "新築" in text or "0年" in text: return 0
        match = re.search(r"(\d+)年", text)
        return int(match.group(1)) if match else 0

