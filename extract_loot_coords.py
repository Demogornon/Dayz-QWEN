import json
import math

def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def rotate_point(x, z, angle_deg):
    """Поворот точки (x, z) на угол angle_deg вокруг центра (0,0)."""
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    x_new = x * cos_a - z * sin_a
    z_new = x * sin_a + z * cos_a
    
    return x_new, z_new

def main():
    # Загрузка данных
    builds_data = load_json('builds_database.json')
    proto_data = load_json('proto_full_database.json')
    
    result_points = set() # Используем множество для автоматического удаления дубликатов координат
    
    for building in builds_data:
        classname = building.get('classname')
        position = building.get('position')
        angle = building.get('angle', 0.0)
        
        if not classname or not position:
            continue
            
        # Ищем локальные точки для этого типа здания
        if classname not in proto_data:
            # Если точного совпадения нет, пропускаем
            continue
            
        loot_points = proto_data[classname].get('lootFloor', [])
        
        bx, by, bz = position
        
        for local_point in loot_points:
            lx, ly, lz = local_point
            
            # Поворот локальных координат X и Z
            rx, rz = rotate_point(lx, lz, angle)
            
            # Смещение к мировым координатам
            world_x = bx + rx
            world_y = by + ly
            world_z = bz + rz
            
            # Округляем до 6 знаков для корректного сравнения дубликатов и читаемости
            point_key = (round(world_x, 6), round(world_y, 6), round(world_z, 6))
            result_points.add(point_key)
    
    # Конвертируем множество обратно в список списков с добавлением 4-го параметра (0)
    final_result = []
    for px, py, pz in result_points:
        final_result.append([px, py, pz, 0])
    
    # Сортировка для стабильности вывода
    final_result.sort(key=lambda p: (p[0], p[1], p[2]))
    
    # Запись результата
    with open('result_coords.txt', 'w', encoding='utf-8') as f:
        json.dump(final_result, f, indent=2)
        
    print(f"Готово! Сгенерировано {len(final_result)} уникальных точек.")

if __name__ == "__main__":
    main()
