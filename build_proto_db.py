import xml.etree.ElementTree as ET
import json
import os

def build_proto_database(xml_path, output_json):
    if not os.path.exists(xml_path):
        print(f"Ошибка: Файл {xml_path} не найден.")
        return

    print(f"Чтение файла прототипов: {xml_path}...")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    database = {}
    stats = {
        "total_groups": 0,
        "groups_with_loot": 0,
        "total_points": 0
    }

    for group in root.findall('group'):
        class_name = group.get('name')
        if not class_name:
            continue
        
        stats["total_groups"] += 1
        
        # Ищем контейнер lootFloor
        loot_floor_container = None
        for container in group.findall('container'):
            if container.get('name') == 'lootFloor':
                loot_floor_container = container
                break
        
        if loot_floor_container is not None:
            points = []
            for point in loot_floor_container.findall('point'):
                pos_str = point.get('pos')
                if pos_str:
                    try:
                        coords = list(map(float, pos_str.split()))
                        if len(coords) == 3:
                            points.append(coords)
                    except ValueError:
                        continue
            
            if points:
                database[class_name] = {
                    "lootFloor": points
                }
                stats["groups_with_loot"] += 1
                stats["total_points"] += len(points)

    # Сохранение в JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2)

    print(f"База данных сохранена в {output_json}")
    print(f"Статистика:")
    print(f"  - Всего групп в прото: {stats['total_groups']}")
    print(f"  - Групп с контейнером 'lootFloor': {stats['groups_with_loot']}")
    print(f"  - Всего точек спавна: {stats['total_points']}")
    
    # Вывод примера (первые 3 элемента)
    print("\nПример данных (первые 3 класса):")
    for i, (cls, data) in enumerate(database.items()):
        if i >= 3:
            break
        print(f"  Класс: {cls}")
        print(f"    Точек: {len(data['lootFloor'])}")
        print(f"    Первая точка: {data['lootFloor'][0]}")

if __name__ == "__main__":
    build_proto_database("mapgroupproto.xml", "proto_database.json")
