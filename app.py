import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from tkinter import *
from tkinter import ttk, messagebox
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
            print(f"Error scraping recipe {url}: {e}")
            return None
    
    def crawl(self, num_recipes=10):
        """Main crawling function using hardcoded links"""
        self.recipes = []
        links = self.get_hardcoded_links()[:num_recipes]
        
        for i, link in enumerate(links):
            print(f"Scraping recipe {i+1}/{len(links)}...")
            recipe = self.scrape_recipe(link)
            if recipe:
                self.recipes.append(recipe)
            time.sleep(random.uniform(1, 3))  # Polite delay
            
        return self.recipes
    
    def save_to_csv(self, filename="tasteofhome_recipes.csv"):
        """Save recipes to CSV"""
        if not self.recipes:
            print("No recipes to save")
            return False
        
        df = pd.DataFrame(self.recipes)
        df.to_csv(filename, index=False)
        return True

# باقي الكود الخاص بواجهة المستخدم يبقى كما هو بدون تغيير
class RecipeCrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Taste of Home Recipe Crawler")
        self.root.geometry("800x600")
        self.crawler = TasteOfHomeCrawler()
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=BOTH, expand=True)
        
        # Header
        ttk.Label(main_frame, text="Taste of Home Recipe Crawler", font=('Helvetica', 16, 'bold')).pack(pady=10)
        
        # Controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=X, pady=10)
        
        ttk.Label(controls_frame, text="Number of recipes to fetch (max 10):").pack(side=LEFT, padx=5)
        self.num_recipes = IntVar(value=10)
        ttk.Spinbox(controls_frame, from_=1, to=10, textvariable=self.num_recipes, width=5).pack(side=LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Start Crawling", command=self.start_crawling).pack(side=LEFT, padx=10)
        ttk.Button(controls_frame, text="Save to CSV", command=self.save_recipes).pack(side=LEFT, padx=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, orient=HORIZONTAL, mode='determinate')
        self.progress.pack(fill=X, pady=5)
        self.progress_label = ttk.Label(main_frame, text="Ready")
        self.progress_label.pack()
        
        # Results frame
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=BOTH, expand=True, pady=10)
        
        # Treeview for recipes
        self.tree = ttk.Treeview(results_frame, columns=('title', 'prep_time', 'cook_time', 'servings'), show='headings')
        self.tree.heading('title', text='Recipe Title')
        self.tree.heading('prep_time', text='Prep Time')
        self.tree.heading('cook_time', text='Cook Time')
        self.tree.heading('servings', text='Servings')
        
        self.tree.column('title', width=300)
        self.tree.column('prep_time', width=100)
        self.tree.column('cook_time', width=100)
        self.tree.column('servings', width=100)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Details frame
        details_frame = ttk.Frame(main_frame)
        details_frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(details_frame, text="Recipe Details", font=('Helvetica', 12, 'bold')).pack(anchor=W)
        
        self.details_text = Text(details_frame, wrap=WORD, height=10)
        self.details_text.pack(fill=BOTH, expand=True)
        
        # Bind tree selection
        self.tree.bind('<<TreeviewSelect>>', self.show_recipe_details)
        
    def start_crawling(self):
        self.progress['value'] = 0
        self.progress_label.config(text="Starting...")
        self.root.update()
        
        # Clear previous results
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.details_text.delete(1.0, END)
        
        num_recipes = self.num_recipes.get()
        
        try:
            recipes = self.crawler.crawl(num_recipes)
            
            # Update progress
            self.progress['maximum'] = len(recipes)
            
            for i, recipe in enumerate(recipes):
                self.tree.insert('', 'end', values=(
                    recipe['title'],
                    recipe['prep_time'],
                    recipe['cook_time'],
                    recipe['servings']
                ))
                self.progress['value'] = i + 1
                self.progress_label.config(text=f"Fetched {i+1}/{len(recipes)} recipes")
                self.root.update()
            
            self.progress_label.config(text=f"Done! Fetched {len(recipes)} recipes")
            messagebox.showinfo("Success", f"Successfully fetched {len(recipes)} recipes!")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.progress_label.config(text="Error occurred")
    
    def save_recipes(self):
        if not self.crawler.recipes:
            messagebox.showwarning("Warning", "No recipes to save. Please crawl first.")
            return
        
        try:
            if self.crawler.save_to_csv():
                messagebox.showinfo("Success", "Recipes saved to 'tasteofhome_recipes.csv'")
            else:
                messagebox.showwarning("Warning", "No recipes were available to save")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save recipes: {str(e)}")
    
    def show_recipe_details(self, event):
        selected_item = self.tree.focus()
        if not selected_item:
            return
        
        item_data = self.tree.item(selected_item)
        recipe_title = item_data['values'][0]
        
        # Find the matching recipe
        recipe = next((r for r in self.crawler.recipes if r['title'] == recipe_title), None)
        if not recipe:
            return
        
        # Display details
        self.details_text.delete(1.0, END)
        self.details_text.insert(END, f"Title: {recipe['title']}\n\n")
        self.details_text.insert(END, f"URL: {recipe['url']}\n\n")
        self.details_text.insert(END, f"Prep Time: {recipe['prep_time']}\n")
        self.details_text.insert(END, f"Cook Time: {recipe['cook_time']}\n")
        self.details_text.insert(END, f"Servings: {recipe['servings']}\n\n")
        self.details_text.insert(END, "Ingredients:\n")
        self.details_text.insert(END, recipe['ingredients'] + "\n\n")
        self.details_text.insert(END, "Directions:\n")
        self.details_text.insert(END, recipe['directions'])

def main():
    root = Tk()
    app = RecipeCrawlerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()