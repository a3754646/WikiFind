import json, re
import requests
from pathlib import Path

API_URL = "https://en.wikipedia.org/w/api.php"

output = Path(__file__).with_name("sample_articles.json") 

#500 articles
#category: electronics (later on add more)
#content: pageid,  Title,  introduction, url 
#collection method: api to local saves
#cleaning: duplicates, empty pages investigation, External links, citation