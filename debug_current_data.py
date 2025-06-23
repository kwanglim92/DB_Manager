import sqlite3

conn = sqlite3.connect('../data/local_db.sqlite')
cursor = conn.cursor()

print('=== NX-wafer 장비 유형 실제 DB 데이터 ===')
cursor.execute('''
    SELECT d.id, d.parameter_name, d.module_name, d.part_name, d.source_files, d.description 
    FROM Default_DB_Values d
    WHERE d.equipment_type_id = 3
    ORDER BY d.id
''')
results = cursor.fetchall()

print(f"총 {len(results)}개 파라미터:")

for row in results:
    id, param_name, module_name, part_name, source_files, description = row
    print(f'\nID {id}: {param_name}')
    print(f'  Module: "{module_name}"')
    print(f'  Part: "{part_name}"')
    print(f'  Source: "{source_files}"')
    print(f'  Description: "{description}"')

# get_default_values 쿼리와 동일한 결과 확인
print(f'\n=== get_default_values 쿼리 결과 (UI에서 사용하는 것) ===')
cursor.execute('''
    SELECT d.id, d.parameter_name, d.default_value, d.min_spec, d.max_spec, e.type_name,
           d.occurrence_count, d.total_files, d.confidence_score, d.source_files, d.description,
           d.module_name, d.part_name, d.item_type, d.is_performance
    FROM Default_DB_Values d
    JOIN Equipment_Types e ON d.equipment_type_id = e.id
    WHERE d.equipment_type_id = 3
    ORDER BY d.confidence_score DESC, d.parameter_name
''')
results = cursor.fetchall()

labels = ['id', 'parameter_name', 'default_value', 'min_spec', 'max_spec', 'type_name', 
          'occurrence_count', 'total_files', 'confidence_score', 'source_files', 'description', 
          'module_name', 'part_name', 'item_type', 'is_performance']

for row in results:
    print(f'\n파라미터: {row[1]}')
    for i, value in enumerate(row):
        if i in [11, 12]:  # module_name, part_name
            print(f'  {labels[i]} (index {i}): "{value}"')

conn.close() 