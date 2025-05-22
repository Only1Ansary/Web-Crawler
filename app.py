import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import streamlit as st
import feedparser # For RSS feeds
from urllib.parse import urljoin # For joining relative URLs

# Selenium imports for JS handling (optional, only if JS rendering is used)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

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

    def _parse_soup_for_recipe(self, soup, full_url):
        """Helper function to extract recipe details from a BeautifulSoup soup object."""
        try:
            title = soup.find('h1') or soup.find('h1', class_='entry-title')
            title = title.get_text(strip=True) if title else "No title found"

            ingredients = []
            ingredients_section = soup.find('ul', class_='recipe-ingredients__list') or \
                                  soup.find('div', class_='recipe-ingredients') or \
                                  soup.find('div', class_='ingredients')
            if ingredients_section:
                ingredients = [li.get_text(strip=True) for li in ingredients_section.find_all('li') if li.get_text(strip=True)]

            directions = []
            directions_section = soup.find('ul', class_='recipe-directions__list') or \
                                 soup.find('div', class_='recipe-directions') or \
                                 soup.find('div', class_='directions')
            if directions_section:
                directions_items = directions_section.find_all(['li', 'p']) # Common tags for directions
                directions = [item.get_text(strip=True) for item in directions_items if item.get_text(strip=True)]


            prep_time_el = soup.find('div', class_='prep-time') or soup.find('span', class_='prep-time') or \
                           soup.find(attrs={"data-label": "Prep Time:"}) or soup.find(string=lambda text: "Prep:" in text if text else False)
            prep_time = prep_time_el.get_text(strip=True).replace("Prep: ", "") if prep_time_el else "N/A"
            if prep_time == "N/A" and prep_time_el: # Try to get next element if it's just a label
                next_sibling = prep_time_el.find_next_sibling()
                if next_sibling: prep_time = next_sibling.get_text(strip=True)


            cook_time_el = soup.find('div', class_='cook-time') or soup.find('span', class_='cook-time') or \
                           soup.find(attrs={"data-label": "Cook Time:"}) or soup.find(string=lambda text: "Cook:" in text if text else False)
            cook_time = cook_time_el.get_text(strip=True).replace("Cook: ", "") if cook_time_el else "N/A"
            if cook_time == "N/A" and cook_time_el:
                next_sibling = cook_time_el.find_next_sibling()
                if next_sibling: cook_time = next_sibling.get_text(strip=True)


            servings_el = soup.find('div', class_='servings') or soup.find('span', class_='servings') or \
                          soup.find(attrs={"data-label": "Servings:"}) or soup.find(string=lambda text: "Yield:" in text if text else False)
            servings = servings_el.get_text(strip=True).replace("Yield: ", "") if servings_el else "N/A"
            if servings == "N/A" and servings_el:
                next_sibling = servings_el.find_next_sibling()
                if next_sibling: servings = next_sibling.get_text(strip=True)

            image_url = ""
            image_tag = soup.find('img', class_='primary-image') or \
                        soup.find('div', class_='recipe-image-wrap rd_images_load') # Common class observed
            if image_tag:
                img_src_tag = image_tag.find('img') if image_tag.name == 'div' else image_tag
                if img_src_tag:
                    image_url = img_src_tag.get("src", "") or img_src_tag.get("data-src", "") # Check data-src for lazy loading
                    if image_url and not image_url.startswith('http'):
                        image_url = urljoin(full_url, image_url)

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
            st.warning(f"Error parsing content for {full_url}: {e}")
            return { # Return with N/A to avoid breaking the process for one bad parse
                'title': "Parsing Error", 'url': full_url, 'ingredients': "N/A", 'directions': "N/A",
                'prep_time': "N/A", 'cook_time': "N/A", 'servings': "N/A", 'image_url': ""
            }

    def scrape_recipe_js(self, url, driver_path):
        if not SELENIUM_AVAILABLE:
            st.error("Selenium library is not available. Please install it.")
            return None
        if not driver_path:
            st.error("ChromeDriver path is not provided for JavaScript rendering.")
            return None

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox') # Important for some environments
        options.add_argument('--disable-dev-shm-usage') # Important for some environments
        options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        
        service = Service(executable_path=driver_path)
        driver = None
        try:
            driver = webdriver.Chrome(service=service, options=options)
            full_url = url if url.startswith('http') else self.base_url + url
            driver.get(full_url)
            
            # Wait for a general element that indicates page load, e.g., recipe title or ingredients list
            # Adjust timeout and selector as needed for the specific site
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1, .recipe-ingredients__list, .recipe-directions__list"))
            )
            # Allow a bit more time for any lazy-loaded content or JS hydration
            time.sleep(random.uniform(2, 4)) # Adjust as needed

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            return self._parse_soup_for_recipe(soup, full_url)

        except Exception as e:
            st.error(f"Error scraping {url} with JS: {e}")
            return None
        finally:
            if driver:
                driver.quit()

    def scrape_recipe(self, url, use_js=False, driver_path=None):
        full_url = url if url.startswith('http') else self.base_url + url

        if use_js:
            return self.scrape_recipe_js(full_url, driver_path)
        
        try:
            response = requests.get(full_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_soup_for_recipe(soup, full_url)

        except requests.exceptions.RequestException as e:
            st.error(f"Request error scraping {full_url}: {e}")
            return None
        except Exception as e: # Catch other parsing errors if any slip through _parse_soup_for_recipe
            st.error(f"General error scraping {full_url}: {e}")
            return None


    def fetch_links_from_rss(self, rss_url):
        st.info(f"Fetching links from RSS: {rss_url}")
        try:
            feed = feedparser.parse(rss_url)
            if feed.bozo:
                st.error(f"Error parsing RSS feed (possibly malformed): {feed.bozo_exception}")
                return []
            
            links = [entry.link for entry in feed.entries if hasattr(entry, 'link')]
            if not links:
                st.warning(f"No recipe links found in RSS feed: {rss_url}")
            else:
                st.success(f"Found {len(links)} links in RSS feed.")
            return links
        except Exception as e:
            st.error(f"Could not fetch or parse RSS feed {rss_url}: {e}")
            return []

    def fetch_recipes_from_api(self, api_endpoint): # Conceptual
        st.info(f"Attempting to fetch from API: {api_endpoint} (This is a conceptual placeholder)")
        # This is a placeholder. Real API interaction would require:
        # 1. Knowing the API's request format (params, headers, auth)
        # 2. Knowing the API's response structure (JSON, XML)
        # 3. Parsing the response to fit the common recipe dictionary format.
        try:
            # response = requests.get(api_endpoint, headers=self.headers, ...)
            # response.raise_for_status()
            # api_data = response.json() # Assuming JSON
            # recipes_from_api = []
            # for item in api_data.get('recipes', []): # Example structure
            #     recipe_data = {
            #         'title': item.get('title'),
            #         'url': item.get('source_url'), # URL to the actual recipe page if API gives summaries
            #         'ingredients': "\n".join(item.get('ingredientLines', [])),
            #         'directions': item.get('instructions'),
            #         'prep_time': item.get('prepTime'),
            #         'cook_time': item.get('cookTime'),
            #         'servings': item.get('yield'),
            #         'image_url': item.get('image')
            #     }
            #     recipes_from_api.append(recipe_data)
            # st.success(f"Fetched {len(recipes_from_api)} items from API.")
            # return recipes_from_api
            st.warning("API fetching is not implemented for this website as no public recipe API is known.")
            return [] # Return empty list as it's a placeholder
        except Exception as e:
            st.error(f"Error fetching from API {api_endpoint}: {e}")
            return []

    def crawl(self, num_items=10, source_type="hardcoded", source_input=None, use_js=False, driver_path=None):
        links_to_scrape = []
        direct_recipes = [] # For APIs that might return full data

        if source_type == "hardcoded":
            links_to_scrape = self.get_hardcoded_links()[:num_items]
        elif source_type == "rss":
            if source_input:
                links_to_scrape = self.fetch_links_from_rss(source_input)[:num_items]
            else:
                st.warning("RSS URL not provided.")
                return []
        elif source_type == "api":
            if source_input:
                # This is conceptual. If API returns full data, direct_recipes would be populated.
                # If API returns links, links_to_scrape would be populated.
                direct_recipes = self.fetch_recipes_from_api(source_input) # Placeholder
                # For this example, we'll assume API gives full data and doesn't need further scraping
                if direct_recipes:
                     st.success(f"Conceptual API returned {len(direct_recipes)} direct recipes.")
                     return direct_recipes[:num_items] # Return directly if API provides full data
                else:
                    st.info("Conceptual API did not return direct recipes or is not implemented.")
                    return []
            else:
                st.warning("API endpoint not provided.")
                return []
        
        scraped_recipes = []
        if not links_to_scrape:
            if source_type not in ["api"]: # API might not produce links if it's meant to give data directly
                 st.info("No links to process for scraping.")
            return scraped_recipes # or direct_recipes if API was the source and returned data

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, link in enumerate(links_to_scrape):
            status_text.text(f"Scraping recipe {i + 1}/{len(links_to_scrape)}: {link}")
            recipe = self.scrape_recipe(link, use_js=use_js, driver_path=driver_path)
            if recipe:
                # Basic validation: ensure at least a title was found
                if recipe.get('title') and recipe.get('title') != "Parsing Error" and recipe.get('title') != "No title found":
                    scraped_recipes.append(recipe)
                elif recipe.get('title') == "Parsing Error":
                     st.warning(f"Skipping recipe due to parsing error: {link}")
                else:
                    st.warning(f"Skipping recipe with missing title: {link}")

            progress_bar.progress((i + 1) / len(links_to_scrape))
            # Ensure politeness even if JS scraping introduces its own waits
            time.sleep(random.uniform(0.5, 1.5)) 

        if not scraped_recipes:
            status_text.text("No recipes were successfully scraped.")
        else:
            status_text.text(f"Scraping complete. Fetched {len(scraped_recipes)} recipes.")
        return scraped_recipes

def main():
    st.set_page_config(page_title="Recipe Crawler", layout="wide")
    st.title("\U0001F967 Universal Recipe Crawler")
    st.markdown("Fetches recipes from 'Taste of Home' or other sources via links, RSS, or (conceptually) an API.")

    crawler = TasteOfHomeCrawler()

    if "recipes" not in st.session_state:
        st.session_state.recipes = []

    # Sidebar for controls
    st.sidebar.header("\U0001F527 Crawler Configuration")
    source_type_display = st.sidebar.selectbox(
        "Choose data source:",
        ("Hardcoded TasteOfHome Links", "RSS Feed", "API (Conceptual)")
    )

    source_input_val = None
    source_type_arg = "hardcoded"

    if source_type_display == "RSS Feed":
        source_type_arg = "rss"
        source_input_val = st.sidebar.text_input(
            "Enter RSS Feed URL:", 
            "https://www.tasteofhome.com/collection/top-10-chicken-recipes/feed/" # Example
        )
    elif source_type_display == "API (Conceptual)":
        source_type_arg = "api"
        source_input_val = st.sidebar.text_input("Enter API Endpoint URL (conceptual):")

    num_items_label = "Number of recipes from hardcoded list:" if source_type_arg == "hardcoded" else "Max recipes/links to process from source:"
    num_items = st.sidebar.slider(num_items_label, 1, 25, 10)

    use_js_scraping = False
    chromedriver_path_input = None

    if SELENIUM_AVAILABLE:
        st.sidebar.markdown("---")
        st.sidebar.subheader("JavaScript Rendering (Advanced)")
        use_js_scraping = st.sidebar.checkbox("Enable JS Rendering (Slower, requires ChromeDriver)")
        if use_js_scraping:
            chromedriver_path_input = st.sidebar.text_input(
                "Path to ChromeDriver executable:",
                help="e.g., C:\\path\\to\\chromedriver.exe or /usr/local/bin/chromedriver. Ensure it matches your Chrome version."
            )
            if not chromedriver_path_input:
                st.sidebar.warning("ChromeDriver path is required for JS rendering.")
            else:
                st.sidebar.caption(f"Using ChromeDriver from: {chromedriver_path_input}")
    else:
        st.sidebar.markdown("---")
        st.sidebar.info("Selenium library not detected. JS rendering is disabled. Install Selenium to enable this feature.")


    if st.sidebar.button("\U0001F50D Start Crawling", key="start_crawl_button"):
        st.session_state.recipes = [] # Clear previous results
        
        if use_js_scraping and not chromedriver_path_input:
            st.error("JavaScript rendering is enabled, but ChromeDriver path is missing.")
        else:
            with st.spinner("Crawling in progress... Please wait."):
                st.session_state.recipes = crawler.crawl(
                    num_items=num_items,
                    source_type=source_type_arg,
                    source_input=source_input_val,
                    use_js=use_js_scraping,
                    driver_path=chromedriver_path_input
                )
                if st.session_state.recipes:
                    st.success(f"Successfully fetched {len(st.session_state.recipes)} recipes.")
                else:
                    st.info("No recipes were fetched. Check settings, logs, or source URL.")
    
    # Display recipes
    recipes_to_display = st.session_state.recipes

    if recipes_to_display:
        st.subheader(f"\U0001F4CB Fetched Recipes ({len(recipes_to_display)})")
        
        # Filter out recipes that might have had parsing errors but still got through
        valid_recipes = [r for r in recipes_to_display if r.get('title') and r['title'] not in ["Parsing Error", "No title found"]]

        if not valid_recipes:
            st.warning("No valid recipes to display after filtering.")
        else:
            df = pd.DataFrame(valid_recipes)
            display_cols = ['title', 'prep_time', 'cook_time', 'servings']
            existing_display_cols = [col for col in display_cols if col in df.columns]
            
            if existing_display_cols:
                st.dataframe(df[existing_display_cols], use_container_width=True)
            else:
                st.warning("Key columns for overview are missing in the fetched data.")

            st.markdown("---")
            st.subheader("\U0001F50D Recipe Details")
            
            # Ensure titles are unique for selectbox or handle duplicates if any
            recipe_titles = [r['title'] for r in valid_recipes]
            
            if not recipe_titles:
                st.info("No recipe titles available for selection.")
            else:
                # Handle potential duplicate titles for selectbox by appending index temporarily
                unique_selection_titles = []
                title_counts = {}
                for r_title in recipe_titles:
                    if r_title in title_counts:
                        title_counts[r_title] += 1
                        unique_selection_titles.append(f"{r_title} ({title_counts[r_title]})")
                    else:
                        title_counts[r_title] = 0 # 0 for the first one, so it doesn't get (0)
                        unique_selection_titles.append(r_title)
                
                # Map display title back to original recipe index
                selected_display_title = st.selectbox(
                    "Select a recipe to view details:", 
                    unique_selection_titles,
                    index=0 if unique_selection_titles else None
                )

                selected_recipe = None
                if selected_display_title:
                    original_title_to_find = selected_display_title
                    # If it was a duplicate, strip the counter " (count)"
                    if " (" in selected_display_title and selected_display_title.endswith(")"):
                        original_title_to_find = selected_display_title.rsplit(" (", 1)[0]

                    # Find the correct recipe matching the potentially de-duplicated title
                    current_occurrence = 0
                    target_occurrence = 0
                    if " (" in selected_display_title and selected_display_title.endswith(")"):
                        try:
                            target_occurrence = int(selected_display_title.rsplit(" (", 1)[1][:-1])
                        except ValueError:
                            pass # Not a numbered duplicate
                    
                    for idx, r in enumerate(valid_recipes):
                        if r['title'] == original_title_to_find:
                            if current_occurrence == target_occurrence:
                                selected_recipe = r
                                break
                            current_occurrence += 1
                
                if selected_recipe:
                    col1, col2 = st.columns([2,3])
                    with col1:
                        if selected_recipe.get('image_url'):
                            st.image(selected_recipe['image_url'], caption=selected_recipe['title'], use_container_width=True)
                        else:
                            st.markdown("*No image available.*")
                        st.markdown(f"**URL**: [{selected_recipe['title']}]({selected_recipe['url']})")
                        st.markdown(f"**Prep Time**: {selected_recipe.get('prep_time', 'N/A')}")
                        st.markdown(f"**Cook Time**: {selected_recipe.get('cook_time', 'N/A')}")
                        st.markdown(f"**Servings**: {selected_recipe.get('servings', 'N/A')}")
                    
                    with col2:
                        st.markdown(f"### {selected_recipe['title']}")
                        st.markdown("#### \U0001F958 Ingredients") # Changed emoji
                        st.text_area("", selected_recipe.get('ingredients', 'N/A'), height=200, key=f"ing_{selected_recipe['title']}")
                        st.markdown("#### \U0001F4DC Directions") # Changed emoji
                        st.text_area("", selected_recipe.get('directions', 'N/A'), height=300, key=f"dir_{selected_recipe['title']}")
                else:
                    st.info("Select a recipe to see its details.")
    else:
        st.info("No recipes loaded. Configure and click 'Start Crawling' in the sidebar.")

    # Export results (Save to CSV)
    st.sidebar.markdown("---")
    st.sidebar.subheader("\U0001F4BE Export")
    if recipes_to_display: # Only show button if there are recipes
        if st.sidebar.button("\U0001F4C2 Save Displayed Recipes to CSV", key="save_csv_button"):
            valid_recipes_to_save = [r for r in recipes_to_display if r.get('title') and r['title'] not in ["Parsing Error", "No title found"]]
            if valid_recipes_to_save:
                df_to_save = pd.DataFrame(valid_recipes_to_save)
                csv_file_name = "recipes_export.csv"
                try:
                    csv_data = df_to_save.to_csv(index=False).encode('utf-8')
                    st.sidebar.download_button(
                        label="\U0001F4E5 Download CSV File",
                        data=csv_data,
                        file_name=csv_file_name,
                        mime="text/csv",
                    )
                    st.sidebar.success(f"CSV prepared for download as `{csv_file_name}`.")
                except Exception as e:
                    st.sidebar.error(f"Failed to create CSV: {e}")
            else:
                st.sidebar.warning("No valid recipes to save.")
    else:
        st.sidebar.button("\U0001F4C2 Save Displayed Recipes to CSV", disabled=True, key="save_csv_button_disabled")

if __name__ == "__main__":
    main()