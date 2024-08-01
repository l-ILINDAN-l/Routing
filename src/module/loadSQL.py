import psycopg2
from data_hosts_vlad import *

def get_tables_as_2d_arrays(host, dbname, user, password) -> dict:
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )

        # Создание курсора
        cursor = conn.cursor()

        # Выполнение запроса для получения списка таблиц
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
        )

        # Получение результата
        tables = cursor.fetchall()

        data = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            # Принудительное декодирование строк в UTF-8 с игнорированием или замещением ошибок
            decoded_rows = []
            for row in rows:
                decoded_row = []
                for col in row:
                    if isinstance(col, bytes):
                        decoded_row.append(col.decode('utf-8', errors='replace'))
                    else:
                        decoded_row.append(col)
                decoded_rows.append(decoded_row)
            data[table_name] = decoded_rows

        return data

    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
    finally:
        # Закрытие курсора и соединения
        if cursor:
            cursor.close()
        if conn:
            conn.close()

name_table_route = ""

try:
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )

    # Создание курсора
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM table_itinerary
        """
    )

    rows = cursor.fetchall()
    a = len(rows)
    name_table_route=f'itinerary{a+1}'
    cursor.execute(
        f"""
        INSERT INTO table_itinerary (itinerary_name) VALUES ('itinerary{a+1}');
        """
    )
    conn.commit()
except Exception as e:
    print(f"Ошибка подключения к базе данных: {e}")
finally:
    # Закрытие курсора и соединения
    if cursor:
        cursor.close()
    if conn:
        conn.close()


print(name_table_route)