# -*- coding: utf-8 -*-
"""
Le script tel qu'il est met entre 4 et 5 heures à s'exécuter, donc à faire tourner quand on est certain de ne pas avoir à redémarrer sa machine à court terme.
Il est très certainement possible de l'améliorer pour récupérer les données en moins d'1 heure, mais pas eu le temps de chercher plus que ça.
"""

import praw
from psaw import PushshiftAPI
import tldextract
import pandas
import datetime as dt
import time

#Lignes ci-dessous à compléter avec ses propres valeurs. Il faut s'enregistrer auprès de Reddit. Voir https://www.reddit.com/wiki/api pour plus d'infos.
CLIENT_ID = ""
CLIENT_SECRET = ""
USERNAME = ""
PASSWORD = ""

#Connection à l'API Reddit
reddit = praw.Reddit(client_id=CLIENT_ID,
                      client_secret=CLIENT_SECRET,
                      user_agent="", #Il faut indiquer un user agent.
                      redirect_uri="http://localhost:8080", #voir la doc de l'API Reddit pour voir quoi définir ici. J'ai utilisé http://localhost:8080 pour faire tourner le script sur mon pc perso.
                      )
#Connection à l'API Pushshift
api = PushshiftAPI(reddit)

#date à partir de laquelle on veut commencer à récupérer les données 
start_date= dt.datetime(2010, 1, 1) #ici, 1 er janvier 2010
start_epoch= int(start_date.timestamp()) #convertir cette date en timestamp

#créer une liste dans laquelle on mettra progressivement les données issues de pushshift
all_list = []
#L'API pushshift ne permet de récupérer que 500 posts à chaque requête, il faut donc faire plusieurs requêtes pour récupérer les données sur de longues périodes.
#Ici, pour récupérer les données de /r/France, chaque requête récupère les données sur une période de 2 jours à partir de "start_date".
while True:
    end_date = start_date + dt.timedelta(days=2) #comme on veut récupérer les données sur 2 jours, définir un "end_date" comme étant égal à start_date + 2 jours
    end_epoch = int(end_date.timestamp()) #convertir end_date en timestamp

    # 2 lignes ci-dessous à décommenter, si on veut voir la progression du script (affiche les dates en train d'être requêtées)
    # print("début:", "-".join([str(start_date.day), str(start_date.month), str(start_date.year)])) #décommenter si on veut afficher la progression
    # print("fin:", "-".join([str(end_date.day), str(end_date.month), str(end_date.year)])) #décommenter si on veut afficher la progression


    #définir la requête sur l'API pushshift:
    data = list(api.search_submissions(
                  #faire attention à bien passer un integer et pas un float pour "after" et "before", sinon l'API renvoie des erreurs ou bien la requête tourne dans le vide.
                  after=int(start_epoch), 
                  before=int(end_epoch),
                  subreddit='france', #le subreddit dont on veut récupérer les données
                  #définir les données qu'on veut récupérer. Je ne sais pas si c'est vraiment nécessaire en fait (voir plus bas à partir de la ligne 75)
                  filter=['full_link', 'subreddit', 'id', 'created_utc', 'score', 'num_comments', 'author', 'title', 'selftext', "domain"],
                  limit=500,
                                    )
        )
    #si aucun post n'a été récupéré sur la période de deux jours, il faut décaler un peu la date de départ, sinon le script tourne indéfiniment dans le vide
    if len(data) == 0:
        start_epoch = end_epoch + 300 #data[0].created_utc
        start_date = dt.datetime.fromtimestamp(start_epoch)
        continue
    all_list.extend(data)
    start_epoch = data[0].created_utc
    start_date = dt.datetime.fromtimestamp(start_epoch)
    #la limite de l'API de pushshift est actuellement de 120 requêtes par minute (voir https://api.pushshift.io/meta),
    #... mais on n'est pas aux pièces et on peut se limiter à 60 requêtes par minute pour éviter de surcharger l'API -> time.sleep(1)
    time.sleep(1)

    if start_epoch > 1614553200: #définir le timestamp jusqu'auquel on veut récupérer les données (ici 1614553200 = 28 février 2021)
        break

#définir une liste "posts", qui contiendra des dictionnaires avec les données de chaque post. On transformera cette liste en dataframe pandas.
posts = []
for post in all_list:
    post_dict = {}
    post_dict["created_utc"] = post.created_utc
    post_dict["created"] = post.created
    post_dict["score"] = post.score
    post_dict["total_awards_received"] = post.total_awards_received
    post_dict["title"] = post.title
    post_dict["selftext"] = post.selftext
    post_dict["id"] = post.id
    post_dict["author"] = post.author
    post_dict["url"] = post.url
    post_dict["shortlink"] = post.shortlink
    # post_dict["flair"] = post.flair #décommenter pour récupérer le flair (attention, ce n'est pas une chaine de caractères, mais un objet praw à requêter à part)
    post_dict["upvote_ratio"] = post.upvote_ratio
    # post_dict["removed_by"] = post.removed_by #vide pour tous les posts de /r/France
    post_dict["num_comments"] = post.num_comments
    post_dict["is_self"] = post.is_self
    post_dict["is_reddit_media_domain"] = post.is_reddit_media_domain
    post_dict["is_robot_indexable"] = post.is_robot_indexable
    post_dict["domain"] = post.domain
    posts.append(post_dict)

#on crée un dataframe à partir de cette liste "submissions" (332618 items)
df = pandas.DataFrame(posts)
df = df.drop_duplicates() #si jamais on a récupéré par erreur des doublons

#extraire le domaine principal (pour pouvoir regrouper les sites du type etudiant.figaro.fr et figaro.fr)
df["main_domain"] = df["domain"].apply(lambda x: tldextract.extract(x).domain + "."+tldextract.extract(x).suffix)

#convertir le format epoch de la date de publi en date lisible par un humain
df["date"] = df["created_utc"].apply(lambda x: dt.datetime.fromtimestamp(x).date())
df["date"] = pandas.to_datetime(df['date'],format='%Y-%m-%d')

#export en csv
df.to_csv("rFrance_2010-2021.csv", index=False)
