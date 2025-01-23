
import pymysql
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

# Set up logging
def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Create handlers
    info_handler = logging.FileHandler('google_search_info.log', encoding='utf-8')
    info_handler.setLevel(logging.INFO)

    error_handler = logging.FileHandler('google_search_error.log', encoding='utf-8')
    error_handler.setLevel(logging.ERROR)

    # Create formatters and add them to handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    info_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger = logging.getLogger()
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)

# Initialize the database
def init_db():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='mysql_eG',
        database='gsearch'
    )
    return connection

# Truncate tables
def truncate_tables(connection):
    with connection.cursor() as cursor:
        cursor.execute('TRUNCATE TABLE search_results')
        cursor.execute('TRUNCATE TABLE search_terms')
        connection.commit()

# Read search terms from a file
def get_search_terms(file_name):
    with open(file_name, "r") as file:
        return [line.strip() for line in file.readlines() if line.strip()]  # Strip whitespace

# Categorize the result based on URL and description
def categorize_result(url, description):
    # Categorize based on description
    if any(keyword in description for keyword in ["news", "article", "report", "breaking", "חדשות", "כתבה", "דיווח", "חדשות", "חדשות"]):
        return 1
    elif any(keyword in description for keyword in ["blog", "post", "wordpress", "פוסט", "בלוג", "פוסטים", "בלוגים"]):
        return 2
    elif any(keyword in description for keyword in ["shop", "store", "buy", "sale", "קניה", "חנות", "מכירה", "מכירות", "קניות", "מוצרים", "מוצר", "קניית", "קנית"]):
        return 3
    elif any(keyword in description for keyword in ["edu", "course", "tutorial", "ללמוד", "לימודים", "קורס", "הדרכה", "הדרכות", "לימוד", "למידה", "למידה", "לימוד"]):
        return 4
    
    # Categorize based on URL suffix
    if url.endswith(".com"):
        return 1
    elif url.endswith(".blog"):
        return 2
    elif url.endswith(".store"):
        return 3
    elif url.endswith(".edu"):
        return 4
    else:
        return 5  # Default category ID for "Other"

# Insert search term into the database
def insert_search_term(connection, term):
    with connection.cursor() as cursor:
        cursor.execute('INSERT INTO search_terms (desc_st) VALUES (%s)', (term,))
        connection.commit()
        return cursor.lastrowid

# Insert search result into the database
def insert_search_result(connection, term_id, category_id, headline, url, description):
    with connection.cursor() as cursor:
        try:
            cursor.execute('''
                INSERT INTO search_results (id_st, id_ct, headline, description, url)
                VALUES (%s, %s, %s, %s, %s)
            ''', (term_id, category_id, headline, description, url))
            connection.commit()
            print(f"Inserted result: term_id={term_id}, category_id={category_id}, headline={headline}, url={url}, description={description}")
            logging.info(f"Inserted result: term_id={term_id}, category_id={category_id}, headline={headline}, url={url}, description={description}")
        except Exception as e:
            print(f"Error inserting result: term_id={term_id}, category_id={category_id}, headline={headline}, url={url}, description={description}")
            print(f"Exception: {e}")
            logging.error(f"Error inserting result: term_id={term_id}, category_id={category_id}, headline={headline}, url={url}, description={description}, Exception: {e}")

# Query results based on search term
def query_results_by_term(connection, search_term):
    with connection.cursor() as cursor:
        query = '''
            SELECT sr.headline, sr.url, sr.description, ct.desc_ct
            FROM search_results sr
            JOIN search_terms st ON sr.id_st = st.id_st
            JOIN content_type ct ON sr.id_ct = ct.id_ct
            WHERE st.desc_st = %s
        '''
        cursor.execute(query, (search_term,))
        results = cursor.fetchall()
        if results:
            for result in results:
                print(f"Headline: {result[0]}, URL: {result[1]}, Description: {result[2]}, Content Type: {result[3]}")
                logging.info(f"Headline: {result[0]}, URL: {result[1]}, Description: {result[2]}, Content Type: {result[3]}")
        else:
            print(f"No results for the term '{search_term}'")
            logging.info(f"No results for the term '{search_term}'")

# Query results based on content type
def query_results_by_content_type(connection, content_type):
    with connection.cursor() as cursor:
        query = '''
            SELECT sr.headline, sr.url, sr.description, st.desc_st
            FROM search_results sr
            JOIN search_terms st ON sr.id_st = st.id_st
            JOIN content_type ct ON sr.id_ct = ct.id_ct
            WHERE ct.desc_ct = %s
        '''
        cursor.execute(query, (content_type,))
        results = cursor.fetchall()
        if results:
            for result in results:
                print(f"Headline: {result[0]}, URL: {result[1]}, Description: {result[2]}, Search Term: {result[3]}")
                logging.info(f"Headline: {result[0]}, URL: {result[1]}, Description: {result[2]}, Search Term: {result[3]}")
        else:
            print(f"No results for content type '{content_type}'")
            logging.info(f"No results for content type '{content_type}'")

