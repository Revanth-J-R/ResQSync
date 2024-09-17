import feedparser
import json
import os
from flask import Flask, render_template, request
from newspaper import Article
import re
from datetime import datetime
import spacy
from nltk.tokenize import sent_tokenize
from wordcloud import WordCloud
import matplotlib.pyplot as plt

nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)

# RSS URL
rss_url = "https://www.indiatoday.in/rss/1206578"

# JSON file paths
FULL_FEED_FILE = "static/data/full_feed.json"
DISASTER_DATA_FILE = "static/data/disaster_data.json"
EXTRACTED_DATA_FILE = "static/data/extracted_data.json"


def fetch_rss_updates():
    feed = feedparser.parse(rss_url)
    all_entries = []
    disaster_entries = []

    # Fetching all entries and disaster-related entries
    with open(DISASTER_DATA_FILE, "r") as file:
        data = json.load(file)

    for entry in feed.entries:
        title = entry.title
        link = entry.link
        published = entry.published

        all_entries.append({"title": title, "link": link, "published": published})

        article = Article(link)
        article.download()
        article.parse()
        content = article.text
        """
        disaster_list = {
            "flood": [],
            "cyclone": [],
            "earthquake": [],
            "pandemic": [],
            "virus": []
        }
"""
        for dis in data.keys():
            if dis in content.lower() and title not in data[dis]:
                if len(data[dis]) == 0:
                    data[dis].append(
                        {
                            "title": title,
                            "link": link,
                            "published": published,
                            "content": content,
                        }
                    )
                else:
                    for news in data[dis]:
                        if title not in news["title"]:
                            data[dis].append(
                                {
                                    "title": title,
                                    "link": link,
                                    "published": published,
                                    "content": content,
                                }
                            )
    # Write the full RSS feed data to a JSON file (overwritten each time)
    with open(FULL_FEED_FILE, "w") as file:
        json.dump(all_entries, file, indent=4)

    with open(DISASTER_DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)


def append_to_json(file_path, new_data):
    # Load existing data
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            existing_data = json.load(file)
    else:
        existing_data = []

    # Add only non-duplicate entries
    updated_data = existing_data + [
        entry for entry in new_data if entry not in existing_data
    ]

    # Save updated data
    with open(file_path, "w") as file:
        json.dump(updated_data, file, indent=4)


def extract_details():
    with open(DISASTER_DATA_FILE, "r") as file:
        disaster_entries = json.load(file)

    with open(EXTRACTED_DATA_FILE, "r") as file:
        extracted_entries = json.load(file)

    # Extract details from the articles
    for dis in disaster_entries.keys():
        if len(disaster_entries[dis]) > 0:
            entry = disaster_entries[dis][-1]
            link = entry["link"]
            article = Article(link)
            article.download()
            article.parse()
            text = article.text
            doc = nlp(text)
            disaster = dis
            place = None
            for ent in doc.ents:
                if ent.label_ == "GPE":  # GPE stands for Geopolitical Entity
                    place = ent.text
                    break

            people_affected = None
            match = re.search(
                r"\b(\d{1,3}(?:,\d{3})*)\b\s+(affected|villagers|deaths?|people)", text
            )

            if match:
                people_affected = int(match.group(1).replace(",", ""))

            date = str(
                datetime.strptime(entry["published"], "%a, %d %b %Y %H:%M:%S %z").date()
            )
            time = str(
                datetime.strptime(entry["published"], "%a, %d %b %Y %H:%M:%S %z").time()
            )

            new = {
                "latest_headline": article.title,
                "people_affected": people_affected,
                "last_updated_date": date,
                "last_updated_time": time,
                "link": link,
            }

            if len(extracted_entries[dis]) > 0:
                if place.lower() in extracted_entries[dis].keys():
                    if len(extracted_entries[dis][place.lower()]) > 0:
                        for key in extracted_entries[dis][place.lower()].keys():
                            if extracted_entries[dis][place.lower()][key] != new[key]:
                                extracted_entries[dis][place.lower()][key] = new[key]

            else:
                extracted_entries[dis][place.lower()] = new
    with open(EXTRACTED_DATA_FILE, "w") as file:
        json.dump(extracted_entries, file, indent=4)


@app.route("/")
def index():
    with open(DISASTER_DATA_FILE, "r") as file:
        full_feed = json.load(file)
    disaster_data = []
    for i in full_feed.keys():
        if len(full_feed[i]) > 0:
            disaster_data.append(i)
    return render_template("index.html", data=disaster_data)


@app.route("/places")
def place_details():
    disaster_name = request.args.get("disaster_name")

    with open(EXTRACTED_DATA_FILE, "r") as file:
        extracted = json.load(file)

    places = []
    for x in extracted[disaster_name].keys():
        if x not in places:
            places.append(x)
    # Pass the manipulated data to the template
    return render_template("places.html", disaster=disaster_name, list=places)


@app.route("/disaster_data")
def show_disaster_data():
    with open(DISASTER_DATA_FILE, "r") as file:
        disaster_data = json.load(file)
    return render_template("json_view.html", data=disaster_data, title="Disaster News")


@app.route("/extracted_data")
def show_extracted_data():
    with open(EXTRACTED_DATA_FILE, "r") as file:
        extracted_data = json.load(file)
    return render_template(
        "json_view.html", data=extracted_data, title="Extracted Data"
    )


@app.route("/weather")
def weather():
    return render_template("weather.html")


@app.route("/summary")
def summary():
    disaster_name = request.args.get("disaster_name")
    place = request.args.get("place")
    with open("static/data/extracted_data.json", "r") as file:
        data = json.load(file)
    content = data[disaster_name][place]
    link = content["link"]
    article = Article(link)
    article.download()
    article.parse()
    text = article.text
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(
        text
    )

    wordcloud_path = "static/wordcloud.png"
    wordcloud.to_file(wordcloud_path)

    return render_template(
        "summary.html",
        place=place,
        disaster_name=disaster_name,
        data=content,
        wc_path=wordcloud_path,
    )


@app.route("/latest_news")
def latest_news():
    with open("static/data/disaster_data.json", "r") as file:
        data = json.load(file)

    return render_template("latest_news.html", data=data)


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    fetch_rss_updates()  # Fetch and process RSS feed data
    extract_details()  # Scrape disaster-related news articles
    app.run(debug=True)  # Start the Flask server
