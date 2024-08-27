#!/usr/bin/env python
import json
import enum
import psycopg2
import logging
import traceback
from os import environ


class QueryTypes(enum.Enum):
    GET_TOP_TAGS = "GET_TOP_TAGS"
    GET_TOP_ARTISTS = "GET_LATEST_TOP_ARTISTS"
    GET_ARTISTS_FROM_TAG = "GET_ARTISTS_FROM_TAG"


class QueryHandler:
    _queries = {
        QueryTypes.GET_TOP_TAGS: """
                        SELECT t.tag_name, COUNT(DISTINCT at.artist_id) AS artist_count \
                        FROM artist_tags at \
                        JOIN tags t ON at.tag_id = t.tag_id \
                        GROUP BY t.tag_name \
                        ORDER BY artist_count DESC
                        """,

        QueryTypes.GET_TOP_ARTISTS: """
                                    SELECT r.artist_id, a.artist_name, r.rank, r.listeners_count, r.ranking_date 
                                    FROM rankings r 
                                    JOIN artists a ON r.artist_id = a.artist_id 
                                    WHERE r.ranking_date = (SELECT MAX(ranking_date) FROM rankings) 
                                    ORDER BY r.rank ASC 
                                    LIMIT 100
                                     """,

        QueryTypes.GET_ARTISTS_FROM_TAG: """
                                SELECT a.artist_id, a.artist_name, a.spotify_url
                                FROM artists a
                                JOIN artist_tags at ON a.artist_id = at.artist_id
                                JOIN tags t ON at.tag_id = t.tag_id
                                WHERE t.tag_name = {}; 
                                """

    }

    def __init__(self, queryType: QueryTypes):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel("INFO")
        self.endpoint = environ.get('ENDPOINT')
        self.port = environ.get('PORT')
        self.dbUser = environ.get('DBUSER')
        self.password = environ.get('DBPASSWORD')
        self.database = environ.get('DATABASE')
        self.query = self._queries[queryType]
        self.cursor = None

    def __del__(self):
        if self.cursor is not None:
            try:
                self.cursor.close()
            except Exception:
                pass

    def _log_err(self, errmsg):
        self._logger.error(errmsg)
        return {"body": errmsg, "headers": {}, "statusCode": 400,
                "isBase64Encoded": "false"}

    def _make_connection(self):
        try:
            conn_str = "host={0} dbname={1} user={2} password={3} port={4}".format(
                self.endpoint, self.database, self.dbUser, self.password, self.port)
            conn = psycopg2.connect(conn_str)
            conn.autocommit = True
            self.cursor = conn.cursor()

        except Exception:
            return self._log_err("ERROR: Cannot connect to database from handler.\n{}".format(
                traceback.format_exc()))

    def _execute_query(self, *args, **kwargs):
        if self.cursor is None:
            return
        try:
            self.cursor.execute(self.query.format(*args, **kwargs))
        except Exception:
            return self._log_err("ERROR: Cannot execute cursor.\n{}".format(
                traceback.format_exc()))

    def _retrieve_data(self):
        if self.cursor is None:
            return

        try:
            results_list = [result for result in self.cursor]
            self.cursor.close()
        except Exception:
            return None, self._log_err("ERROR: Cannot retrieve query data.\n{}".format(
                traceback.format_exc()))

        return results_list, None

    def execute(self, *args, **kwargs):
        err = self._make_connection()
        if err is not None:
            return err

        err = self._execute_query(*args, **kwargs)
        if err is not None:
            return err

        results, err = self._retrieve_data()
        if err is not None:
            return err

        return {"body": json.dumps(results), "headers": {}, "statusCode": 200,
                "isBase64Encoded": "false"}