class GoogleSearchPage:
    def __init__(self, driver):
        self.driver = driver
        self.search_box = (By.NAME, "q")
        self.results_selector = (By.CSS_SELECTOR, 'div.g.Ww4FFb.vt6azd.tF2Cxc.asEBEc')
        self.internet_tab_xpath = "//div[text()='אינטרנט']"
        self.more_button_selector = (By.CSS_SELECTOR, 'div[jscontroller="xdV1C"]')
        self.internet_option_selector = (By.CSS_SELECTOR, 'a.d4DFfb.nPDzT.T3FoJb div.eJWNqc.YmvwI')

    def load(self):
        self.driver.get("https://www.google.com")
        logging.info("Google loaded successfully")

    def search(self, term):
        search_box = self.driver.find_element(*self.search_box)
        search_box.clear()
        search_box.send_keys(term)
        search_box.send_keys(Keys.RETURN)
        logging.info(f"Searching for: {term}")

    def wait_for_results(self):
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_all_elements_located(self.results_selector))

    def click_internet_tab(self):
        wait = WebDriverWait(self.driver, 10)
        try:
            internet_tab = wait.until(EC.element_to_be_clickable((By.XPATH, self.internet_tab_xpath)))
            internet_tab.click()
            logging.info("Clicked on the 'אינטרנט' tab")
        except Exception as e:
            logging.error(f"Error clicking on the 'אינטרנט' tab: {e}")
            try:
                more_button = wait.until(EC.element_to_be_clickable(self.more_button_selector))
                more_button.click()
                internet_option = wait.until(EC.element_to_be_clickable(self.internet_option_selector))
                internet_option.click()
                logging.info("Clicked on the 'אינטרנט' option")
            except Exception as e:
                logging.error(f"Error clicking on the 'עוד' button or 'אינטרנט' option: {e}")
                raise

    def get_results(self):
        return self.driver.find_elements(*self.results_selector)

def main():
    setup_logging()

    search_terms = get_search_terms("search_terms.txt")
    print("Search terms:", search_terms)
    logging.info("Search terms loaded")

    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    connection = init_db()
    truncate_tables(connection)
    logging.info("Database tables truncated")

    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    google_search_page = GoogleSearchPage(driver)
    google_search_page.load()

    for term in search_terms:
        try:
            term_id = insert_search_term(connection, term)
            google_search_page.search(term)
            time.sleep(random.uniform(2, 5))
            google_search_page.wait_for_results()
            google_search_page.click_internet_tab()
            google_search_page.wait_for_results()

            results = google_search_page.get_results()
            print(f"Found {len(results)} results for '{term}'")
            logging.info(f"Found {len(results)} results for '{term}'")

            for index, result in enumerate(results):
                try:
                    headline = result.find_element(By.CSS_SELECTOR, 'h3.LC20lb.MBeuO.DKV0Md').text
                    url = result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    description = result.find_element(By.CSS_SELECTOR, 'div.VwiC3b.yXK7lf.p4wth.r025kc.hJNv6b.Hdw6tb').text
                    category = categorize_result(url, description)
                    print(f"Result {index + 1}:")
                    print(f"Headline: {headline}")
                    print(f"URL: {url}")
                    print(f"Description: {description}")
                    print(f"Category: {category}")
                    logging.info(f"Result {index + 1}: Headline: {headline}, URL: {url}, Description: {description}, Category: {category}")

                    insert_search_result(connection, term_id, category, headline, url, description)
                except Exception as e:
                    print(f"Error parsing result {index + 1}: {e}")
                    logging.error(f"Error parsing result {index + 1}: {e}")

        except Exception as e:
            print(f"Unexpected error processing term '{term}': {e}")
            logging.error(f"Unexpected error processing term '{term}': {e}")

    # First of all empty fields
    search_term = ''
    content_type = ''
    search_term = input("Enter the search term to query: ")
    content_type = input("Enter the content type to query (e.g., 'News Article'): ")
    
    print(f"Results for search term '{search_term.strip()}':")
    logging.info(f"Results for search term '{search_term.strip()}':")
    query_results_by_term(connection, search_term.strip())

    print(f"\nResults for content type '{content_type.strip()}':")
    logging.info(f"\nResults for content type '{content_type.strip()}':")
    query_results_by_content_type(connection, content_type.strip())

if __name__ == "__main__":
    main()
