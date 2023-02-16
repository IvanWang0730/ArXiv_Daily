#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import time
import datetime
import requests
import json
import arxiv
import re
import hmac
import hashlib
import base64
import urllib.parse

base_url = "https://arxiv.paperswithcode.com/api/v0/papers/"


def del_unicode(string):
    string = re.sub(r'\\u.{4}', '', string.__repr__())
    return string


def del_not_english(string):
    string = re.sub('[^A-Za-z]', '', string.__str__())
    return string


def get_authors(authors, first_author=False):
    output = str()
    if first_author == False:
        output = ", ".join(str(author) for author in authors)
    else:
        output = authors[0]
    return output


def get_daily_papers(topic, query="nlp", max_results=2, date=datetime.date.today()):
    """
    @param topic: str
    @param query: str
    @return paper_with_code: dict
    """
    # output
    content = dict()
    content_to_web = dict()

    search_engine = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    for result in search_engine.results():

        paper_id = result.get_short_id()
        paper_title = result.title
        paper_url = result.entry_id

        code_url = base_url + paper_id
        paper_abstract = result.summary.replace("\n", " ")
        paper_authors = get_authors(result.authors)
        paper_first_author = get_authors(result.authors, first_author=True)
        primary_category = result.primary_category

        publish_time = result.published.date()
        update_time = result.updated.date()

        if update_time != date:
            continue

        print("Time = ", update_time,
              " title = ", paper_title,
              " author = ", paper_first_author)

        # eg: 2108.09112v1 -> 2108.09112
        ver_pos = paper_id.find('v')
        
        if ver_pos == -1:
            paper_key = paper_id
        else:
            paper_key = paper_id[0:ver_pos]

        try:
            r = requests.get(code_url).json()
            # source code link
            output.append("[{}][{}]({}) \n\n {} \n\n".format(len(output)+1, paper_title, paper_url, paper_authors))
            if "official" in r and r["official"]:
                repo_url = r["official"]["url"]
                content[
                    paper_key] = f"|**{update_time}**|**{paper_title}**|{paper_first_author} et.al.|[{paper_id}]({paper_url})|**[link]({repo_url})**|\n"
                content_to_web[
                    paper_key] = f"- **{update_time}**, **{paper_title}**, {paper_first_author} et.al., [PDF:{paper_id}]({paper_url}), **[code]({repo_url})**\n"
            else:
                content[
                    paper_key] = f"|**{update_time}**|**{paper_title}**|{paper_first_author} et.al.|[{paper_id}]({paper_url})|null|\n"
                content_to_web[
                    paper_key] = f"- **{update_time}**, **{paper_title}**, {paper_first_author} et.al., [PDF:{paper_id}]({paper_url})\n"

        except Exception as e:
            print(f"exception: {e} with id: {paper_key}")

    data = {topic: content}
    data_web = {topic: content_to_web}
    return data, data_web


def get_timestamp_sign():
    timestamp = str(round(time.time() * 1000))
    import os
    SCKEY = "SECa27c4ee78efe89f7e2c39324a4d96d444813a1e457aad2f0f3c52e41107855f4"
    print(os.environ["SCKEY"]=="SECa27c4ee78efe89f7e2c39324a4d96d444813a1e457aad2f0f3c52e41107855f4")
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc,
                         digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    print("timestamp: ",timestamp)
    print("sign:",sign)
    return (timestamp, sign)


def get_signed_url(url):
    timestamp, sign = get_timestamp_sign()
    webhook = url + "&timestamp="+timestamp+"&sign="+sign
    return webhook


if __name__ == "__main__":
    yesterday = datetime.date.today()-datetime.timedelta(days=1)
    before_yesterday = yesterday-datetime.timedelta(days=1)
    print(f"yesterday: {yesterday}")
    final = []

    for date in [yesterday, before_yesterday]:
        data_collector = []
        data_collector_web = []
        global output
        output = []

        keywords = dict()
        keywords["CTR"] = "\"Click-Through Rate\"OR\"CTR\""
        # keywords["Named Entity Recognition"] = "\"Named Entity Recognition\""
        # keywords["Text Classification"] = "\"Text Classification\"OR\"Topic Labeling\"OR\"News Classification\"OR\"Dialog Act Classification\"OR\"Natural Language Inference\"OR\"Relation Classification\"OR\"Event Prediction\""
        # keywords["Sentiment Analysis"] = "\"Sentiment Analysis\""
        # keywords["Question Answering"] = "\"QA\"OR\"Question Answering\""
        # keywords["Information Extraction"] = "\"Information Extraction\"OR\"Automatic Summary\"OR\"Title Generation\"OR\"Event Extraction\""
        keywords["Recommendation System"] = "\"Recommendation System\"OR\"Semantic Matching\"OR\"Chatbots\""
        # keywords["Knowledge Graph"] = "\"Knowledge Graph\"OR\"Knowledge Graphs\""
        # keywords["GNN"] = "GNN" + "OR" + "\"Graph Neural Network\""
        keywords["ChatGPT"] = "\"ChatGPT\""

        for topic, keyword in keywords.items():
            # topic = keyword.replace("\"","")
            print("Keyword: " + topic)

            data, data_web = get_daily_papers(topic, query=keyword, max_results=10, date=date)
            data_collector.append(data)
            data_collector_web.append(data_web)

            print("\n")

        date_title = date.strftime('%a, %d %b %Y')
        final.append("**{}** \n\n".format(date_title) + "--- \n\n".join(output))
    
    final = "--- \n\n".join(final)
    print(final)
    url = "https://oapi.dingtalk.com/robot/send?access_token=04cd2462c1d451f0099e7b32263d2256683e8ae0b0dcdd5b6c4bca366ff7eef5"
    url = get_signed_url(url)
    header = {
        "Content-Type": "application/json",
        "Charset": "UTF-8"
    }
    data = {
    "msgtype": "markdown",
    "markdown": {
        "title": "ArXiv Daily",
        "text": final
    },
    "at": {
        "isAtAll": False
        }
    }
    response = requests.post(url, json.dumps(data), headers=header)
    print(response.text)

    
