# ByeTwitter

**Yet another Twitter account eraser**

## Scope

- Delete all tweets
- Unlike all tweets

## Install

You need Python 3.10 to run the scripts and API keys.

```bash
$ python3 -m venv venv
$ source venv/bin/activate
(venv)$ pip install -r requirements.txt
```

Set the following environment variables:

- TWITTER_CONSUMER_KEY
- TWITTER_CONSUMER_SECRET
- TWITTER_ACCESS_TOKEN
- TWITTER_ACCESS_TOKEN_SECRET

## Run

The scripts use the API v.1 (v.2 is not that great).

You can either:

- download an archive from your Twitter account and use the [local archive version](local_archive.py) or
- use the [full API version](main.py).

The local archive is slightly faster, uses less API calls and is more reliable. For some reason, the API version does not allow to fetch old tweets and likes. 

```bash
(venv)$ python main.py
```

or

```bash
(venv)$ python local_archive.py /path/to/archive
```
