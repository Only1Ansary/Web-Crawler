import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import streamlit as st

class TasteOfHomeCrawler:
    def __init__(self):
        self.base_url = "https://www.tasteofhome.com"
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

    def scrape_recipe(self, url):
        try:
            full_url = url if url.startswith('http') else self.base_url + url
            response = requests.get(full_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            title = soup.find('h1') or soup.find('h1', class_='entry-title')
            title = title.get_text(strip=True) if title else "No title"

            ingredients = []
            ingredients_section = soup.find('ul', class_='recipe-ingredients__list') or \
                                  soup.find('div', class_='recipe-ingredients') or \
                                  soup.find('div', class_='ingredients')
            if ingredients_section:
                ingredients = [li.get_text(strip=True) for li in ingredients_section.find_all('li')]

            directions = []
            directions_section = soup.find('ul', class_='recipe-directions__list') or \
                                 soup.find('div', class_='recipe-directions') or \
                                 soup.find('div', class_='directions')
            if directions_section:
                directions = [li.get_text(strip=True) for li in directions_section.find_all('li')]
                if not directions:
                    directions = [p.get_text(strip=True) for p in directions_section.find_all('p') if p.get_text(strip=True)]

            prep_time = soup.find('div', class_='prep-time') or soup.find('span', class_='prep-time')
            cook_time = soup.find('div', class_='cook-time') or soup.find('span', class_='cook-time')
            servings = soup.find('div', class_='servings') or soup.find('span', class_='servings')

            image_url = ""
            image_tag = soup.find('img', class_='primary-image') or soup.find('img', class_='attachment-full')
            if image_tag:
                image_url = image_tag.get("src", "")

            return {
                'title': title,
                'url': full_url,
                'ingredients': "\n".join(ingredients),
                'directions': "\n".join(directions),
                'prep_time': prep_time.get_text(strip=True) if prep_time else "N/A",
                'cook_time': cook_time.get_text(strip=True) if cook_time else "N/A",
                'servings': servings.get_text(strip=True) if servings else "N/A",
                'image_url': image_url
            }

        except Exception as e:
            st.error(f"Error scraping {url}: {e}")
            return None

    def crawl(self, num_recipes=10):
        links = self.get_hardcoded_links()[:num_recipes]
        recipes = []

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, link in enumerate(links):
            status_text.text(f"Scraping recipe {i + 1}/{len(links)}...")
            recipe = self.scrape_recipe(link)
            if recipe:
                recipes.append(recipe)
            progress_bar.progress((i + 1) / len(links))
            time.sleep(random.uniform(1, 2))

        status_text.text("Done!")
        return recipes


def main():
    st.set_page_config(page_title="Taste of Home Crawler", layout="wide")
    st.title("🥧 Taste of Home Recipe Crawler")

    crawler = TasteOfHomeCrawler()

    if "recipes" not in st.session_state:
        st.session_state.recipes = []

    num_recipes = st.slider("Number of recipes to fetch (max 10):", 1, 10, 10)

    if st.button("Start Crawling"):
        with st.spinner("Crawling recipes..."):
            st.session_state.recipes = crawler.crawl(num_recipes)
            st.success(f"Fetched {len(st.session_state.recipes)} recipes.")

    recipes = st.session_state.recipes

    if recipes:
        df = pd.DataFrame(recipes)
        st.subheader("📋 Recipes Overview")
        st.dataframe(df[['title', 'prep_time', 'cook_time', 'servings']], use_container_width=True)

        st.subheader("🔍 Recipe Details")
        selected_title = st.selectbox("Select a recipe:", [r['title'] for r in recipes])
        selected_recipe = next((r for r in recipes if r['title'] == selected_title), None)

        if selected_recipe:
            st.markdown(f"### {selected_recipe['title']}")
            st.markdown(f"**URL**: [{selected_recipe['url']}]({selected_recipe['url']})")
            st.markdown(f"**Prep Time**: {selected_recipe['prep_time']}")
            st.markdown(f"**Cook Time**: {selected_recipe['cook_time']}")
            st.markdown(f"**Servings**: {selected_recipe['servings']}")

            if selected_recipe['image_url']:
                st.image(selected_recipe['image_url'], use_container_width=True)

            st.markdown("#### 🥄 Ingredients")
            st.text(selected_recipe['ingredients'])

            st.markdown("#### 🍳 Directions")
            st.text(selected_recipe['directions'])

    if st.button("Save to CSV"):
        if recipes:
            df = pd.DataFrame(recipes)
            csv_file = "tasteofhome_recipes.csv"
            df.to_csv(csv_file, index=False)
            st.success(f"Recipes saved to `{csv_file}`")

            with open(csv_file, "rb") as f:
                st.download_button("📥 Download CSV", data=f, file_name=csv_file, mime="text/csv")
        else:
            st.warning("No recipes to save.")


if __name__ == "__main__":
    main()
