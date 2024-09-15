import os
from dotenv import load_dotenv
import psycopg2
import requests

# Load environment variables from .env file
load_dotenv()

print("Welcome to the Recipe Generator that helps you prepare the perfect meal using the ingredients you have at home ")

user_name = input("Please Tell Us What Is Your Name\n").lower()

# Fetch password from environment variable
db_password = os.getenv("DB_PASSWORD")

if not db_password:
    print("Error: DB_PASSWORD environment variable is not set.")
    exit(1)

conn = psycopg2.connect(
    host="localhost",
    database="smart_recipe_db",
    user="postgres",
)

cur = conn.cursor()

cur.execute("SELECT name FROM Users WHERE name = %s", (user_name,))

user = cur.fetchone()
if user:
    print(f" Welcome back, {user[0]}!")
    # Check if user wants to update ingredients
    has_new_ingredients = input("Do you have any new ingredients? Or would you like to proceed with what you already had? Answer with yes/no: ")
    if has_new_ingredients.lower() == "yes":
        new_ingredients = input("Great! Give me an updated list, separated by commas: ")
        cur.execute("""
        UPDATE Users
        SET ingredients = %s
        WHERE name = %s;
        """, (new_ingredients, user_name))
        conn.commit()
        print("Your ingredients have been updated.")
    elif has_new_ingredients.lower() == "no":
        print("Okay, let's proceed with what you already had.")
    else:
        print("I didn't get it right, start over.")
else:
    print("Welcome!")
    preferences = input("What kind of recipe would you like to get? 'vegetarian', 'carnivorous', 'vegan', 'gluten free', or 'sensitivity to dairy products': ")
    ingredients = input("Tell us what ingredients you have, separated by commas: ")
    cur.execute("""
    INSERT INTO Users (name, preferences, ingredients)
    VALUES (%s, %s, %s)
    """, (user_name, preferences, ingredients))
    conn.commit()

SPOONS_API_KEY = '75c5943f0a8f4f3b999982259b7e1693'
cur.execute("""
    SELECT ingredients
    FROM Users
    WHERE name = %s;
    """, (user_name,))
users_ingredients = cur.fetchone()

if users_ingredients:
    ingredients_query = users_ingredients[0].replace(" ", "")  # Access the first element of the tuple and remove spaces

url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredients_query}&number=5&apiKey={SPOONS_API_KEY}"
response = requests.get(url)
missing_ingredients = int(input("How many missing ingredients are acceptable? "))

if response.status_code == 200:
    recipes = response.json()
    filtered_recipes = [recipe for recipe in recipes if recipe['missedIngredientCount'] <= missing_ingredients]  # Filter recipes
    if filtered_recipes:
        print("\nHere are some recipes you can make with your ingredients:\n")
        for i, recipe in enumerate(filtered_recipes, 1):
            print(f"{i}. {recipe['title']}")
        chosen_recipe_number = int(input('Write the number of the recipe you want to get the ingredients and steps: '))
        chosen_recipe_id = filtered_recipes[chosen_recipe_number - 1]['id']
        details_url = f"https://api.spoonacular.com/recipes/{chosen_recipe_id}/information?apiKey={SPOONS_API_KEY}"
        details_response = requests.get(details_url)
        if details_response.status_code == 200:
            recipe_details = details_response.json()
            print(f"\nRecipe: {recipe_details['title']}")
            print("Ingredients needed:")
            for ingredient in recipe_details['extendedIngredients']:
                print(f"  - {ingredient['original']}")
            print("Steps to make:")
            for step in recipe_details['analyzedInstructions'][0]['steps']:
                print(f"  {step['number']}. {step['step']}")
        else:
            print("Sorry, no detailed information was found for the selected recipe.")
    else:
        print("No recipes match your criteria.")
else:
    print("Error fetching recipes from Spoonacular API.")
