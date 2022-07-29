import requests 
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import logging

URL = 'https://sports.sportium.es/es/tennis'
START_URL = "https://sports.sportium.es"


TENNIS_SELECTOR = 'li[class="expander expander-collapsed sport-TENN"]'
MATCHES_TABLE_SELECTOR = 'table[class="coupon coupon-horizontal coupon-scoreboard video-enabled"]'
MATCH_SELECTOR = 'tr'
PLAYERS_SELECTOR = 'span[class="seln-label"]'
ODDS_SELECTOR = 'span[class="price dec"]'


def _get_soup_from_url(url: str):
    """Get soup object from url"""
    html = requests.get(url).text 
    soup = BeautifulSoup(html, "lxml")

    return soup


def scrape_sportium(type_tournaments_list):
    """Scrape every tennis tournament with a word from type_tournamnets_list on Sportium"""
    soup = _get_soup_from_url(URL)
    # Get tennis tag
    soup = soup.select_one(TENNIS_SELECTOR)
    # Get url for every tennis tournament
    tournaments_selectors = [f'a[href*="{t}"]' for t in type_tournaments_list]
    tags_list = [soup.select(selector) for selector in tournaments_selectors]
    tournament_urls = list(set([START_URL + tournament.get("href").strip() for type_tag in tags_list for tournament in type_tag]))
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    all_df = []
    logging.info([t.split('/')[-1] for t in tournament_urls])

    # Get matches from every tournament
    for t_url in tournament_urls:
        tournament = t_url.split("/")[-1]
        soup = _get_soup_from_url(t_url)

        matches_table = soup.select_one(MATCHES_TABLE_SELECTOR)
        if matches_table:
            time_list = []
            tournament_list = []
            player1 = []
            player2 = []
            odd1 = []
            odd2 = []

            matches = matches_table.select(MATCH_SELECTOR)

            for m in matches:

                try:
                    m.find('span', attrs = {'class':'period'}).get_text()
                    vivo_sign = "live"
                except:
                    vivo_sign = "pre-match"

                players_tags = m.select(PLAYERS_SELECTOR)
                odds_tags = m.select(ODDS_SELECTOR)

                if players_tags and odds_tags and vivo_sign == "pre-match":
                    players = [tag.get_text().strip() for tag in players_tags]
                    odds = [tag.get_text().strip() for tag in odds_tags]

                    player1.append(players[0].split("(")[0].strip())
                    player2.append(players[1].split("(")[0].strip())
                    odd1.append(odds[0])
                    odd2.append(odds[1])
                    tournament_list.append(tournament)
                    time_list.append(now)

            dicc = {
                'Player1' : player1,
                'Player2' : player2, 
                'Odd1' : odd1,
                'Odd2' : odd2,
                'Tournament' : tournament_list,
                "snap": now}

            df = pd.DataFrame(dicc)
            all_df.append(df)

        else: 
            logging.info(f"not fixtures found for {tournament}")

    df_fin = pd.concat(all_df)

    # Clean data
    df_fin["snap"] = pd.to_datetime(df_fin["snap"]).dt.strftime('%Y-%m-%d %H:%M')
    df_fin = df_fin.sort_values(["Player1","Player2","Tournament","snap"], ascending = True).reset_index(drop = True)

    logging.info(f"{len(df_fin)} matches scraped from {len(tournament_urls)} tournaments")

    return df_fin
