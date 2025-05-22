import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import streamlit as st

# -----------------------
# Cached scraping function (must be outside the class)
# -----------------------
@st.cache_data(show_spinner=False)
def scrape_recipe(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Title
        title_elem = soup.find('h1', class_='recipe-title') or soup.find('h1', class_='entry-title') or soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else "No title"

        # Ingredients
        ingredients = []
        ingredients_section = soup.find('ul', class_='recipe-ingredients__list') or \
                              soup.find('div', class_='recipe-ingredients') or \
                              soup.find('div', class_='ingredients')
        if ingredients_section:
            ingredients = [li.get_text(strip=True) for li in ingredients_section.find_all('li')]
            if not ingredients:
                ingredients = [span.get_text(strip=True) for span in ingredients_section.find_all('span')]

        # Directions
        directions = []
        directions_section = soup.find('ul', class_='recipe-directions__list') or \
                             soup.find('div', class_='recipe-directions') or \
                             soup.find('div', class_='directions')
        if directions_section:
            directions = [li.get_text(strip=True) for li in directions_section.find_all('li')]
            if not directions:
                directions = [p.get_text(strip=True) for p in directions_section.find_all('p') if p.get_text(strip=True)]

        # Prep Time
        prep_time = "N/A"
        prep_elem = soup.find('div', class_='prep-time') or soup.find('span', class_='prep-time')
        if prep_elem:
            prep_time = prep_elem.get_text(strip=True)

        # Cook Time
        cook_time = "N/A"
        cook_elem = soup.find('div', class_='cook-time') or soup.find('span', class_='cook-time')
        if cook_elem:
            cook_time = cook_elem.get_text(strip=True)

        # Servings
        servings = "N/A"
        servings_elem = soup.find('div', class_='servings') or soup.find('span', class_='servings')
        if servings_elem:
            servings = servings_elem.get_text(strip=True)

        # Image
        image_elem = soup.find('img', class_='primary-image') or soup.find('img')
        image_url = image_elem['src'] if image_elem and 'src' in image_elem.attrs else None

        return {
            'title': title,
            'url': url,
            'ingredients': "\n".join(ingredients),
            'directions': "\n".join(directions),
            'prep_time': prep_time,
            'cook_time': cook_time,
            'servings': servings,
            'image_url': image_url
        }

    except Exception as e:
        st.error(f"Error scraping recipe {url}: {e}")
        return None


# -----------------------
# Main crawler class
# -----------------------
class TasteOfHomeCrawler:
    def __init__(self):
        self.base_url = "https://www.tasteofhome.com"
        self.recipes = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_hardcoded_links(self):
        return [
            "https://www.tasteofhome.com/recipes/favorite-chicken-potpie/",
            "https://www.tasteofhome.com/recipes/puff-pastry-chicken-potpie/",
            "https://www.tasteofhome.com/recipes/chicken-potpie-soup/",
            "https://www.tasteofhome.com/recipes/homemade-chicken-potpie/",
            "https://www.tasteofhome.com/recipes/ham-potpie/",
            "https://www.tasteofhome.com/recipes/buttermilk-biscuit-ham-potpie/",
            "https://www.tasteofhome.com/recipes/buttermilk-biscuits/",
            "https://www.tasteofhome.com/recipes/buttermilk-pancakes/",
            "https://www.tasteofhome.com/recipes/buttermilk-chocolate-cupcakes/",
            "https://www.tasteofhome.com/recipes/orange-buttermilk-cupcakes/"
        ]

    def crawl(self, num_recipes=10):
        self.recipes = []
        links = self.get_hardcoded_links()[:num_recipes]

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, link in enumerate(links):
            status_text.text(f"Scraping recipe {i+1}/{len(links)}...")
            recipe = scrape_recipe(link, self.headers)
            if recipe:
                self.recipes.append(recipe)
            progress_bar.progress((i + 1) / len(links))
            time.sleep(random.uniform(1, 2))  # Polite delay

        status_text.text(f"Done! Fetched {len(self.recipes)} recipes.")
        return self.recipes

    def save_to_csv(self, filename="tasteofhome_recipes.csv"):
        if not self.recipes:
            st.warning("No recipes to save.")
            return False
        df = pd.DataFrame(self.recipes)
        df.to_csv(filename, index=False)
        return True


# -----------------------
# Streamlit App
# -----------------------
def main():
    st.set_page_config(page_title="Taste of Home Recipe Crawler", layout="wide")
    st.title("🥧 Taste of Home Recipe Crawler")

    crawler = TasteOfHomeCrawler()
    num_recipes = st.slider("Number of recipes to fetch (max 10):", 1, 10, 5)

    if st.button("Start Crawling"):
        recipes = crawler.crawl(num_recipes)
        if recipes:
            st.success(f"Fetched {len(recipes)} recipes successfully!")

            df = pd.DataFrame(recipes)
            st.subheader("📋 Recipes Overview")
            st.dataframe(df[['title', 'prep_time', 'cook_time', 'servings']])

            st.subheader("🔍 Recipe Details")
            selected_title = st.selectbox("Choose a recipe to view details:", [r['title'] for r in recipes])
            selected_recipe = next((r for r in recipes if r['title'] == selected_title), None)

            if selected_recipe:
                st.markdown(f"### {selected_recipe['title']}")
                if selected_recipe['image_url']:
                    st.image(selected_recipe['image_url'], use_container_width=True)
                st.markdown(f"**URL**: [{selected_recipe['url']}]({selected_recipe['url']})")
                st.markdown(f"**Prep Time:** {selected_recipe['prep_time']}")
                st.markdown(f"**Cook Time:** {selected_recipe['cook_time']}")
                st.markdown(f"**Servings:** {selected_recipe['servings']}")

                st.markdown("#### 🧂 Ingredients")
                st.text(selected_recipe['ingredients'])

                st.markdown("#### 🍳 Directions")
                st.text(selected_recipe['directions'])

    if st.button("Save to CSV"):
        if crawler.save_to_csv():
            st.success("Saved to 'tasteofhome_recipes.csv'.")
            with open("tasteofhome_recipes.csv", "rb") as f:
                st.download_button(
                    label="📥 Download CSV",
                    data=f,
                    file_name="tasteofhome_recipes.csv",
                    mime="text/csv"
                )
        else:
            st.warning("No data available to save.")

if __name__ == "__main__":
    main()
