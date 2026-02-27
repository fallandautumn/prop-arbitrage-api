import logging
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from app.schemas.property import PropertyCreate

logger = logging.getLogger(__name__)

class SuumoScraperV2:
    def __init__(self):
        # 新宿区の賃貸マンション・アパートに絞ったURL
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
            # --- 建物共通情報の取得 ---
            title = self._extract_text(cassette, ".cassetteitem_content-title")
            address = self._extract_text(cassette, ".cassetteitem_detail-col1")
            age_str = self._extract_text(cassette, ".cassetteitem_detail-col3 div:nth-child(1)")
            walk_text = self._extract_text(cassette, ".cassetteitem_detail-col2 .cassetteitem_detail-text")
            b_type = self._extract_text(cassette, ".ui-pct--util1")
            
            # --- 【ここが肝】ループを回さず、最初の1部屋(select_one)だけを取得する ---
            room = cassette.select_one(".cassetteitem_other tbody tr") 
            
            if room:
                try:
                    # 数値抽出（賃料、面積、管理費、階数）
                    price_val = self._clean_numeric(self._extract_text(room, ".cassetteitem_other-emphasis"))
                    admin_fee_val = self._clean_numeric(self._extract_text(room, ".cassetteitem_price--administration")) / 10000
                    liv_area_val = self._clean_numeric(self._extract_text(room, ".cassetteitem_menseki"))
                    floor_val = self._parse_floor(self._extract_text(room, "td:nth-child(3)"))

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
            
            # 部屋のループがないため、1つの建物(cassette)につき1回しかappendされません。
        
        logger.info(f"Page {page}: {len(properties)} buildings extracted (1 room each).")
        return properties

    def _clean_numeric(self, text: str) -> float:
        if not text or text == "-" or "別" in text: return 0.0
        match = re.search(r"(\d+\.?\d*)", text.replace(",", ""))
        return float(match.group(1)) if match else 0.0

    def _parse_floor(self, text: str) -> int:
        """階数の文字列を数値に変換する（失敗時は1を返す）"""
        if not text or text.strip() == "" or text == "-":
            return 1  # 取れない場合は1階とみなす
        
        try:
            # 範囲指定（1-2階など）の場合、最初の数字を抽出
            first_part = text.split('-')[0]
            
            # 数値だけを抜き出す
            match = re.search(r"(\d+)", first_part)
            if match:
                val = int(match.group(1))
                # 地下判定
                if "B" in first_part or "地下" in first_part:
                    return -val
                return val
            return 1
        except Exception:
            return 1


    def _parse_walk_time(self, text: str) -> int:
        match = re.search(r"(\d+)分", text)
        return int(match.group(1)) if match else 0

    def _parse_age(self, text: str) -> int:
        if "新築" in text or "0年" in text: return 0
        match = re.search(r"(\d+)年", text)
        return int(match.group(1)) if match else 0