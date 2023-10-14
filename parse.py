# -*- coding: utf-8 -*-
import math
import json
from tqdm import tqdm
import shapefile
from pyproj import Transformer


def get_cicle(lng, lat, radius):
    # 将wgs84下的经纬度转换为平面坐标
    transformer_43 = Transformer.from_crs("epsg:4326", "epsg:3857")
    transformer_34 = Transformer.from_crs("epsg:3857", "epsg:4326")
    # 计算圆形的边界点
    points = []
    cy, cx = transformer_43.transform(lat, lng)
    for i in range(0, 360, 10):  # 用36个点表示圆
        x = cx + radius * math.cos(math.radians(i))
        y = cy + radius * math.sin(math.radians(i))
        y, x = transformer_34.transform(y, x)  # 转回wgs84
        points.append([x, y])
    return points


def create_shape(index):
    # 创建shp文件
    w = shapefile.Writer(
        target="shapes/polygon_" + str(int(index)) + ".shp",
        shapeType=shapefile.POLYGON,
        encoding="utf-8",
    )
    w.field("name", "C", "40")
    w.field("area_id", "C", "20")
    w.field("country", "C", "20")
    w.field("type", "C", "20")
    return w


color_zone_map = {
    "#DE4329": "禁飞区",
    "#979797": "限高区",
    "#1088F2": "授权区",
    "#FFCC00": "警示区",
    "#EE8815": "加强警示区",
    "#37C4DB": "法规限制区",
    "#00BE00": "法规适飞区",
    "#377A26": "风景示范区",
}

with open("data.txt", "r", encoding="utf-8") as f:
    # 解析下载的文件
    lines = f.readlines()
    index = 0
    w = create_shape(index)
    for il, line in tqdm(enumerate(lines)):  # 循环输出读取的内容
        if il % 50 == 0:
            index += 1
            w = create_shape(index)  # 分文件创建，一个shape太大了无法加载
        data_json = json.loads(line)
        # print(line)
        for area in data_json["data"]["areas"]:
            # print(area["name"], area["area_id"], area["country"], area["color"])
            poly_points = get_cicle(
                float(area["lng"]),
                float(area["lat"]),
                float(area["radius"]),
            )
            # print(poly_points)
            w.poly([poly_points])
            w.record(
                area["name"],
                area["area_id"],
                area["country"],
                color_zone_map[area["color"]],
            )
            country = area["country"]

            if area["polygon_points"] is not None:
                w.poly(area["polygon_points"])
                w.record(
                    area["name"],
                    area["area_id"],
                    country,
                    color_zone_map[area["color"]],
                )

            if area["sub_areas"] is not None:
                for sub_area in area["sub_areas"]:
                    sub_poly_points = get_cicle(
                        float(sub_area["lng"]),
                        float(sub_area["lat"]),
                        float(sub_area["radius"]),
                    )
                    # print(sub_poly_points)
                    w.poly([sub_poly_points])
                    w.record(
                        area["name"],
                        area["area_id"],
                        country,
                        color_zone_map[area["color"]],
                    )

                    if sub_area["polygon_points"] is not None:
                        w.poly(sub_area["polygon_points"])
                        w.record(
                            area["name"],
                            area["area_id"],
                            country,
                            color_zone_map[sub_area["color"]],
                        )
