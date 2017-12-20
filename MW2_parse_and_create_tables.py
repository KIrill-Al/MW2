import urllib.request
import urllib.error
import re
import datetime
import psycopg2


def get_date(date):
    months = {'января': '01','февраля': '02', 'марта': '03', 'апреля': '04', 'мая': '05',
              'июня': '06', 'июля': '07', 'августа': '08', 'сентября': '09', 'октября': '10',
              'ноября': '11', 'декабря': '12'}
    date = date.strip()
    date_lst = date.split(' ')
    result_date = ''
    if date_lst[0].isdigit():
        result_date = '{}-{}'.format(months[date_lst[1]], date_lst[0])
        if date_lst[2].isdigit():
            result_date = '{}-{}'.format(date_lst[2], result_date)
        else:
            result_date = '{}-{}'.format(datetime.date.today().year, result_date)
        return result_date
    elif date_lst[0] == 'вчера':
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        return '{}-{}-{}'.format(yesterday.year, yesterday.month, yesterday.day)
    elif date_lst[0] == 'сегодня':
        today = datetime.date.today()
        return '{}-{}-{}'.format(today.year, today.month, today.day)


def parse_habr(encoding='utf-8'):
    url = 'https://habrahabr.ru/top/weekly/page'
    max_page = 11
    post_tag = '<article[\W\w]+?</article>'
    title_tag = 'class="post__title_link">([\W\w]+?)</a>'
    date_tag = '<span class="post__time">([\W\w]+?)</span>'
    author_tag = '<span class="user-info__nickname user-info__nickname_small">([\W\w]+?)</span>'
    hubname_tag = '; }">([\W\w]+?)</a>'
    posts_list = []
    for page in range(1, max_page):
        res = urllib.request.urlopen('{}{}/'.format(url, page))
        html_habr = res.read().decode(encoding)
        posts_html = re.findall(post_tag, html_habr)
        for post in posts_html:
            post_title = re.findall(title_tag, post)[0]
            post_date = re.findall(date_tag, post)[0]
            post_date = get_date(post_date)
            post_author = re.findall(author_tag, post)[0]
            post_hubs = re.findall(hubname_tag, post)
            posts_list.append({'title': post_title, 'author': post_author,
                               'hubs': post_hubs, 'date': post_date})
    return posts_list


def create_tables():
    commands_list = ['DROP TABLE IF EXISTS authors, articles, hubs CASCADE;',
                     'CREATE TABLE authors (id serial PRIMARY KEY, name VARCHAR);',
                     'CREATE TABLE articles (id serial PRIMARY KEY, title VARCHAR, \
                     author VARCHAR, hubs VARCHAR, date VARCHAR);',
                     'CREATE TABLE hubs (id serial PRIMARY KEY, name VARCHAR);']
    try:
        conn = psycopg2.connect(host='localhost', port=5432,
                                dbname='habr_db', user='kirill', password='qwerty')
    except psycopg2.Error as e:
        print(e)
    else:
        cursor = conn.cursor()
        for command in commands_list:
            cursor.execute(command)
        conn.commit()


def write_to_db(posts):
    try:
        conn = psycopg2.connect(host='localhost', port=5432,
                                dbname = 'habr_db', user = 'kirill', password = 'qwerty')
    except psycopg2.Error as e:
        print(e)
    else:
        cursor = conn.cursor()
        for post in posts:
            cursor.execute("SELECT count(name) FROM authors WHERE name = '{}';".format(post['author']))
            result = cursor.fetchall()
            if int(result[0][0]) == 0:  # если в таблице нет такого автора, заносим  его
                cursor.execute("INSERT INTO authors (name) VALUES ('{}');".format(post['author']))
            hubs_str = ''  # строка для записи хабов в базу
            for hub in post['hubs']:  # т. к. хабы для статьи - это список, проверяем по отдельности
                cursor.execute("SELECT count(name) FROM hubs WHERE name = '{}';".format(hub))
                result = cursor.fetchall()
                if int(result[0][0]) == 0: # если в таблице нет такого хаба, добавляем
                    cursor.execute("INSERT INTO hubs (name) VALUES ('{}');".format(hub))
                hubs_str = '{}{},'.format(hubs_str, hub)  # формируем строку для записи в базу
            cursor.execute("INSERT INTO articles (title, author, hubs, date) \
            VALUES ('{}', '{}', '{}', '{}');".format(post['title'], post['author'], hubs_str, post['date']))
            conn.commit()


if __name__ == '__main__':
    create_tables()
    write_to_db(parse_habr())