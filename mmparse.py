import os
import re
import sys

import chardet
from polars import DataFrame

#--- CONSTANTS ---#

UNITS = ['x ', 'sm', 'md', 'lg', 'cn' , 'pk' , 'pn' , 'dr' , 'ds'
               , 'ct' , 'bn' , 'sl' , 'ea' , 't ' , 'ts' , 'T ' , 'tb' , 'fl'
               , 'c ' , 'pt' , 'qt' , 'ga' , 'oz' , 'lb' , 'ml' , 'cb' , 'cl'
               , 'dl' , 'l ' , 'mg' , 'cg' , 'dg' , 'g ' , 'kg' , '  ', '']

QUANTIFIERS = [str(x) for x in range(10)] + [
    "/",
    "."
]

#--- UTILS ---#

def get_center_chars(line) -> str:
    center_index = len(line) // 2
    return line[center_index - 1: center_index + 2]

def split_line_in_middle(line: str) -> list[str]:
    center_index = len(line) // 2

    return [line[:center_index], line[center_index + 1:]]

# --- Classes --- #
class Recipe(object):
    version: int
    title: str
    categories: list[str]
    servings: str
    ingredients: list[str]
    directions: list[str]

    def __str__(self):
        return self.to_dict()

    def __init__(self, recipe_lines: list[str]) -> None:
        self.title = ""
        self.categories = []
        self.servings = 0
        self.ingredients = []
        self.directions = []
        self.parse_and_store_recipe(recipe_lines)

    def parse_and_set_title(self, line: str) -> None:
        self.title = line.split(":")[1].strip()

    def parse_and_set_category_line(self, line: str) -> None:
        self.categories = line.split(":")[1].strip().split(",")

    def parse_and_set_servings(self, line: str) -> None:
        self.servings = line.split(":")[1].strip()

    @staticmethod
    def split_ingredients_line_to_left_right(line: str) -> tuple[str, str]:
        line.strip()
        split_line = split_line_in_middle(line)
        return split_line[0].strip(), split_line[1].strip()

    def parse_ingredient_line(self, line: str) -> None:
        stripped_and_split_line = line.strip().split("     ")
        if len(stripped_and_split_line) >= 2:
            left = stripped_and_split_line[0]
            right = stripped_and_split_line[len(stripped_and_split_line) - 1]

            self.ingredients.append(left)
            self.ingredients.append(right)
            return
        self.ingredients.append(stripped_and_split_line[0])

    def ingredients_are_set(self):
        return self.ingredients != {}

    @staticmethod
    def check_if_ingredients_line(line: str) -> bool:
        quantifier = line[:9]
        unit = line[9:11]

        quantifier_present = False
        unit_present = False

        for q in quantifier.strip():
            if q in QUANTIFIERS:
                quantifier_present = True

        for u in unit.strip():
            if u in UNITS:
                unit_present = True

        return True if quantifier_present or unit_present else False

    @staticmethod
    def parse_ingredients_heading_line(line: str) -> str:
        return line.strip("-").strip(" ").split(" ")[0]

    @staticmethod
    def check_ingredient_heading_line(line: str) -> bool:

        if not line.startswith("-----") or not line.startswith("MMMMM"):
            return False

        if len(line) < 40:
            return False

        if len(set(line.strip("\n"))) == 2:
            return False

        return True

    @staticmethod
    def check_end_line(line: str) -> bool:
        if line.strip().startswith("MMMMM") or line.strip().startswith("-----") and len(set(line.strip())) <= 1 and set(line.strip()).pop() == "-":
            return True
        return False

    def parse_header_section(self, header_lines: list[str]) -> None:
        for line in header_lines:
            start = line.split(":")

            match start[0].strip():

                case "Title":
                    self.parse_and_set_title(line)
                case "Categories":
                    self.parse_and_set_category_line(line)
                case "Servings":
                    self.parse_and_set_servings(line)
                case "Yield":
                    self.parse_and_set_servings(line)
                case _:
                    print(start[0].strip())
                    print("Weird stuff in heading section.")

    def parse_ingredients_section(self, ingredient_lines: list[str]) -> None:
        for line in ingredient_lines:

            if self.check_if_ingredients_line(line):
                self.parse_ingredient_line(line)

    def parse_directions_section(self, directions_sections: list[list[str]]) -> None:
        for directions_section in directions_sections:
            for line in directions_section:
                self.directions.append(line)

    def parse_and_store_recipe(self, lines: list[str]):
        indexes_to_split_on = []
        start_index = 0
        for index, line in enumerate(lines):
            if index == 0 and line.replace(" ", "") == '\n':
                start_index += 1
                continue
            if line.replace(" ", "") == '\n':
                indexes_to_split_on.append(index)

        # first section should he headings and stuff, second the ingredients, all all remaing will be treated as directions
        sections = []
        for index in indexes_to_split_on:
            sections.append(lines[start_index:index])
            start_index = index + 1

        header_section = sections[0]
        ingredients_section = sections[1]
        directions_sections = sections[2:]

        self.parse_header_section(header_section)
        self.parse_ingredients_section(ingredients_section)
        self.parse_directions_section(directions_sections)

    @staticmethod
    def check_recipe_start_line(line: str) -> bool:
        if not re.match(r"Meal-Master", line) and (line.startswith("-----") or line.startswith("MMMMM")):
            return False
        return True

    def to_dict(self):
        categories = ",".join(self.categories)
        ingredients = "---".join(self.ingredients)
        directions = "---".join(self.directions)
        return {"title": self.title, "categories": categories, "servings": self.servings, "ingredients": ingredients, "directions": directions}

class RecipesArr(object):
    output_file_name: str
    df: DataFrame
    arr: list[Recipe]

    def __init__(self, output_file_name):
        self.output_file_name = output_file_name
        self.arr = []
        self.df = None

    def __load_data(self):
        for recipe in self.arr:
            if self.df is None:
                self.df = DataFrame(recipe.to_dict())
                continue
            self.df.extend(DataFrame(recipe.to_dict()))


    def parse_file(self, file_name) -> None:
        with open(file_name, "rb") as raw_bytes:
            raw_data = raw_bytes.read()
            result = chardet.detect(raw_data)
            original_encoding = result.get("encoding")

        with open(file_name, "r", encoding=original_encoding) as f:
            lines = f.readlines()
        lines = lines[1:]

        indexes_to_split_on = []

        for index, line in enumerate(lines):
            if Recipe.check_end_line(line):
                indexes_to_split_on.append(index)

        previous = 0
        for index in indexes_to_split_on:
            recipe = lines[previous:index + 1]
            if not recipe:
                continue
            recipe = Recipe(recipe)
            self.arr.append(recipe)
            previous = index + 3

    def save_to_csv(self):
        self.__load_data()
        self.df.write_csv(self.output_file_name)


def get_files_in_directory(dir_path):
    return [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]

if __name__ == '__main__':
    path = sys.argv[1]
    out_path = sys.argv[2]

    if not os.path.isdir(path):
        new_recipes = RecipesArr(out_path)
        new_recipes.parse_file(path)
        new_recipes.save_to_csv()
        sys.exit(0)

    # first list all the recipes and then do what is needed
    os.chdir(path)
    files = get_files_in_directory(path)

    failed_files = []
    new_recipes = RecipesArr(out_path)
    for file in files:
        try:
            new_recipes.parse_file(file)
        except Exception as e:
            print(e)
            failed_files.append(file)
            pass

    new_recipes.save_to_csv()
    print(failed_files)
    print("Done")