import re
import json

def parse_builds(input_file, output_file):
    buildings = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Разделяем на блоки по пустым строкам
    blocks = content.split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        position = None
        orientation = None
        config_type = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('Position:'):
                match = re.search(r'<\s*([\d.-]+)\s*,\s*([\d.-]+)\s*,\s*([\d.-]+)\s*>', line)
                if match:
                    position = [float(match.group(1)), float(match.group(2)), float(match.group(3))]
            elif line.startswith('Orientation:'):
                match = re.search(r'<\s*([\d.-]+)\s*,\s*([\d.-]+)\s*,\s*([\d.-]+)\s*>', line)
                if match:
                    orientation = [float(match.group(1)), float(match.group(2)), float(match.group(3))]
            elif line.startswith('Config-Type:'):
                config_type = line.split(':', 1)[1].strip()
        
        # Игнорируем блок, если нет classname
        if not config_type:
            continue
        
        # Угол - первый параметр ориентации
        angle = orientation[0] if orientation else 0.0
        
        building = {
            'classname': config_type,
            'position': position,
            'angle': angle
        }
        buildings.append(building)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(buildings, f, indent=2)
    
    print(f"Спаршено {len(buildings)} зданий в {output_file}")

if __name__ == '__main__':
    parse_builds('builds.txt', 'builds_database.json')
