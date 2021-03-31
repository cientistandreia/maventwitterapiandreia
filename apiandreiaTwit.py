##andreia zanette 31/0/2021


            logging.basicConfig()  # you need to initialize logging, otherwise you will not see anything from requests
            logging.getLogger().setLevel(logging.DEBUG)
            requests_log = logging.getLogger("requests.packages.urllib3")
            requests_log.setLevel(logging.DEBUG)
            requests_log.propagate = True

        self._session = requests.Session()

    @staticmethod
    def GetAppOnlyAuthToken(consumer_key, consumer_secret):
        """
        Generate a Bearer Token from consumer_key and consumer_secret
        """
        key = quote_plus(consumer_key)
        secret = quote_plus(consumer_secret)
        bearer_token = base64.b64encode('{}:{}'.format(key, secret).encode('utf8'))

        post_headers = {
            'Authorization': 'Basic {0}'.format(bearer_token.decode('utf8')),
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }

        res = requests.post(url='https://api.twitter.com/oauth2/token',
                            data={'grant_type': 'client_credentials'},
                            headers=post_headers)
        bearer_creds = res.json()
        return bearer_creds

    def SetCredentials(self,
                       consumer_key,
                       consumer_secret,
                       access_token_key=None,
                       access_token_secret=None,
                       application_only_auth=False):
        """Set the consumer_key and consumer_secret for this instance

        Args:
          consumer_key:
            The consumer_key of the twitter account.
          consumer_secret:
            The consumer_secret for the twitter account.
          access_token_key:
            The oAuth access token key value you retrieved
            from running get_access_token.py.
          access_token_secret:
            The oAuth access token's secret, also retrieved
            from the get_access_token.py run.
          application_only_auth:
            Whether to generate a bearer token and use Application-Only Auth
        """
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._access_token_key = access_token_key
        self._access_token_secret = access_token_secret

        if application_only_auth:
            self._bearer_token = self.GetAppOnlyAuthToken(consumer_key, consumer_secret)
            self.__auth = OAuth2(token=self._bearer_token)
        else:
            auth_list = [consumer_key, consumer_secret,
                         access_token_key, access_token_secret]
            if all(auth_list):
                self.__auth = OAuth1(consumer_key, consumer_secret,
                                     access_token_key, access_token_secret)

        self._config = None

    def GetHelpConfiguration(self):
        """Get basic help configuration details from Twitter.

        Args:
            None

        Returns:
            dict: Sets self._config and returns dict of help config values.
        """
        if self._config is None:
            url = '%s/help/configuration.json' % self.base_url
            resp = self._RequestUrl(url, 'GET')
            data = self._ParseAndCheckTwitter(resp.content.decode('utf-8'))
            self._config = data
        return self._config

    def GetShortUrlLength(self, https=False):
        """Returns number of characters reserved per URL included in a tweet.

        Args:
            https (bool, optional):
                If True, return number of characters reserved for https urls
                or, if False, return number of character reserved for http urls.
        Returns:
            (int): Number of characters reserved per URL.
        """
        config = self.GetHelpConfiguration()
        if https:
            return config['short_url_length_https']
        else:
            return config['short_url_length']

    def ClearCredentials(self):
        """Clear any credentials for this instance
        """
        self._consumer_key = None
        self._consumer_secret = None
        self._access_token_key = None
        self._access_token_secret = None
        self._bearer_token = None
        self.__auth = None  # for request upgrade

    def GetSearch(self,
                  term=None,
                  raw_query=None,
                  geocode=None,
                  since_id=None,
                  max_id=None,
                  until=None,
                  since=None,
                  count=15,
                  lang=None,
                  locale=None,
                  result_type="mixed",
                  include_entities=None,
                  return_json=False):
        """Return twitter search results for a given term. You must specify one
        of term, geocode, or raw_query.

        Args:
          term (str, optional):
            Term to search by. Optional if you include geocode.
          raw_query (str, optional):
            A raw query as a string. This should be everything after the "?" in
            the URL (i.e., the query parameters). You are responsible for all
            type checking and ensuring that the query string is properly
            formatted, as it will only be URL-encoded before be passed directly
            to Twitter with no other checks performed. For advanced usage only.
            *This will override any other parameters passed*
          since_id (int, optional):
            Returns results with an ID greater than (that is, more recent
            than) the specified ID. There are limits to the number of
            Tweets which can be accessed through the API. If the limit of
            Tweets has occurred since the since_id, the since_id will be
            forced to the oldest ID available.
          max_id (int, optional):
            Returns only statuses with an ID less than (that is, older
            than) or equal to the specified ID.
          until (str, optional):
            Returns tweets generated before the given date. Date should be
            formatted as YYYY-MM-DD.
          since (str, optional):
            Returns tweets generated since the given date. Date should be
            formatted as YYYY-MM-DD.
          geocode (str or list or tuple, optional):
            Geolocation within which to search for tweets. Can be either a
            string in the form of "latitude,longitude,radius" where latitude
            and longitude are floats and radius is a string such as "1mi" or
            "1km" ("mi" or "km" are the only units allowed). For example:
              >>> api.GetSearch(geocode="37.781157,-122.398720,1mi").
            Otherwise, you can pass a list of either floats or strings for
            lat/long and a string for radius:
              >>> api.GetSearch(geocode=[37.781157, -122.398720, "1mi"])
              >>> # or:
              >>> api.GetSearch(geocode=(37.781157, -122.398720, "1mi"))
              >>> # or:
              >>> api.GetSearch(geocode=("37.781157", "-122.398720", "1mi"))
          count (int, optional):
            Number of results to return.  Default is 15 and maximum that
            Twitter returns is 100 irrespective of what you type in.
          lang (str, optional):
            Language for results as ISO 639-1 code.  Default is None
            (all languages).
          locale (str, optional):
            Language of the search query. Currently only 'ja' is effective.
            This is intended for language-specific consumers and the default
            should work in the majority of cases.
          result_type (str, optional):
            Type of result which should be returned. Default is "mixed".
            Valid options are "mixed, "recent", and "popular".
          include_entities (bool, optional):
            If True, each tweet will include a node called "entities".
            This node offers a variety of metadata about the tweet in a
            discrete structure, including: user_mentions, urls, and
            hashtags.
          return_json (bool, optional):
            If True JSON data will be returned, instead of twitter.Userret
        Returns:
          list: A sequence of twitter.Status instances, one for each message
          containing the term, within the bounds of the geocoded area, or
          given by the raw_query.
        """

        url = '%s/search/tweets.json' % self.base_url
        parameters = {}

        if since_id:
            parameters['since_id'] = enf_type('since_id', int, since_id)

        if max_id:
            parameters['max_id'] = enf_type('max_id', int, max_id)

        if until:
            parameters['until'] = enf_type('until', str, until)

        if since:
            parameters['since'] = enf_type('since', str, since)

        if lang:
            parameters['lang'] = enf_type('lang', str, lang)

        if locale:
            parameters['locale'] = enf_type('locale', str, locale)

        if term is None and geocode is None and raw_query is None:
            return []

        if term is not None:
            parameters['q'] = term

        if geocode is not None:
            if isinstance(geocode, list) or isinstance(geocode, tuple):
                parameters['geocode'] = ','.join([str(geo) for geo in geocode])
            else:
                parameters['geocode'] = enf_type('geocode', str, geocode)

        if include_entities:
            parameters['include_entities'] = enf_type('include_entities',
                                                      bool,
                                                      include_entities)

        parameters['count'] = enf_type('count', int, count)

        if result_type in ["mixed", "popular", "recent"]:
            parameters['result_type'] = result_type

        if raw_query is not None:
            url = "{url}?{raw_query}".format(
                url=url,
                raw_query=raw_query)
            resp = self._RequestUrl(url, 'GET', data=parameters)
        else:
            resp = self._RequestUrl(url, 'GET', data=parameters)

        data = self._ParseAndCheckTwitter(resp.content.decode('utf-8'))
        if return_json:
            return data
        else:
            return [Status.NewFromJsonDict(x) for x in data.get('statuses', '')]

    def GetUsersSearch(self,
                       term=None,
                       page=1,
                       count=20,
                       include_entities=None):
        """Return twitter user search results for a given term.

        Args:
          term:
            Term to search by.
          page:
            Page of results to return. Default is 1
            [Optional]
          count:
            Number of results to return.  Default is 20
            [Optional]
          include_entities:
            If True, each tweet will include a node called "entities,".
            This node offers a variety of metadata about the tweet in a
            discrete structure, including: user_mentions, urls, and hashtags.
            [Optional]

        Returns:
          A sequence of twitter.User instances, one for each message containing
          the term
        """
        # Build request parameters
        parameters = {}

        if term is not None:
            parameters['q'] = term

        if page != 1:
            parameters['page'] = page

        if include_entities:
            parameters['include_entities'] = 1

        try:
            parameters['count'] = int(count)
        except ValueError:
            raise TwitterError({'message': "count must be an integer"})

        # Make and send requests
        url = '%s/users/search.json' % self.base_url
        resp = self._RequestUrl(url, 'GET', data=parameters)
        data = self._ParseAndCheckTwitter(resp.content.decode('utf-8'))
        return [User.NewFromJsonDict(x) for x in data]

    def GetTrendsCurrent(self, exclude=None):
        """Get the current top trending topics (global)

        Args:
          exclude:
            Appends the exclude parameter as a request parameter.
            Currently only exclude=hashtags is supported. [Optional]

        Returns:
          A list with 10 entries. Each entry contains a trend.
        """
        return self.GetTrendsWoeid(woeid=1, exclude=exclude)

    def GetTrendsWoeid(self, woeid, exclude=None):
        """Return the top 10 trending topics for a specific WOEID, if trending
        information is available for it.

        Args:
          woeid:
            the Yahoo! Where On Earth ID for a location.
          exclude:
            Appends the exclude parameter as a request parameter.
            Currently only exclude=hashtags is supported. [Optional]

        Returns:
          A list with 10 entries. Each entry contains a trend.
        """
        url = '%s/trends/place.json' % (self.base_url)
        parameters = {'id': woeid}

        if exclude:
            parameters['exclude'] = exclude

        resp = self._RequestUrl(url, verb='GET', data=parameters)
        data = self._ParseAndCheckTwitter(resp.content.decode('utf-8'))
        trends = []
        timestamp = data[0]['as_of']

        for trend in data[0]['trends']:
            trends.append(Trend.NewFromJsonDict(trend, timestamp=timestamp))
        return trends

		