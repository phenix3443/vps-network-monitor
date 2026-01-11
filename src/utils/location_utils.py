#!/usr/bin/env python3

from typing import Dict, Optional, Tuple


REGION_LOCATIONS: Dict[str, Tuple[float, float]] = {
    "日本东京": (35.6762, 139.6503),
    "日本": (35.6762, 139.6503),
    "新加坡": (1.3521, 103.8198),
    "美国洛杉矶": (34.0522, -118.2437),
    "美国纽约": (40.7128, -74.0060),
    "美国西雅图": (47.6062, -122.3321),
    "美国芝加哥": (41.8781, -87.6298),
    "美国达拉斯": (32.7767, -96.7970),
    "德国法兰克福": (50.1109, 8.6821),
    "德国": (51.1657, 10.4515),
    "英国伦敦": (51.5074, -0.1278),
    "英国": (51.5074, -0.1278),
    "法国巴黎": (48.8566, 2.3522),
    "荷兰阿姆斯特丹": (52.3676, 4.9041),
    "澳大利亚悉尼": (-33.8688, 151.2093),
    "韩国首尔": (37.5665, 126.9780),
    "香港": (22.3193, 114.1694),
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "深圳": (22.5431, 114.0579),
    "广州": (23.1291, 113.2644),
    "印度班加罗尔": (12.9716, 77.5946),
    "加拿大多伦多": (43.6532, -79.3832),
    "芬兰赫尔辛基": (60.1699, 24.9384),
}


def get_location(region: str) -> Optional[Tuple[float, float]]:
    """
    根据区域名称获取地理位置（经纬度）
    
    Args:
        region: 区域名称
        
    Returns:
        (纬度, 经度) 元组，如果找不到则返回 None
    """
    region = region.strip()
    
    # 精确匹配
    if region in REGION_LOCATIONS:
        return REGION_LOCATIONS[region]
    
    # 模糊匹配
    for key, location in REGION_LOCATIONS.items():
        if key in region or region in key:
            return location
    
    return None


def add_location_to_vps(vps: Dict) -> Dict:
    """
    为VPS配置添加地理位置信息
    
    Args:
        vps: VPS配置字典
        
    Returns:
        添加了location字段的VPS配置
    """
    if "location" not in vps:
        region = vps.get("region", "")
        location = get_location(region)
        if location:
            vps["location"] = {"lat": location[0], "lng": location[1]}
    
    return vps
