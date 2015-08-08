# Smartnews: The highway to hell for news
Web platform which allows the users to 'scrape' from their favorite news site and have a refined landscape for everyday hot topics.
# How to use it locally? (Linux - Mac)
* git clone or download project.

Server:
------
* Install vagrant
* In project's folder:
1. sudo vagrant init.
2. sudo fab vagrant install.

Then you can call the task that creates the topics:
```
from scraper_module.tasks import scrape_news
scrape_news.delay()
```
The web module is still on development.
But idea is user can signup, select the scrapers he wants and the user will have the news in a tag cloud format with all the sites related to every topic


ROAD MAP:
--------

* 0.1: Simple version with everyday hot-topic
* 0.2: Multiuser support. User can select in a list of predefined scrapers.
* 0.3: User can create 'alarms' looking for some concepts or topics.
* 0.4: User can create its own scrapers.
* 0.5: Integration with social networks.
* 0.6: Integration with blog services (widget creation)
* 0.7: Migration to AngularJS. API Generation