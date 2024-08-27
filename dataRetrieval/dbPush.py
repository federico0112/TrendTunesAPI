from datetime import datetime

import traceback
import trendTunesAPI
import psycopg2
from psycopg2 import sql, errors


class DBInteraction:
    def __init__(self):
        self._conn = None
        self._cur = None

    def connect(self):
        self._conn = psycopg2.connect(database="postgres",
                                      user="postgres",
                                      password="Fred*0112!",
                                      host="trendtunes-dev.clq2m6y84fp1.us-east-1.rds.amazonaws.com",
                                      port="5432")

        self._cur = self._conn.cursor()

    def disconnect(self):
        if self._conn is None:
            return
        self._cur.close()
        self._conn.close()

    def insert_artist(self, name, url):
        if self._cur is None:
            self.connect()

        artist_id = None

        try:
            self._cur.execute("""
                INSERT INTO artists (artist_name, artist_url)
                VALUES (%s, %s)
                ON CONFLICT (artist_name) DO NOTHING
                RETURNING artist_id;
            """, (name, url))

            # Get the artist_id
            returned_data = self._cur.fetchone()
            if returned_data is None:
                self._cur.execute("SELECT artist_id FROM artists WHERE artist_name = %s", (name,))
                returned_data = self._cur.fetchone()

            artist_id = returned_data[0]
            self._conn.commit()
            print(f"Inserted Artist: {name}, id: {artist_id}")
        except Exception as e:
            print(f"Error: {e}, artist name: {name}")
            print(traceback.format_exc())
            self._conn.rollback()
        return artist_id

    def insert_tag(self, tag_name, tag_url):
        if self._cur is None:
            self.connect()

        tag_id = None
        try:
            self._cur.execute("""
                INSERT INTO tags (tag_name, tag_url)
                VALUES (%s, %s)
                ON CONFLICT (tag_name) DO NOTHING
                RETURNING tag_id;
            """, (tag_name, tag_url))

            # Get the tag_id
            returned_data = self._cur.fetchone()
            if returned_data is None:
                self._cur.execute("SELECT tag_id FROM tags WHERE tag_name = %s", (tag_name,))
                returned_data = self._cur.fetchone()

            tag_id = returned_data[0]
            self._conn.commit()
            print(f"Inserted tag: {tag_name}, id: {tag_id}")
        except Exception as e:
            print(f"Error: {e}, tag name: {tag_name}")
            print(traceback.format_exc())
            self._conn.rollback()

        return tag_id

    def link_artist_and_tag(self, artist_id, tag_id):
        if self._cur is None:
            self.connect()

        try:
            self._cur.execute("""
                INSERT INTO artist_tags (artist_id, tag_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
            """, (artist_id, tag_id))

            self._conn.commit()
            print(f"Linked artist and tag id: {tag_id}, artist id: {artist_id}")
        except Exception as e:
            print(f"Error: {e}, tag id: {tag_id}, artist id: {artist_id}")
            print(traceback.format_exc())
            self._conn.rollback()

    def insert_rank(self, artist_id, rank, listeners_count, plays_count):
        if self._cur is None:
            self.connect()

        try:
            self._cur.execute("""
                INSERT INTO rankings (artist_id, rank, listeners_count, plays_count, ranking_date)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (artist_id, rank, listeners_count, plays_count, str(datetime.now().date())))

            self._conn.commit()
            print(f"Inserted rank for: {artist_id}")
        except Exception as e:
            print(f"Error: {e}, failed to insert rank for: {artist_id}")
            print(traceback.format_exc())

            self._conn.rollback()

    def run(self):
        # Get top artists
        top_artists = trendTunesAPI.run_api()

        for rank, artist in enumerate(top_artists):
            # Add artist to DB
            artist_id = self.insert_artist(name=artist.name, url=artist.url)
            if artist_id is None:
                continue

            # Add tags to db
            for tag in artist.tags:
                # Don't push single letter tags
                if len(tag.name) == 1:
                    continue
                tag_id = self.insert_tag(tag_name=tag.name, tag_url=tag.url)
                if tag_id is None:
                    continue

                # Link artist to tag
                self.link_artist_and_tag(artist_id=artist_id, tag_id=tag_id)

            self.insert_rank(artist_id=artist_id, rank=rank + 1, listeners_count=artist.listeners,
                             plays_count=artist.playcount)


if __name__ == '__main__':
    DBInteraction().run()
