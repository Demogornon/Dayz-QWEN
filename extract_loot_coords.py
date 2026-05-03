#!/usr/bin/env python3
"""
Скрипт для извлечения мировых координат точек спавна лута для зданий в зонах NWAF.
Использует полную базу данных proto_full_database.json
"""

import xml.etree.ElementTree as ET
import json
import math
from pathlib import Path


def load_zones(json_path):
    """Загрузить зоны из JSON файла."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            zones = []
            for zone in data.get('FirstPersonZones', []):
                zones.append({
                    'name': zone['Name'],
                    'x': zone['X'],
                    'z': zone['Z'],
                    'radius': zone['Radius']
                })
            return zones
    except Exception as e:
        print(f"Ошибка чтения JSON: {e}")
        return None


def get_builtin_zones():
    """Встроенные зоны NWAF (расширенные)."""
    return [
        {"name": "NWAF 1", "x": 4327.0, "z": 10678.0, "radius": 950},
        {"name": "NWAF 2", "x": 4867.0, "z": 9809.0, "radius": 980},
        {"name": "NWAF 3", "x": 4027.0, "z": 11330.0, "radius": 850},
        {"name": "NWAF 4", "x": 4029.0, "z": 11766.0, "radius": 750},
        {"name": "NWAF 5", "x": 4449.0, "z": 10173.0, "radius": 700},
        {"name": "NWAF 6", "x": 5000.0, "z": 9323.0, "radius": 680},
        {"name": "NWAF 7", "x": 3800.0, "z": 10923.0, "radius": 600},
        {"name": "NWAF 8", "x": 4801.0, "z": 10411.0, "radius": 550},
        {"name": "NWAF 9", "x": 3700.0, "z": 11574.0, "radius": 580},
        {"name": "NWAF 10", "x": 4240.0, "z": 11640.0, "radius": 600}
    ]


def is_in_zone(x, z, zones):
    """Проверить, попадает ли точка (x, z) в любую из зон."""
    for zone in zones:
        dx = x - zone['x']
        dz = z - zone['z']
        distance = math.sqrt(dx * dx + dz * dz)
        if distance <= zone['radius']:
            return True, zone['name']
    return False, None


def normalize_class_name(class_name):
    """Нормализовать имя класса, удаляя суффиксы типа _Old, _ruin и т.д."""
    suffixes = ['_Old', '_ruin', '_damage', '_broken', '_destroyed', '_base',
                '_floor', '_wall', '_roof', '_door', '_window', '_gate',
                '_fence', '_tower', '_stairs', '_part', '_end', '_mid',
                '_left', '_right', '_top', '_bottom', '_corner', '_single',
                '_double', '_triple', '_long', '_short', '_wide', '_narrow']

    normalized = class_name
    for suffix in suffixes:
        if normalized.lower().endswith(suffix.lower()):
            normalized = normalized[:-len(suffix)]
            break

    return normalized


def parse_mapgrouppos(xml_path):
    """Парсить mapgrouppos.xml и вернуть список зданий."""
    buildings = []
    tree = ET.parse(xml_path)
    root = tree.getroot()

    for group in root.findall('group'):
        name = group.get('name', '')
        pos_str = group.get('pos', '')
        a_str = group.get('a', '0')

        if not pos_str:
            continue

        parts = pos_str.split()
        if len(parts) < 3:
            continue

        try:
            bx = float(parts[0])
            by = float(parts[1])
            bz = float(parts[2])
            angle_a = float(a_str) if a_str else 0.0
        except ValueError:
            continue

        buildings.append({
            'name': name,
            'bx': bx,
            'by': by,
            'bz': bz,
            'angle_a': angle_a
        })

    return buildings


def load_proto_database(db_path):
    """Загрузить полную базу данных прототипов из JSON."""
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения базы данных: {e}")
        return {}


def find_prototype(class_name, proto_db):
    """Найти прототип по имени класса в полной базе данных (возвращает все контейнеры)."""
    # Прямое совпадение
    if class_name in proto_db:
        return proto_db[class_name]

    # Нормализованное совпадение
    normalized = normalize_class_name(class_name)
    if normalized in proto_db:
        return proto_db[normalized]

    # Попытка найти частичное совпадение
    for proto_name, containers in proto_db.items():
        if proto_name.startswith(class_name) or class_name.startswith(proto_name):
            return containers
        if normalize_class_name(proto_name) == normalized:
            return containers

    return None


def calculate_world_coords(bx, by, bz, angle_a, local_points):
    """Рассчитать мировые координаты для локальных точек."""
    # ИСПРАВЛЕНО: Рабочий угол = значение атрибута a (без инверсии!)
    yaw_degrees = angle_a
    yaw_radians = math.radians(yaw_degrees)

    cos_yaw = math.cos(yaw_radians)
    sin_yaw = math.sin(yaw_radians)

    world_points = []
    for lx, ly, lz in local_points:
        x_world = bx + (lx * cos_yaw - lz * sin_yaw)
        y_world = by + ly
        z_world = bz + (lx * sin_yaw + lz * cos_yaw)
        world_points.append((x_world, y_world, z_world))

    return world_points


def main():
    base_dir = Path('/workspace')

    # Загрузка зон
    zones = load_zones(base_dir / 'Zen3ppConfig (1).json')
    if zones is None:
        print("Использую встроенные зоны NWAF...")
        zones = get_builtin_zones()

    print(f"Загружено зон: {len(zones)}")

    # Парсинг mapgrouppos.xml
    print("Парсинг mapgrouppos.xml...")
    buildings = parse_mapgrouppos(base_dir / 'mapgrouppos.xml')
    print(f"Всего зданий в mapgrouppos.xml: {len(buildings)}")

    # Фильтрация зданий по зонам
    buildings_in_zones = []
    for building in buildings:
        in_zone, zone_name = is_in_zone(building['bx'], building['bz'], zones)
        if in_zone:
            building['zone'] = zone_name
            buildings_in_zones.append(building)

    print(f"Зданий в зонах: {len(buildings_in_zones)}")

    # Загрузка полной базы данных прототипов
    print("Загрузка proto_full_database.json...")
    proto_db = load_proto_database(base_dir / 'proto_full_database.json')
    print(f"Всего прототипов в базе: {len(proto_db)}")

    # Обработка зданий и расчет координат (используем только lootFloor)
    all_world_points = []
    matched_count = 0
    not_matched_count = 0

    for building in buildings_in_zones:
        proto_containers = find_prototype(building['name'], proto_db)

        if proto_containers and 'lootFloor' in proto_containers:
            matched_count += 1
            loot_floor_points = [tuple(p) for p in proto_containers['lootFloor']]
            world_points = calculate_world_coords(
                building['bx'], building['by'], building['bz'],
                building['angle_a'], loot_floor_points
            )
            for wp in world_points:
                all_world_points.append(wp)
        else:
            not_matched_count += 1

    print(f"\n=== СТАТИСТИКА ===")
    print(f"Зданий в зонах: {len(buildings_in_zones)}")
    print(f"Прототипов найдено: {matched_count}")
    print(f"Прототипов не найдено: {not_matched_count}")
    print(f"Всего точек спавна: {len(all_world_points)}")

    # Запись результата
    output_path = base_dir / 'result_coords.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        for x, y, z in all_world_points:
            f.write(f"[ {x:.6f}, {y:.6f}, {z:.6f}, 0 ],\n")

    print(f"\nРезультат записан в: {output_path}")

    # Вывод первых 20 строк
    print("\n=== ПЕРВЫЕ 20 ТОЧЕК ===")
    for i, (x, y, z) in enumerate(all_world_points[:20]):
        print(f"[ {x:.6f}, {y:.6f}, {z:.6f}, 0 ],")


if __name__ == '__main__':
    main()
