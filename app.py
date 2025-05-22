import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import streamlit as st
import datetime

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

    @st.cache_data(show_spinner=False)
    def scrape_recipe(self, url):
        try:
            full_url = url if url.startswith('http') else self.base_url + url
            response = requests.get(full_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            title_elem = soup.find('h1', class_='recipe-title') or soup.find('h1', class_='entry-title') or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "No title"

            ingredients = []
            ingredients_section = soup.find('ul', class_='recipe-ingredients__list') or \
                                  soup.find('div', class_='recipe-ingredients') or \
                                  soup.find('div', class_='ingredients')
            if ingredients_section:
                ingredients = [li.get_text(strip=True) for li in ingredients_section.find_all('li')]
                if not ingredients:
                    ingredients = [span.get_text(strip=True) for span in ingredients_section.find_all('span')]

            directions = []
            directions_section = soup.find('ul', class_='recipe-directions__list') or \
                                 soup.find('div', class_='recipe-directions') or \
                                 soup.find('div', class_='directions')
            if directions_section:
                directions = [li.get_text(strip=True) for li in directions_section.find_all('li')]
                if not directions:
                    directions = [p.get_text(strip=True) for p in directions_section.find_all('p') if p.get_text(strip=True)]

            prep_time = soup.find(text='Prep Time') or soup.find(class_='prep-time')
            prep_time = prep_time.find_next().get_text(strip=True) if prep_time else "N/A"

            cook_time = soup.find(text='Cook Time') or soup.find(class_='cook-time')
            cook_time = cook_time.find_next().get_text(strip=True) if cook_time else "N/A"

            servings = soup.find(text='Servings') or soup.find(class_='servings')
            servings = servings.find_next().get_text(strip=True) if servings else "N/A"

            image_elem = soup.find('img', class_='primary-image') or soup.find('img')
            image_url = image_elem['src'] if image_elem and 'src' in image_elem.attrs else None

            return {
                'title': title,
                'url': full_url,
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

    def crawl(self, num_recipes=10):
        self.recipes = []
        links = self.get_hardcoded_links()[:num_recipes]

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, link in enumerate(links):
            status_text.text(f"Scraping recipe {i + 1}/{len(links)}...")
            recipe = self.scrape_recipe(link)
            if recipe:
                self.recipes.append(recipe)
            progress_bar.progress((i + 1) / len(links))
            time.sleep(random.uniform(1, 2.5))

        status_text.text(f"Done! Fetched {len(self.recipes)} recipes.")
        return self.recipes

    def save_to_csv(self, filename=None):
        if not self.recipes:
            st.warning("No recipes to save.")
            return None

        if not filename:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tasteofhome_recipes_{timestamp}.csv"

        df = pd.DataFrame(self.recipes)
        df.to_csv(filename, index=False)
        return filename


def main():
    st.set_page_config(page_title="Taste of Home Recipe Crawler", layout="centered")
    st.title("🍲 Taste of Home Recipe Crawler")

    crawler = TasteOfHomeCrawler()
    st.markdown("---")
    num_recipes = st.slider("Number of recipes to fetch (max 10):", 1, 10, 5)

    if st.button("Start Crawling"):
        with st.spinner("Scraping recipes..."):
            recipes = crawler.crawl(num_recipes)

        if recipes:
            st.success(f"Successfully fetched {len(recipes)} recipes!")
            st.subheader("📋 Recipes Overview")
            df = pd.DataFrame(recipes)
            st.dataframe(df[['title', 'prep_time', 'cook_time', 'servings']])

            st.markdown("---")
            st.subheader("🔍 Recipe Details")
            selected_title = st.selectbox("Select a recipe to view details:", [r['title'] for r in recipes])

            recipe = next((r for r in recipes if r['title'] == selected_title), None)
            if recipe:
                st.write(f"### {recipe['title']}")
                st.markdown(f"**URL:** [{recipe['url']}]({recipe['url']})")
                st.markdown(f"**Prep Time:** {recipe['prep_time']} &nbsp;&nbsp; **Cook Time:** {recipe['cook_time']} &nbsp;&nbsp; **Servings:** {recipe['servings']}")
                if recipe.get("image_url"):
                    st.image(recipe['image_url'], use_column_width=True)

                st.markdown("#### 🧂 Ingredients")
                st.text(recipe['ingredients'])

                st.markdown("#### 🧑‍🍳 Directions")
                st.text(recipe['directions'])

    st.markdown("---")
    if st.button("💾 Save Recipes to CSV"):
        filename = crawler.save_to_csv()
        if filename:
            st.success(f"Recipes saved to `{filename}`")
            with open(filename, "rb") as f:
                st.download_button("Download CSV File", data=f, file_name=filename, mime="text/csv")


if __name__ == "__main__":
    main()
