# Belka

Belka is a slack app / slackbot for #TNN (Strelka 2017 // The New Normal)'s internal slack team.

## Current Functionality

- post all URLs in the #links channel on slack to the [Links channel](https://www.are.na/strelka-2017/links-1489249188) on the Strelka 2017 are.na page

## Requirements

Things you need:
- Python
- virtualenv
- an env.prod / env.dev file with keys etc.

## Install & Run

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt

source env.dev && gunicorn belka:slack_events_adapter.server
```
## Deployment

I originally set this up to run on heroku, but free-dynos on heroku go
to sleep after being inactive for 1 hour, and take around 5-10 seconds
to boot back up after being asleep. This doesn't work too well with Slack's
Event API which has a retry logic & times out after 3 seconds...

The alternative was just running the bot in a screen on a personal server I
have... this is what the `./start.sh` script is for. I may look into fancy
git-hooks at some point but for now am doing deployments manually.

# Contributing

If you want to add any functionality based off event streams in slack,
take a look at the documentation for Slack's Event API [here](https://medium.com/slack-developer-blog/enhancing-slacks-events-api-7535827829ab#.e25h4meix).

The only file you'll have to peep into at all is `belka.py`.

Fork & PR away !
