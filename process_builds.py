import xml.etree.ElementTree as ET
import json
import math
import re

# --- КОНФИГУРАЦИЯ ---
BUILDS_FILE = 'builds.txt'
PROTO_DB_FILE = 'proto_full_database.json' # Используем полную базу
OUTPUT_FILE = 'result_coords.txt'
CONTAINER_NAME = 'lootFloor'

def parse_builds_txt(filename):
    """Парсит builds.txt и возвращает список зданий с координатами и углом."""
    buildings = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Ошибка: Файл {filename} не найден.")
        return buildings

    # Разбиваем на блоки по Config-Type или Position (зависит от формата, будем искать блоки)
    # Формат в примере:
    # Position: <x, y, z>
    # Orientation: <x, y, z>
    # Config-Type: Name
    
    # Используем regex для извлечения блоков
    # Ищем паттерн: Position(...), Orientation(...), Config-Type(...)
    pos_pattern = r'Position:\s*<([^>]+)>'
    ori_pattern = r'Orientation:\s*<([^>]+)>'
    type_pattern = r'Config-Type:\s*(\S+)'
    
    # Разделяем файл на блоки (предполагаем, что они идут группами)
    # Простой подход: найти все совпадения и сгруппировать их по порядку
    positions = re.findall(pos_pattern, content)
    orientations = re.findall(ori_pattern, content)
    types = re.findall(type_pattern, content)
    
    count = min(len(positions), len(orientations), len(types))
    print(f"Найдено записей в builds.txt: {count}")
    
    for i in range(count):
        try:
            # Парсим позицию
            p_parts = [float(x.strip()) for x in positions[i].split(',')]
            bx, by, bz = p_parts[0], p_parts[1], p_parts[2]
            
            # Парсим ориентацию
            o_parts = [float(x.strip()) for x in orientations[i].split(',')]
            # Нас интересует только Z (Yaw) из Orientation
            rpy_z = o_parts[2]
            
            # Парсим тип
            class_name = types[i].strip()
            
            # Рассчитываем рабочий угол по формуле: yaw = 90 - rpy_z
            yaw_deg = 90.0 - rpy_z
            
            buildings.append({
                'name': class_name,
                'pos': (bx, by, bz),
                'yaw': yaw_deg
            })
        except Exception as e:
            print(f"Ошибка парсинга записи #{i}: {e}")
            
    return buildings

def load_proto_db(filename):
    """Загружает базу прототипов из JSON."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл {filename} не найден.")
        return {}

def find_prototype_exact(class_name, proto_db):
    """Ищет прототип по точному совпадению имени (case-sensitive), затем case-insensitive."""
    if class_name in proto_db:
        return proto_db[class_name]
    
    # Попытка найти игнорируя регистр
    class_name_lower = class_name.lower()
    for name, data in proto_db.items():
        if name.lower() == class_name_lower:
            return data
            
    return None

def calculate_world_points(building, proto_data, container_name):
    """Рассчитывает мировые координаты точек для здания."""
    points = []
    
    if not proto_data or container_name not in proto_data:
        return points
        
    local_points = proto_data[container_name]
    
    bx, by, bz = building['pos']
    yaw_deg = building['yaw']
    yaw_rad = math.radians(yaw_deg)
    
    cos_yaw = math.cos(yaw_rad)
    sin_yaw = math.sin(yaw_rad)
    
    for lp in local_points:
        lx, ly, lz = lp
        
        # Формула вращения
        wx = bx + (lx * cos_yaw - lz * sin_yaw)
        wy = by + ly
        wz = bz + (lx * sin_yaw + lz * cos_yaw)
        
        points.append([wx, wy, wz, 0.0])
        
    return points

def main():
    print("--- Запуск обработки данных ---")
    
    # 1. Чтение источников
    buildings = parse_builds_txt(BUILDS_FILE)
    proto_db = load_proto_db(PROTO_DB_FILE)
    
    if not buildings:
        print("Нет зданий для обработки.")
        return
    if not proto_db:
        print("Нет базы прототипов.")
        return
        
    results = []
    stats = {'total': 0, 'found': 0, 'points': 0}
    
    # 2. Обработка каждого здания
    for bld in buildings:
        stats['total'] += 1
        proto_data = find_prototype_exact(bld['name'], proto_db)
        
        if proto_data:
            stats['found'] += 1
            points = calculate_world_points(bld, proto_data, CONTAINER_NAME)
            if points:
                stats['points'] += len(points)
                results.extend(points)
            else:
                print(f"Предупреждение: У здания {bld['name']} нет контейнера '{CONTAINER_NAME}'")
        else:
            print(f"Предупреждение: Прототип для {bld['name']} не найден в БД")
            
    # 3. Запись результата
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for pt in results:
            # Формат: [ X, Y, Z, 0 ],
            line = f"[ {pt[0]:.6f}, {pt[1]:.6f}, {pt[2]:.6f}, 0 ],\n"
            f.write(line)
            
    print("\n--- СТАТИСТИКА ---")
    print(f"Всего зданий в builds.txt: {stats['total']}")
    print(f"Найдено прототипов: {stats['found']}")
    print(f"Всего точек спавна сгенерировано: {stats['points']}")
    print(f"Результат сохранен в: {OUTPUT_FILE}")
    
    # Вывод первых 20 строк для проверки
    print("\n--- ПЕРВЫЕ 20 ТОЧЕК ---")
    for i, pt in enumerate(results[:20]):
        print(f"[ {pt[0]:.6f}, {pt[1]:.6f}, {pt[2]:.6f}, 0 ],")

if __name__ == "__main__":
    main()
