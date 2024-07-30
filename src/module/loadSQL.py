import psycopg2

# Параметры подключения к базе данных
host = "LOCALHOST"       # Адрес сервера базы данных
port = "5432"            # Порт подключения к базе данных
dbname = "postgres"  # Имя базы данных
user = "postgres"   # Имя пользователя
password = "U-)ei12uwji"  # Пароль

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

    # Вывод списка таблиц
    print("Список таблиц в базе данных:")
    for table in tables:
        print(table[0])

except Exception as e:
    print(f"Ошибка подключения к базе данных: {e}")
finally:
    # Закрытие курсора и соединения
    if cursor:
        cursor.close()
    if conn:
        conn.close()