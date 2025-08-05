import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd

class InstagramScraperModal:
    def __init__(self, headless=False):
        self.setup_driver(headless)
    
    def setup_driver(self, headless=False):
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if headless:
            options.add_argument('--headless')
        
        options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def login(self, username, password):
        try:
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(random.uniform(3, 5))
            
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_input.send_keys(username)
            time.sleep(random.uniform(1, 2))
            
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(password)
            time.sleep(random.uniform(1, 2))
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(random.uniform(5, 8))
            
            current_url = self.driver.current_url
            if "challenge" in current_url or "login" in current_url:
                print("Login mungkin perlu verifikasi")
                return False
            else:
                print("Login berhasil")
                return True
                
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def go_to_profile_and_select_post(self, username, post_index=0):
        try:
            profile_url = f"https://www.instagram.com/{username}/"
            print(f"Mengakses profile: {profile_url}")
            self.driver.get(profile_url)
            time.sleep(random.uniform(4, 6))
        

            print(f"Current page title: {self.driver.title}")
            print(f"Current URL: {self.driver.current_url}")
        

            post_selectors = [
                "//main//article//div//div//div//div//a[contains(@href, '/p/')]",
                "//article//div//div//div//a[contains(@href, '/p/')]", 
                "//main//article//a[contains(@href, '/p/')]",
                "//div[@class='_ac7v']//a",  
                "//a[contains(@href, '/p/')]"  
            ]
        
            posts = []
            for selector in post_selectors:
                try:
                    posts = self.driver.find_elements(By.XPATH, selector)
                    print(f"Selector: {selector}")
                    print(f"Found {len(posts)} posts")
                    if len(posts) > 0:
                        break
                except Exception as e:
                    print(f"Selector failed: {e}")
                    continue
        
            if len(posts) == 0:
                print("❌ No posts found with any selector!")
    
                with open('debug_profile.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print("Page source saved to debug_profile.html")
                return False
        
            # Click first post
            target_post = posts[post_index]
            print(f"Clicking post {post_index}")
        
   
            post_href = target_post.get_attribute("href")
            print(f"Post URL: {post_href}")
        
            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_post)
            time.sleep(2)
        
            try:
                target_post.click()
                print("✓ Normal click successful")
            except:
                print("Normal click failed, trying JavaScript click...")
                self.driver.execute_script("arguments[0].click();", target_post)
                print("✓ JavaScript click executed")
            
            time.sleep(random.uniform(4, 6))
        
            # Check for modal
            try:
                modal = WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
                )
                print("✓ Modal opened successfully!")
                return True
            except:
                print("❌ Modal not found")
                print(f"Current URL after click: {self.driver.current_url}")
                return False
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def scrape_comments_from_modal(self, max_comments=50):
        try:
            print("Starting comment scraping from modal...")
            comments_data = []
            
            # Scroll untuk load comments di modal
            self.scroll_comments_in_modal(scrolls=5)
            

            modal_selectors = [
                "//div[@role='dialog']//ul//li//div//span[string-length(text()) > 3 and not(ancestor::button)]",
                "//div[@role='dialog']//article//div//span[not(ancestor::button) and not(contains(@class, 'time'))]",
                "//div[@role='dialog']//span[contains(@dir, 'auto') and string-length(text()) > 5 and not(contains(text(), 'Balas'))]",
                "//div[@role='dialog']//div[contains(@class, 'comment')]//span"
            ]
            
            for selector in modal_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    print(f"Testing selector found {len(elements)} elements")
                    
                    valid_count = 0
                    for element in elements[:max_comments]:
                        try:
                            text = element.text.strip()
                            
                            if len(text) < 3:
                                continue
                            
                            # Skip UI elements
                            skip_patterns = [
                                'Balas', 'Reply', 'balasan', 'menit', 'jam', 'hari', 
                                'Lihat semua', 'View all', 'Suka', 'Like', 'Follow',
                                'Ikuti', 'ago', 'min', 'h', 'd', '•', 'Lihat balasan',
                                'Show replies', 'Hide replies'
                            ]
                            
                            skip = False
                            for pattern in skip_patterns:
                                if pattern.lower() in text.lower() and len(text) < 30:
                                    skip = True
                                    break
                            
                            if not skip:
                                # Extract username if possible
                                username = self.extract_username_from_element(element)
                                
                                # Check for duplicates
                                if text not in [c['comment'] for c in comments_data]:
                                    comments_data.append({
                                        'comment': text,
                                        'username': username,
                                        'selector_used': selector
                                    })
                                    valid_count += 1
                                    print(f"✓ Comment {valid_count}: [{username}] {text[:50]}...")
                        
                        except Exception as e:
                            continue
                    
                    print(f"Valid comments from this selector: {valid_count}")
                    
                    if comments_data:
                        print(f"Total unique comments found: {len(comments_data)}")
                        break
                        
                except Exception as e:
                    print(f"Error with selector: {e}")
                    continue
            
            return comments_data
            
        except Exception as e:
            print(f"Error scraping modal: {e}")
            return []
    
    def scroll_comments_in_modal(self, scrolls=5):
        try:
            comment_area_selectors = [
                "//div[@role='dialog']//article//div[contains(@style, 'overflow')]",
                "//div[@role='dialog']//div[contains(@class, 'comment')]//parent::div",
                "//div[@role='dialog']//article//div//div[last()]"  # Area kanan modal
            ]
            
            scroll_target = None
            for selector in comment_area_selectors:
                try:
                    scroll_target = self.driver.find_element(By.XPATH, selector)
                    print(f"Found scroll target with selector: {selector}")
                    break
                except:
                    continue
            
            if not scroll_target:
                # Fallback: scroll di modal secara umum
                scroll_target = self.driver.find_element(By.XPATH, "//div[@role='dialog']")
                print("Using fallback modal scroll")
            
            print("Scrolling di area comments...")
            for i in range(scrolls):
                # Scroll di area yang tepat
                self.driver.execute_script("""
                    arguments[0].scrollTop += 300;
                """, scroll_target)
                
                time.sleep(random.uniform(2, 3))
                print(f"Comment area scroll {i+1}/{scrolls}")
                
        except Exception as e:
            print(f"Scroll error: {e}")
    
    def extract_username_from_element(self, element):
        try:
            parent = element.find_element(By.XPATH, ".//ancestor::div[contains(@class, 'comment') or contains(@role, 'button')]//a")
            return parent.text.strip()
        except:
            try:
                link = element.find_element(By.XPATH, ".//preceding-sibling::a | .//following-sibling::a | .//ancestor::*//a[1]")
                username = link.text.strip()
                if username and len(username) < 30:  # Reasonable username length
                    return username
            except:
                pass
            return "unknown"
    
    def close_modal(self):
        try:
            close_btn = self.driver.find_element(By.XPATH, "//div[@role='dialog']//button[contains(@aria-label, 'Close')]")
            close_btn.click()
            time.sleep(1)
            print("Modal closed dengan tombol X")
        except:
            try:
                from selenium.webdriver.common.keys import Keys
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)
                print("Modal closed dengan ESC")
            except:
                print("Gagal close modal")
    
    def save_to_csv(self, data, filename="instagram_comments_modal.csv"):
        if data:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"✓ Data saved to {filename}")
        else:
            print("No data to save")
    
    def close(self):
        self.driver.quit()

