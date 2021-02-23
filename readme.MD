# Survey helper

Sometimes we want a bit more information in surveygizmo to allow native reports to be more useful without post-analysis. 

This flask-based app sits between surveygizmo's webhooks and mapit/other lookups to pass fuller information back into survey results. 

Should be used in combination with templates for questions and webhooks in the research library. 

## End points

Parameters may be passed either through url parameters or as part of a POST action. 

### Geographic lookup

Convert postcode into LSOA and direct measures of deprivation on the fly so can be viewed in surveygizmo reports.

`\postcode`

Required parameters are:

* `postcode` - UK postcode in a format that mapit will accept.
* `access_key` - if access key is required by server.

### Category lookup

Convert a native FixMyStreet category into [the three meta-categories](https://github.com/mysociety/fms_meta_categories). 

`\fms_category`

Required parameters are:

* `category` - Category as entered into FixMyStreet.
* `access_key` - if access key is required by server.

## Enviromental variables

* `MAPIT_KEY` - key for mapit. 
* `ACCESS_KEY` - (optional) Adds a requirement for the same access key to be used by requests. 
* `SERVER_PRODUCTION` - true/false to use use waitress rather than flask's debug server. 

These can be set through args to the dockerfile build (see below).

## Run locally

Using the dockerfile, the following will run at `http://localhost:5000`.

```
# build
docker build -t survey_helper --build-arg MAPIT_KEY={{mapit_key}} --build-arg ACCESS_KEY={{access_key}} .

# running server
docker run -dp 5000:5000 survey_helper

```

## Deploy to heroku

???