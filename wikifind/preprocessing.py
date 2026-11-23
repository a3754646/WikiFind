"""
Preprocessing functions for WikiFind.

Cleans and normalizes text data, including removing unwanted characters, 
handling whitespace, and converting text to a consistent format. 
Also removes stop words and performs stemming.

MUST RUN: pip install nltk
"""

import json
import os
import re
import sys
import unicodedata
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()

ARTICLE = os.path.join(os.path.dirname(__file__), "..", "data_collection", "sample_articles.json")


#CLEANING

SPECIAL_CHARACTERS = {
    "\u2010": "-",  # Hyphen
    "\u2011": "-",  # Non-breaking hyphen
    "\u2012": " ",  # Figure dash
    "\u2013": " ",  # En dash
    "\u2014": " ",  # Em dash
    "\u2212": " ",  # Minus sign
    "\u2018": "'",  # Left apostrophe
    "\u2019": "'",  # Right apstrophe
    "\u02bc": "'",  # Modifier letter apostrophe
    "\u201c": " ",  # Left double quotation mark
    "\u201d": " ",  # Right double quotation mark
    "\u00d7": " ",  # multiplication sign
    "\u2044": " ",  # forward slash
    "\u00b0": " ",  # Degree symbol
}

def clean_text(text):

    text = re.sub(r"\[(\d+|citation needed)\]", " ", text, flags=re.IGNORECASE)
    
    #links
    text = re.sub(r"https?://\S+|www\.\S+",  "", text)

    for i, j in SPECIAL_CHARACTERS.items():
        text = text.replace(i, j)

    #accents
    text = unicodedata.normalize("NFKD", text)
    temp = ""
    for k in text:
        if not unicodedata.combining(k):
            temp += k

    return " ".join(temp.split())


#Stop words borrowed from:
# https://gist.github.com/sebleier/554280
STOP_WORDS_FILE = os.path.join(os.path.dirname(__file__), "..", "stopwords.txt")

def load_stop_words():
    words = set()
    with open(STOP_WORDS_FILE, encoding="utf-8") as f:
        for line in f:
            word = line.strip().lower()
            if word != "":
                words.add(word)
    return words

STOP_WORDS = load_stop_words()

#TOKENIZATION

def decimal(word):
    return "." in word and word.replace(".", "").isdigit()

def split_word(word):
    word = word.strip("'.-")
    if word == "" or word in STOP_WORDS:
        return []

    if word.endswith("'s"):
        word = word[:-2]
    word = word.replace("'", "")

    if decimal(word):
        return [word]

    if "." in word:
        parts = word.split(".")
        short = True
        for part in parts:
            if len(part) > 2:
                short = False
        if short:
            words = ["".join(parts)]
        else:
            words = parts
    else:
        words = [word]

    #hypiens
    pieces = []
    for i in words:
        parts = []
        for j in i.split("-"):
            if j != "":
                parts.append(j)
        pieces.extend(parts)
        if len(parts) > 1:
            pieces.append("".join(parts))
    return pieces

def tokenize(text, use_stemming=True):
    text = clean_text(text).lower()
    base_words = re.findall(r"[\w'.-]+", text)

    tokens = []
    for word in base_words:
        for piece in split_word(word):
            if piece in STOP_WORDS:
                continue
            if len(piece) == 1 and not piece.isdigit():
                continue
            if use_stemming and piece.isascii() and piece.isalpha():
                piece = stemmer.stem(piece)
            tokens.append(piece)
    return tokens

#article processing

def load_articles():
    with open(ARTICLE, encoding="utf-8") as f:
        articles = json.load(f)
    return articles

def process_articles(articles, include_title=False):
    results = []
    for article in articles:
        text = article["text"]
        if include_title:
            text = article["title"] + ". " + text
        tokens = tokenize(text)
        if len(tokens) > 0:
            new = dict(article)
            new["tokens"] = tokens
            results.append(new)
    return results

def results_printing():
    articles = load_articles()
    processed = process_articles(articles)

    counting = {}
    total = 0
    for article in processed:
        for token in article["tokens"]:
            counting[token] = counting.get(token, 0) + 1
            total += 1

    print("Tokens: " + str(total))
    print("Unique Terms: " + str(len(counting)))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(tokenize(" ".join(sys.argv[1:])))
    else:
        results_printing()