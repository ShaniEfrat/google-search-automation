# Google Search Automation

This project automates Google searches using Selenium WebDriver and stores the search results in a MySQL database. The script reads search terms from a file, performs searches on Google, categorizes the results, and stores them in the database. It also provides functionality to query the stored results based on search terms or content types.

## Prerequisites

- Python 3.x
- MySQL server
- Google Chrome browser (In Hebrew)
- ChromeDriver
- Pymysql 

## Dependencies

- **Python Packages**:
  - `pymysql`
  - `selenium`

- **External Tools**:
  - Google Chrome browser
  - ChromeDriver

- **Database**:
  - MySQL server

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/google-search-automation.git
   cd google-search-automation

2. Install the required Python packages:
   pip install -r requirements.txt
   
3. Set up the MySQL database:

Create a database named gsearch.
UnZip Dump20250122.zip and Import Schema from the file [search_terms(empty table), search_results(empty table), content_type]

4. Attached file named search_terms.txt in the project directory and add your search terms, one per line.

Usage
1. Run the script:
python google_search.py

2. Follow the prompts to query the stored results:

Enter the search term to query.
Enter the content type to query (e.g., 'News Article').

Logging
The script logs information and errors to separate log files:
google_search_info.log for informational messages.
google_search_error.log for error messages.

License
This project is licensed under the MIT License.
