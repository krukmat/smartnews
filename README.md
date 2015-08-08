# smartnews: The highway to the hell for the news
Web platform which allows the users to 'scrape' from their favorite news site and have a refined landscape for everyday hot topics.
# How to use it locally? (Linux - Mac)
* git clone or download project.

Server:
------
* Install vagrant
* sudo fab vagrant init
* sudo fab vagrant install


Then you can call this task:
from scraper_module.tasks import scrape_news
scrape_news.delay()

The web module is still on development. But idea is user can signup, select the scrapers he wants and the user will have the news in a tag cloud format with all the sites related to every topic
