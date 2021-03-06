from cassandra.cluster import Cluster

cluster = Cluster(['cassandra'])
session = cluster.connect()
try:
    session.execute("use tweets")
except Exception as e:
    print(str(e))
    session.execute("create keyspace tweets with replication = {'class': 'SimpleStrategy', 'replication_factor': '1'}")
    session.execute("use tweets")


def add_tweet(data):
    hashtags = data.get('hashtags', [])
    content = data.get('text', '')
    source = data.get('source', '')
    full = data.get('full_text', '')
    user = data.get('user', {}).get('name', '')
    profile_image = data.get('user', {}).get('profile_image_url_https')
    for hashtag in hashtags:
        insert_tweet_data = insert_tweet.bind([hashtag, content, source, user, profile_image, full])
        session.execute(insert_tweet_data)


def get_last_tweets(hashtag):
    cassandra_tweets_prepare = session.prepare("select * from tweets_by_hashtag where hashtag=? limit 10")
    cassandra_tweets_query = cassandra_tweets_prepare.bind(['#'+hashtag])
    cassandra_tweets = session.execute(cassandra_tweets_query)
    tweets = []
    for tweet in cassandra_tweets:
        tweets.append({
            'text': tweet.content,
            'hashtag': tweet.hashtag,
            'user': tweet.user,
            'profile_image': tweet.profile_image
        })

    return {'tweets': tweets[::-1]}


def get_counts():
    # get tables count
    python = session.execute("select count(*) from tweets_by_hashtag where hashtag='#python'")[0][0]
    iot = session.execute("select count(*) from tweets_by_hashtag where hashtag='#iot'")[0][0]
    bigdata = session.execute("select count(*) from tweets_by_hashtag where hashtag='#bigdata'")[0][0]

    return {
        'python': python,
        'iot': iot,
        'bigdata': bigdata
    }


def create_tables():
    # search tweet by hashtag
    session.execute(
        """
        create table tweets_by_hashtag (
            hashtag text,
            id timeuuid,
            content text,
            source text,
            user text,
            profile_image text,
            full_text text,
            primary key ((hashtag), id)
        ) with clustering order by(id desc);
        """
    )


try:
    session.execute("select count(*) from tweets_by_hashtag where hashtag='#python'")
except Exception as e:
    print("Creating tables...")
    create_tables()
    print("Tables created...")


insert_tweet = session.prepare(
    """
    insert into  tweets_by_hashtag (
        hashtag,
        id,
        content,
        source,
        user,
        profile_image,
        full_text
        ) values (?, now(), ?, ?, ?, ?, ?);
    """
)
