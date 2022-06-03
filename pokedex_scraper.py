import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import random
import time


class PokedexScraper:
    """Scrapes a page from 
    https://www.pokemon.com/us/pokedex/+the+name+of+a+pokemon.

    ...

    Attributes
    ----------
    url
    pokemon
    abilities
    next_pokemon_url
    """

    def __init__(self, pokemon_url):
        """
        Parameters
        ----------
        pokemon_url : str
            A pokemon's pokedex page.

        Raises
        ------
        ValueError
            If the passed url does not start with
            https://www.pokemon.com/us/pokedex/.
        """
        # Check for a valid url.
        if not pokemon_url.startswith("https://www.pokemon.com/us/pokedex/"):
            error_message = """The PokedexScraper can only scrape pages at 
                https://www.pokemon.com/us/pokedex/ + the name of a pokemon. 
                The url "{}" was passed.""".format(pokemon_url)
            raise ValueError(error_message)

        self._url = pokemon_url
        r = requests.get(self._url)
        self._soup = BeautifulSoup(r.text, "html.parser")

        self._pokemon = self.__scrape_pokemon()
        self._abilities = self.__scrape_abilities()
        self._next_pokemon_url = self.__scrape_next_pokemon_url()

    @property
    def url(self):
        """Get the url of the pokedex page that was scraped."""
        return self._url

    @property
    def pokemon(self):
        """Get the pokemon info that was scraped."""
        return self._pokemon

    @property
    def abilities(self):
        """Get the abilities that were scraped."""
        return self._abilities

    @property
    def next_pokemon_url(self):
        """Get the url of the next pokemon in the pokedex."""
        return self._next_pokemon_url

    def __scrape_pokemon(self):
        """Creates a dictionary containing all of the pokemon's info.

        Returns
        -------
        pokemon : dictionary
            The pokemon's info scraped from the website.
        """
        pokemon = {}
        pokemon["url"] = self.url
        pokemon["name"] = self.__scrape_name()
        pokemon["number"] = self.__scrape_number()
        pokemon["evolutions"] = self.__scrape_evolutions()

        # Gather the info specific to each form of the pokemon.
        formes = self.__scrape_formes()
        images = self.__scrape_images(formes)
        descriptions = self.__scrape_descriptions(formes)
        types = self.__scrape_types(formes)
        misc_info = self.__scrape_misc_info(formes)

        # Add the form-specific info to the dictionary.
        pokemon["formes"] = []
        for form in formes:
            form_dict = {}
            form_dict["form"] = form
            form_dict["image"] = images[form]
            form_dict["descriptions"] = descriptions[form]
            form_dict["types"] = types[form]
            form_dict.update(misc_info[form])
            pokemon["formes"].append(form_dict)

        return pokemon

    def __scrape_name(self):
        """Scrape the name of the pokemon on this page.

        Returns
        -------
        str
            The pokemon's name.
        """
        pokemon_title = self._soup.find(
            class_="pokedex-pokemon-pagination-title").contents[1]
        return pokemon_title.contents[0].strip(" \n")

    def __scrape_number(self):
        """Scrape the number of the pokemon on this page.

        Returns
        -------
        int
            The pokemon's number.
        """
        pokemon_title = self._soup.find(
            class_="pokedex-pokemon-pagination-title").contents[1]
        return int(pokemon_title.contents[1].string.strip(" \n#"))

    def __scrape_formes(self):
        """Scrape the different formes of the pokemon on this page.

        Each pokemon can come in one to several different formes.

        Returns
        -------
        formes : list of str
            A list of the formes this pokemon comes in.
        """
        formes = []
        formes_tag = self._soup.find(id="formes")
        if formes_tag:
            for form in formes_tag.contents[1::2]: # Slice to remove newlines
                formes.append(form.string.strip(" \n"))
        else: # Only one form so use the pokemon's name.
            formes.append(self.__scrape_name())
        return formes

    def __scrape_images(self, formes):
        """Scrape the urls of images of the pokemon.

        There is one image for each form of the pokemon.

        Parameters
        ----------
        formes : list of str
            The different formes of this pokemon.

        Returns
        -------
        images : dictionary
            The formes of this pokemon paired 
            with the url of their image.
        """
        images = {}
        images_tag = self._soup.find(class_="profile-images").find_all("img")
        for image, form in zip(images_tag, formes):
            images[form] = image["src"]
        return images

    def __scrape_descriptions(self, formes):
        """Scrape the short biographies of the pokemon
         called descriptions in the site's html.

        There are two descriptions for each form of the pokemon.

        Parameters
        ----------
        formes : list of str
            The different formes of this pokemon.

        Returns
        -------
        descriptions : dictionary
            The formes of this pokemon paired 
            with a list of their two descriptions.
        """
        descriptions = {}
        descriptions_tag = self._soup.find_all(class_="version-descriptions")
        for two_descriptions, form in zip(descriptions_tag, formes):
            form_descriptions = []
            for description in two_descriptions.find_all("p"):
                form_descriptions.append(description.string.strip(" \n"))
            descriptions[form] = form_descriptions
        return descriptions

    def __scrape_types(self, formes):
        """Scrape the types of the pokemon.

        There are one to two types for each form of the pokemon.

        Parameters
        ----------
        formes : list of str
            The different formes of this pokemon.

        Returns
        -------
        types : dictionary
            The formes of this pokemon paired 
            with a list of their types.
        """
        types = {}
        types_tag = self._soup.find_all(class_="dtm-type")
        for form_types, form in zip(types_tag, formes):
            form_types_list = []
            for type_ in form_types.find_all("li"):
                form_types_list.append(type_.text.strip(" \n"))
            types[form] = form_types_list
        return types

    def __scrape_misc_info(self, formes):
        """Scrape miscellaneous info about the pokemon from
        a table on the site.

        There's a table for each form of the pokemon.

        Parameters
        ----------
        formes : list of str
            The different formes of this pokemon.

        Returns
        -------
        info : dictionary
            The formes of this pokemon paired with a dictionary of 
            their info. The info dictionaries pair the names of the 
            info, such as height, with their values.
        """
        info = {}
        info_tag = self._soup.find_all(class_="pokemon-ability-info")

        # The for loop creates a dictionary of info for each pokemon form.
        for form_info, form in zip(info_tag, formes):
            # The titles html contains the keys for the dictionary.
            titles = form_info.find_all(class_="attribute-title")
            # The values html contains the values for the dictionary.
            values = form_info.find_all(class_="attribute-value")
            info[form] = {}

            # Add this form's height and weight.
            for i in range(2):
                info[form][titles[i].text.lower()] = values[i].text
            
            # Add the possible genders in text form rather than symbols.
            genders = []
            icons = values[2].find_all(class_="icon")
            if icons: # If they're symbols.
                for icon in icons:
                    if icon.attrs["class"][1].find("female") != -1:
                        genders.append("Female")
                    else:
                        genders.append("Male")
            else: # If they're text.
                genders.append(values[2].text.strip(" \n"))
            info[form][titles[2].text.lower()] = genders

            # Add this form's category.
            info[form][titles[3].text.lower()] = values[3].text

            # Put the abilities in a list.
            if len(titles) > 4 and len(values) > 4:
                abilities = []
                for ability in values[4:]:
                    abilities.append(ability.text.strip(" \n"))
                info[form][titles[4].text.lower()] = abilities
        return info
            
    def __scrape_evolutions(self):
        """Scrape the evolution line of this pokemon.

        Returns
        -------
        evolutions : list
            A list of dictionaries where each dictionary pairs the
            name of that spot in the evolution line with a list
            of the pokemon in that spot.
        """
        evolutions_tag = self._soup.find(class_="evolution-profile")
        evolutions = []
        if evolutions_tag:
            for evo_line_spot in evolutions_tag.contents[1::2]:
                evo_spot = evo_line_spot.attrs["class"][0]
                evos_in_spot = [evo.contents[0].strip(" \n") 
                                for evo in evo_line_spot.find_all("h3")]
                evolutions.append({evo_spot: evos_in_spot})
        return evolutions

    def __scrape_abilities(self):
        """Scrape the abilities of the pokemon.

        Returns
        -------
        abilities : list
            A list of dictionaries where each dictionary pairs 
            the name of an ability with its description.
        """
        # Gather the abilities and their descriptions in a dictionary.
        abilities = {}
        for ability_element in self._soup.find_all(
                class_="pokemon-ability-info-detail"):
            ability_name = ability_element.find("h3").text.strip(" \n")
            # There might be duplicate abilities from different forms.
            if ability_name not in abilities.keys():
                ability_description = ability_element.find(
                    "p").text.strip(" \n")
                abilities[ability_name] = ability_description
        # Give each ability its own dictionary and return a list of them.
        return [{"ability": ability, "description": description}
                for ability, description in abilities.items()]

    def __scrape_next_pokemon_url(self):
        """Scrape the url of the next pokemon in the pokedex.

        Returns
        -------
        str
            The url of the next pokemon in the pokedex.
        """
        next_pokemon = self._soup.find('a', class_="next")["href"]
        return "https://www.pokemon.com" + next_pokemon

    def __str__(self):
        return "url: {}\npokemon: {}\nabilities: {}\nnext pokemon: {}".format(
            self.url, self.pokemon, self.abilities, self.next_pokemon_url)


def main():
    """
    Scrape the entire pokedex and save the data in a mongodb database.
    """
    # Set up the database.
    client = MongoClient()
    db = client["pokedex"]
    pkmn_collection = db["pokemon"]
    pkmn_collection.create_index("number", unique=True)
    ability_collection = db["abilities"]
    ability_collection.create_index("ability", unique=True)

    first_pokemon_url = "https://www.pokemon.com/us/pokedex/bulbasaur"
    url = first_pokemon_url
    # Scrape the pokedex page of each pokemon and
    # put the info into the mongodb database.
    while (True):
        # Wait a fraction of a second in between requests to be
        # nice to the server.
        delay = random.random()
        time.sleep(delay)

        # Scrape a pokedex page and store the info in the database.
        pkdx = PokedexScraper(url)
        print(pkdx.pokemon["number"])
        pkmn_collection.insert_one(pkdx.pokemon)
        for ability in pkdx.abilities:
            ability_collection.update_one({"ability": ability["ability"]},
                                        {"$set": ability}, upsert=True)
        # The pokedex website wraps around to the beginning.
        if pkdx.next_pokemon_url == first_pokemon_url:
            break
        else:
            url = pkdx.next_pokemon_url  
    print("done")


if __name__ == "__main__":
    main()