# Usage
if __name__ == "__main__":
    USERNAME = ""
    PASSWORD = "" 
    TARGET_ACCOUNT = ""  # Account yang mau di-scrape
    POST_INDEX = 0  # Post ke-0 (pertama/terbaru)
    
    scraper = InstagramScraperModal(headless=False)
    
    print("=== INSTAGRAM MODAL COMMENT SCRAPER ===")
    print(f"Target: {TARGET_ACCOUNT}")
    print(f"Post index: {POST_INDEX}")
    print("=" * 40)
    
    if scraper.login(USERNAME, PASSWORD):
        print("✓ Login berhasil, akses profile...")
        
        if scraper.go_to_profile_and_select_post(TARGET_ACCOUNT, POST_INDEX):
            print("✓ Modal terbuka, mulai scraping...")
            
            comments = scraper.scrape_comments_from_modal(max_comments=20)
            
            if comments:
                scraper.save_to_csv(comments)
                print(f"\n=== RESULTS ({len(comments)} comments) ===")
                for i, comment in enumerate(comments, 1):
                    username = comment.get('username', 'unknown')
                    text = comment['comment'][:80] + "..." if len(comment['comment']) > 80 else comment['comment']
                    print(f"{i}. [{username}]: {text}")
                print("=" * 40)
            else:
                print("✗ No comments found")
            
            # Close modal
            scraper.close_modal()
        else:
            print("✗ Gagal buka modal")
    else:
        print("✗ Login gagal")
    
    input("Press Enter to close browser...")
    scraper.close()
