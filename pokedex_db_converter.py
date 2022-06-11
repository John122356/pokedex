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
    cur.execute("INSERT INTO pokemon VALUES (?, ?);", values)

def insert_formes_table(cur, pkmn):
    for form in pkmn['formes']:
        type1 = form['types'][0]
        type2 = None if len(form['types']) < 2 else form['types'][1]
        male = 1 if 'Male' in form['gender'] else 0
        female = 1 if 'Female' in form['gender'] else 0
        values = (pkmn['name'], form['form'], form['height'], form['weight'],
                form['category'], type1, type2, male, female)
        cur.execute("INSERT INTO formes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", values)

def insert_form_descriptions_table(cur, pkmn):
    for form in pkmn['formes']:
        desc1 = form['descriptions'][0]
        values = [(pkmn['name'], form['form'], desc1)]
        # Each form has 2 descriptions.
        # But they might be the same and break the database's unique constraint.
        desc2 = form['descriptions'][1]
        if desc1 != desc2:
            values.append((pkmn['name'], form['form'], desc2))
        cur.executemany("INSERT INTO form_descriptions VALUES (?, ?, ?);", values)
        
def insert_abilities_table(cur, ability):
    # Check if the ability is already in the database.
    cur.execute("SELECT * FROM abilities WHERE ability=?;", (ability,))
    if len(cur.fetchall()) == 0:
        # Insert the ability.
        name = ability['ability']
        info = ability['description']
        cur.execute("INSERT INTO abilities VALUES(?, ?);", (name, info))

def insert_form_abilities_table(cur, pkmn):
    values = []
    for form in pkmn['formes']:
        if 'abilities' in form.keys(): # One pokemon doesn't have abilities.
            for ability in form['abilities']:
                values.append((pkmn['name'], form['form'], ability))
    cur.executemany("INSERT INTO form_abilities VALUES (?, ?, ?);", values)

def insert_evolutions_table(cur, pkmn):
    # Check if this pokemon's evolution line is already in the database.
    cur.execute("SELECT * FROM evolutions WHERE pokemon=? OR evolves_to=?;",
                (pkmn['name'], pkmn['name']))
    if len(cur.fetchall()) == 0:
        # Add the pokemon's evolutions to the database.
        values = []
        evos_list = pkmn['evolutions']
        # Combine the dictionaries in evos_list into one dictionary.
        evos = {}
        for dic in evos_list:
            evos.update(dic)
        # I think first, middle, and last are the only possible evolution spots.
        # But I'm going to make sure with an assertion.
        for key in evos.keys():
            assert(key in ['first', 'middle', 'last'])
        # If there are "middle" pokemon, then "first" evolves into "middle",
        # and "middle" evolves into "last".
        if 'middle' in evos.keys():
            for mid_evo in evos['middle']:
                for first_evo in evos['first']:
                    values.append((first_evo, mid_evo))
            for last_evo in evos['last']:
                for mid_evo in evos['middle']:
                    values.append((mid_evo, last_evo))
        # If there are "last" pokemon but no "middle",
        # then "first" evolves into "last".
        elif 'last' in evos.keys():
            for last_evo in evos['last']:
                for first_evo in evos['first']:
                    values.append((first_evo, last_evo))
        cur.executemany("INSERT INTO evolutions VALUES (?, ?);", values)



def fill_sqlite_db(db_name):
    '''Insert the data from the mongodb database into the sqlite database.'''
    client = MongoClient()
    db = client.pokedex
    pkmn_coll = db.pokemon
    ability_coll = db.abilities

    con = sqlite3.connect(db_name)
    cur = con.cursor()
    for ability in ability_coll.find():
        insert_abilities_table(cur, ability)
    for pkmn in pkmn_coll.find():
        insert_pokemon_table(cur, pkmn)
        insert_formes_table(cur, pkmn)
        insert_form_descriptions_table(cur, pkmn)
        insert_form_abilities_table(cur, pkmn)
        insert_evolutions_table(cur, pkmn)

        '''if pkmn['name'] == 'Eevee':
            break'''
    con.commit()
    con.close()

db_name = 'pokedex.db'
create_sqlite_db('testing.db')
fill_sqlite_db('testing.db')


print('done')