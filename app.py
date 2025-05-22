import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import streamlit as st
import webbrowser

class TasteOfHomeCrawler:
    def __init__(self):
        self.base_url = "https://www.tasteofhome.com"
        self.recipes = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def get_hardcoded_links(self):
        """Return the hardcoded recipe links you provided"""
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
        """Scrape individual recipe details"""
        try:
            full_url = url if url.startswith('http') else self.base_url + url
            response = requests.get(full_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract recipe title - try multiple selectors
            title = "No title"
            title_elem = soup.find('h1', class_='recipe-title') or soup.find('h1', class_='entry-title') or soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Ingredients - try multiple selectors
            ingredients = []
            ingredients_section = (soup.find('ul', class_='recipe-ingredients__list') or 
                                 soup.find('div', class_='recipe-ingredients') or
                                 soup.find('div', class_='ingredients'))
            
            if ingredients_section:
                ingredients = [li.get_text(strip=True) for li in ingredients_section.find_all('li')]
            
            # Directions - try multiple selectors
            directions = []
            directions_section = (soup.find('ul', class_='recipe-directions__list') or 
                                 soup.find('div', class_='recipe-directions') or
                                 soup.find('div', class_='directions'))
            
            if directions_section:
                directions = [li.get_text(strip=True) for li in directions_section.find_all('li')]
                if not directions:  # If no li tags, try getting paragraphs
                    directions = [p.get_text(strip=True) for p in directions_section.find_all('p') if p.get_text(strip=True)]
            
            # Additional info - try multiple selectors
            prep_time = "N/A"
            prep_elem = soup.find('div', class_='prep-time') or soup.find('span', class_='prep-time')
            if prep_elem:
                prep_time = prep_elem.get_text(strip=True)
            
            cook_time = "N/A"
            cook_elem = soup.find('div', class_='cook-time') or soup.find('span', class_='cook-time')
            if cook_elem:
                cook_time = cook_elem.get_text(strip=True)
            
            servings = "N/A"
            servings_elem = soup.find('div', class_='servings') or soup.find('span', class_='servings')
            if servings_elem:
                servings = servings_elem.get_text(strip=True)
            
            return {
                'title': title,
                'url': full_url,
                'ingredients': "\n".join(ingredients),
                'directions': "\n".join(directions),
                'prep_time': prep_time,
                'cook_time': cook_time,
                'servings': servings
            }
        except Exception as e:
            st.error(f"Error scraping recipe {url}: {e}")
            return None
    
    def crawl(self, num_recipes=10):
        """Main crawling function using hardcoded links"""
        self.recipes = []
        links = self.get_hardcoded_links()[:num_recipes]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, link in enumerate(links):
            status_text.text(f"Scraping recipe {i+1}/{len(links)}...")
            recipe = self.scrape_recipe(link)
            if recipe:
                self.recipes.append(recipe)
            progress_bar.progress((i + 1) / len(links))
            time.sleep(random.uniform(1, 3))  # Polite delay
        
        status_text.text(f"Done! Fetched {len(self.recipes)} recipes")
        return self.recipes
    
    def save_to_csv(self, filename="tasteofhome_recipes.csv"):
        """Save recipes to CSV"""
        if not self.recipes:
            st.warning("No recipes to save")
            return False
        
        df = pd.DataFrame(self.recipes)
        df.to_csv(filename, index=False)
        return True

def main():
    st.title("Taste of Home Recipe Crawler")
    
    crawler = TasteOfHomeCrawler()
    
    num_recipes = st.slider("Number of recipes to fetch (max 10):", 1, 10, 10)
    
    if st.button("Start Crawling"):
        recipes = crawler.crawl(num_recipes)
        
        if recipes:
            st.success(f"Successfully fetched {len(recipes)} recipes!")
            
            # Display recipes in a table
            st.subheader("Recipes Overview")
            df = pd.DataFrame(recipes)
            st.dataframe(df[['title', 'prep_time', 'cook_time', 'servings']])
            
            # Allow viewing details of each recipe
            st.subheader("Recipe Details")
            selected_recipe = st.selectbox("Select a recipe to view details:", [r['title'] for r in recipes])
            
            if selected_recipe:
                recipe = next((r for r in recipes if r['title'] == selected_recipe), None)
                if recipe:
                    st.write(f"### {recipe['title']}")
                    st.write(f"**URL:** [{recipe['url']}]({recipe['url']})")
                    st.write(f"**Prep Time:** {recipe['prep_time']}")
                    st.write(f"**Cook Time:** {recipe['cook_time']}")
                    st.write(f"**Servings:** {recipe['servings']}")
                    
                    st.write("#### Ingredients")
                    st.text(recipe['ingredients'])
                    
                    st.write("#### Directions")
                    st.text(recipe['directions'])
    
    if st.button("Save to CSV"):
        if crawler.save_to_csv():
            st.success("Recipes saved to 'tasteofhome_recipes.csv'")
            with open("tasteofhome_recipes.csv", "rb") as f:
                st.download_button(
                    label="Download CSV",
                    data=f,
                    file_name="tasteofhome_recipes.csv",
                    mime="text/csv"
                )
        else:
            st.warning("No recipes were available to save")

if __name__ == "__main__":
    main()