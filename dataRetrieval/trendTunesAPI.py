import requests


class ArtistTag:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url


class ArtistData:
    def __init__(self, name: str, playcount: int, listeners: int, url: str, mbid: str):
        self.name = name
        self.playcount = playcount
        self.listeners = listeners
        self.url = url
        self.mbid = mbid
        self.tags: list[ArtistTag] = list()

    def set_tags(self, tags: list):
        for tag in tags:
            tag_class = ArtistTag(name=tag['name'].lower(), url=tag['url'])
            self.tags.append(tag_class)

    def __str__(self):
        return self.name


class DataRetrieval:
    API_KEY = '956a0919de5df08c6b74da7a69559425'
    BASE_URL = 'http://ws.audioscrobbler.com/2.0/'
    NUM_OF_ARTISTS = 3000
    NUM_OF_ARTISTS_PER_PAGE = 50
    NUM_OF_QUERIES = int(NUM_OF_ARTISTS/NUM_OF_ARTISTS_PER_PAGE)

    def __init__(self):
        self.token = ""
        self.top_artists: list[ArtistData] = list()
        self._raw_top = None

    def get_token_api(self):
        response = self._send_request("auth.gettoken")
        if response:
            self.token = response["token"]

    def get_top_artists(self):
        def parse_artists(artist_data):
            for artist in artist_data:
                artist_class = ArtistData(name=artist['name'], playcount=int(artist['playcount']),
                                          listeners=int(artist['listeners']),
                                          url=artist['url'], mbid=artist['mbid'])
                self.top_artists.append(artist_class)

        for i in range(0, self.NUM_OF_QUERIES):
            response = self._send_request("chart.gettopartists", {"page": str(i+1)})
            if not response:
                continue
            parse_artists(response['artists']['artist'])

    def get_tags_for_all_artists(self):
        for artist in self.top_artists:
            params = {"autocorrect": 1}
            if artist.mbid:
                params["mbid"] = artist.mbid
            else:
                params["artist"] = artist.name

            response = self._send_request("artist.gettoptags", params)
            if not response:
                print(f"failed to get tags for: {artist}")
                continue

            if 'error' in response:
                self.search_artist(artist.name)

            artist.set_tags(response['toptags']['tag'])

    def search_artist(self, name: str):
        response = self._send_request("artist.getinfo", {"artist": name})
        print(response)

    def _send_request(self, method: str, optional_params: dict = None):
        param = {
            'method': method,
            'api_key': self.API_KEY,
            'format': 'json'
        }
        if optional_params is not None:
            param.update(optional_params)

        response = requests.get(self.BASE_URL, params=param)
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            print("Response:", data)
            return data
        else:
            print(f"Error: {response.status_code}")


def run_api() -> list[ArtistData]:
    data = DataRetrieval()
    data.get_top_artists()
    data.get_tags_for_all_artists()
    print("done")
    return data.top_artists
