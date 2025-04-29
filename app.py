from flask import Flask, render_template_string, request
import requests, re, random, textwrap

app = Flask(__name__)

# API keys
api_list = [
    #'e1dbe9135bb64625a8de84756accc2f6',
    #'7c7e71b239a14d84823f413d211a759c',
    #'115492a3218a47f6b5a75ece2a5d10de',
    #'3a6b5d690ca245e3be8b82525a080b02',
    '95b7b6cb16314c42b4c6fc4073cb1f3d'
]

MEAL_TYPES = ["main course","side dish","dessert","appetizer","salad","bread","breakfast","soup","beverage","sauce","drink"]

def slugify(title):
    """Converts a recipe title to a URL-friendly slug."""
    return re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

def sentence(text):
    return textwrap.fill(text, width=100)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    error = None
    selected_recipe = None
    steps = []
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        allergies = request.form.get('allergies', '').strip().split()
        meal_type = request.form.get('meal_type', '')
        num = request.form.get('num', '5').strip()
        if not num.isdigit() or int(num) <= 0:
            num = '5'
        api_key = random.choice(api_list)
        headers = {'x-api-key': api_key}
        params = {
            'query': query,
            'number': num,
            'sort': 'popularity',
            'add-recipe-information': "true"
        }
        if meal_type and meal_type in MEAL_TYPES:
            params['meal-type'] = meal_type
        if allergies:
            allergies_separated = ",".join(allergies)
            params['exclude-ingredients'] = allergies_separated
        url = 'https://api.apileague.com/search-recipes'
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
        except requests.exceptions.ConnectionError:
            error = "No internet connection. Please check your connection and try again."
            return render_template_string(TEMPLATE, results=None, error=error, meal_types=MEAL_TYPES)
        except requests.exceptions.Timeout:
            error = "The request timed out. Please try again."
            return render_template_string(TEMPLATE, results=None, error=error, meal_types=MEAL_TYPES)
        if response.status_code == 402:
            error = "Sorry, you have used the daily quota of API calls. Please use a different API key or try again tomorrow."
            return render_template_string(TEMPLATE, results=None, error=error, meal_types=MEAL_TYPES)
        if response.status_code != 200:
            error = f"API error: {response.status_code}"
            return render_template_string(TEMPLATE, results=None, error=error, meal_types=MEAL_TYPES)
        data = response.json()
        recipes = data.get('recipes', [])
        if not recipes:
            error = "Sorry, we did not find any recipes with that query."
            return render_template_string(TEMPLATE, results=None, error=error, meal_types=MEAL_TYPES)
        # If user selected a recipe to view details
        selected_index = request.form.get('selected_index')
        if selected_index is not None and selected_index.isdigit():
            selected_index = int(selected_index)
            if 0 <= selected_index < len(recipes):
                selected_recipe = recipes[selected_index]
                if selected_recipe.get('instructions') and selected_recipe['instructions'][0].get('steps'):
                    steps = selected_recipe['instructions'][0]['steps']
        results = []
        for recipe in recipes:
            ingredients = [ing['name'] for ing in recipe.get('ingredients',[])]
            slug = slugify(recipe['title'])
            link = f"https://spoonacular.com/recipes/{slug}-{recipe['id']}"
            results.append({
                'title': recipe['title'],
                'ingredients': ', '.join(ingredients),
                'image': recipe['images'][0] if recipe.get('images') else '',
                'link': link,
                'instructions': recipe.get('instructions', []),
                'id': recipe['id']
            })
        return render_template_string(
            TEMPLATE,
            results=results,
            error=error,
            meal_types=MEAL_TYPES,
            selected_recipe=selected_recipe,
            steps=steps
        )
    return render_template_string(TEMPLATE, results=None, error=None, meal_types=MEAL_TYPES)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SafeBite Recipe Finder</title>
    <h1>SafeBite Recipe Finder</h1>
    <p style="font-size:1.2em; color:#555; margin-top:0.5em;">
        Find delicious recipes tailored to your allergies and preferences. Enter your search and get inspired!
    </p>

    <style>

        body { font-family: Arial, sans-serif; margin: 40px; background: #f8f8ff; }
        h1 { color: #333366; }
        .recipe-card { border: 1px solid #ccc; border-radius: 8px; background: #fff; margin: 15px 0; padding: 16px; box-shadow: 2px 2px 8px #eee; }
        .recipe-card img { max-width: 250px; border-radius: 6px; }
        .error { color: red; font-weight: bold; }
        .ingredients { font-size: 1.05em; margin-bottom: 8px; }
        .instructions { background: #f3f3ff; border-radius: 6px; padding: 12px; margin-top: 10px; }
        .select-btn { background: #333366; color: #fff; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; }
        .select-btn:hover { background: #5555aa; }
    </style>
</head>
<body>
    <form method="post">
        <label>What would you like to find? (do not leave blank):<br>
            <input type="text" name="query" required style="width:300px;">
        </label><br><br>
        <label>Allergies (separate by spaces):<br>
            <input type="text" name="allergies" style="width:300px;">
        </label><br><br>
        <label>Meal type:<br>
            <select name="meal_type">
                <option value="">Any</option>
                {% for m in meal_types %}
                <option value="{{m}}">{{m.title()}}</option>
                {% endfor %}
            </select>
        </label><br><br>
        <label>How many recipes? (default 5):<br>
            <input type="number" name="num" min="1" max="20" value="5" style="width:60px;">
        </label><br><br>
        <button type="submit" class="select-btn">Search</button>
    </form>
    <hr>
    {% if error %}
        <div class="error">{{error}}</div>
    {% endif %}
    {% if results %}
        <h2>Results:</h2>
        {% for recipe in results %}
            <div class="recipe-card">
                <h3>{{loop.index}}. {{recipe.title}}</h3>
                {% if recipe.image %}
                    <img src="{{recipe.image}}" alt="Recipe image"><br>
                {% endif %}
                <div class="ingredients"><b>Ingredients:</b> {{recipe.ingredients}}</div>
                <a href="{{recipe.link}}" target="_blank">View Recipe Page</a>
                <form method="post" style="margin-top:10px;">
                    <!-- Hidden fields to persist search -->
                    <input type="hidden" name="query" value="{{request.form['query']}}">
                    <input type="hidden" name="allergies" value="{{request.form['allergies']}}">
                    <input type="hidden" name="meal_type" value="{{request.form['meal_type']}}">
                    <input type="hidden" name="num" value="{{request.form['num']}}">
                    <input type="hidden" name="selected_index" value="{{loop.index0}}">
                    <button type="submit" class="select-btn">Show Instructions</button>
                </form>
                {% if selected_recipe and selected_recipe['id'] == recipe['id'] %}
                    <div class="instructions">
                        <b>Instructions:</b><br>
                        {% if steps %}
                            <ol>
                            {% for step in steps %}
                                <li>{{step['step']}}</li>
                            {% endfor %}
                            </ol>
                        {% else %}
                            <i>No instructions available for this recipe.</i>
                        {% endif %}
                    </div>
                {% endif %}
            </div>
        {% endfor %}
    {% endif %}
    <footer style="text-align: center; padding: 12px; background-color: #333366; color: #fff; margin-top: 32px;">
        <div>
        <strong>Hack-a-thon project: SafeBite</strong><br>
        Creators: Phil Feng, Nicole Zhang, Jasmine Zhan<br>
        Launched on: 4/28/2025<br>
        </div>
    </footer>

</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
# To run the app, save this code in a file named `app.py` and run it using the command:
# python app.py
