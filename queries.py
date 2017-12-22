#!/usr/bin/env python3
import argparse
import psycopg2


def get_query(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    for row in result:
        print(row)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--p', nargs=3,
                        metavar=('<имя хаба>', 'начало периода (YYYY-MM-DD)', 'конец периода (YYYY-MM-DD)'))
    parser.add_argument('--w', action='store_true', help='Популярные статьи за неделю')
    parser.add_argument('--top_hub', action='store_true', help='Самые популярные хабы')
    parser.add_argument('--auth', action='store_true', help='Самые плодовитые авторы')
    args = parser.parse_args()
    try:
        conn = psycopg2.connect(host='localhost', port=5432,
                                dbname='habr_db', user='kirill',password='qwerty')
    except psycopg2.Error as e:
        print(e)
    else:
        if args.p:
            query = "SELECT * FROM articles WHERE hubs LIKE '%{}%' AND (date>='{}' AND date<='{}');".format(
                *args.p)
            get_query(conn, query)
        elif args.w:
            query = "SELECT * FROM articles WHERE (DATE(date)>(CURRENT_DATE-7) AND DATE(date)<CURRENT_DATE);"
            get_query(conn, query)
        elif args.top_hub:
            query = "SELECT hubs.name, count(articles.title) as freqency FROM hubs, \
                    articles WHERE articles.hubs LIKE '%'||hubs.name||'%' \
                    GROUP BY hubs.name ORDER BY count(articles.title) desc limit 10;"
            get_query(conn, query)
        elif args.auth:
            query = "SELECT authors.name, count(articles.title) as count_art FROM authors, \
                    articles WHERE articles.author = authors.name GROUP BY authors.name \
                    ORDER BY count(articles.title) desc limit 10;"
            get_query(conn, query)
        else:
            print("Аргументы введены неверно или отсутствуют.")