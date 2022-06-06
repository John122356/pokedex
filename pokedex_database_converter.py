from pymongo import MongoClient
import sqlite3

def create_sqlite_db(db_name):
    ''' Create the sqlite database and its tables.'''
    con = sqlite3.connect(db_name)
    cur = con.cursor()

    sql = '''CREATE TABLE pokemon(
                name TEXT NOT NULL PRIMARY KEY,
                number INTEGER NOT NULL
            );'''
    cur.execute(sql)

    sql = '''CREATE TABLE formes(
                pokemon TEXT NOT NULL,
                form TEXT NOT NULL,
                height TEXT NOT NULL,
                weight TEXT NOT NULL,
                category TEXT NOT NULL,
                type_1 TEXT NOT NULL,
                type_2 TEXT,
                male INTEGER NOT NULL,
                female INTEGER NOT NULL,
                PRIMARY KEY(pokemon, form),
                FOREIGN KEY(pokemon) REFERENCES pokemon(name)
            );'''
    cur.execute(sql)

    sql = '''CREATE TABLE form_descriptions(
                pokemon TEXT NOT NULL,
                form TEXT NOT NULL,
                description TEXT NOT NULL,
                PRIMARY KEY(pokemon, form, description),
                FOREIGN KEY(pokemon, form) REFERENCES formes(pokemon, form)
            );'''
    cur.execute(sql)

    sql = '''CREATE TABLE abilities(
                ability TEXT NOT NULL PRIMARY KEY,
                info TEXT NOT NULL
            );'''
    cur.execute(sql)

    sql = '''CREATE TABLE form_abilities(
                pokemon TEXT NOT NULL,
                form TEXT NOT NULL,
                ability TEXT NOT NULL,
                PRIMARY KEY(pokemon, form, ability),
                FOREIGN KEY(pokemon, form) REFERENCES formes(pokemon, form),
                FOREIGN KEY(ability) REFERENCES abilities(ability)
            );'''
    cur.execute(sql)

    sql = '''CREATE TABLE evolutions(
                pokemon TEXT NOT NULL,
                evolves_to TEXT NOT NULL,
                PRIMARY KEY(pokemon, evolves_to),
                FOREIGN KEY(pokemon) REFERENCES pokemon(name),
                FOREIGN KEY(evolves_to) REFERENCES pokemon(name)
            );'''
    cur.execute(sql)
    con.commit()
    con.close()


def insert_pokemon_table(cur, pkmn):
    values = (pkmn['name'], pkmn['number'])
    print(values)
    cur.execute("INSERT INTO pokemon VALUES (?, ?)", values)

def insert_formes_table(cur, pkmn):
    for form in pkmn['formes']:
        type1 = form['types'][0]
        type2 = None if len(form['types']) < 2 else form['types'][1]
        male = 1 if 'Male' in form['gender'] else 0
        female = 1 if 'Female' in form['gender'] else 0
        values = (pkmn['name'], form['form'], form['height'], form['weight'],
                form['category'], type1, type2, male, female)
        cur.execute("INSERT INTO formes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", values)

def insert_form_descriptions_table(cur, pkmn):
    pass


def fill_sqlite_db(db_name):
    '''Insert the data from the mongodb database into the sqlite database.'''
    client = MongoClient()
    db = client.pokedex
    pkmn_coll = db.pokemon

    con = sqlite3.connect(db_name)
    cur = con.cursor()
    for pkmn in pkmn_coll.find():
        #insert_pokemon_table(cur, pkmn)
        #insert_formes_table(cur, pkmn)
        insert_form_descriptions_table(cur, pkmn)

        if pkmn['name'] == 'Charizard':
            break
    con.commit()
    con.close()

#create_sqlite_db('testing.db')
fill_sqlite_db('testing.db')




print('done')