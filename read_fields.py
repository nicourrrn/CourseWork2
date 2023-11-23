import psycopg2

if __name__ == '__main__':
    connect = psycopg2.connect("dbname=course_work user=django password=django")

    cursor = connect.cursor()

    cursor.execute("""SELECT table_name, column_name, data_type 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE table_name like 'main_%' """)

    data = cursor.fetchall()
    data.sort()
    for row in data:
        print(f"{row[1]}")
    print("-" * 50)
    for i, row in enumerate(data):
        print(f"{row[0]}.{row[1]}")
        print(f"{i})", "{item_id, material_id, type_id, worker_id} ->", row[1])
    print(", ".join([i[1] for i in data]))
