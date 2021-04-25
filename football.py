from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd
import re

app = Flask(__name__)

@app.route('/bot', methods=['POST'])
def process():
    incoming_msg = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()
    msg = resp.message()
    reply = ''
    
    if 'hello' in incoming_msg:
        reply = ('Hi, I am foot-bot, your English Premier League chatbot. '
                 'I can provide information about any season from the 2003-04 '
                 'Arsenal invincibles season to the 2019-20 season. You can '
                 'ask questions like:\n\nWhat were the scores in the Man City '
                 'vs Man United games in the 2016-17 season?\n\n How many '
                 'away goals did Everton concede in the 2005-06 season?\n\n '
                 'How many goals did Liverpool score in the 2013-14 season?')
        msg.body(reply)
        return str(resp)
    
    # read all datasets in epl_data
    df_names = []
    for x in range(19, 2, -1):
        if x < 10:
            df_names.append('20' + str(x).zfill(2) + '-' + str(x+1).zfill(2))
        else:    
            df_names.append('20' + str(x) + '-' + str(x+1))
    dfs = {}
    for i in df_names:
        dfs['df_' + i] = pd.read_csv('epl_data\\{}.csv'.format(i))
    
    #determine season
    seasons = re.findall('|'.join(df_names), incoming_msg)
    if len(seasons) == 0:
        reply = 'Please choose a season.'
        msg.body(reply)
        return str(resp)
    elif len(seasons) > 1:
        reply = 'Please choose only one season.'
        msg.body(reply)
        return str(resp)
    else:
        season = seasons[0]
      
    df = dfs['df_' + season]
    season_teams = df['HomeTeam'].unique().tolist()
    #lower() was applied to team names incoming_msg 
    season_teams = [y.lower() for y in season_teams]
    
    msg_teams = re.findall('|'.join(season_teams), incoming_msg)
    #first letter of each team is capitalized in datasets
    msg_teams = [z.title() for z in msg_teams]
        
    if len(msg_teams) == 0:
        reply = ('Sorry, team(s) not recognized. The team(s) that you entered ' 
        'may not have played in the EPL in that season.')
    #user wants info about one team's goals
    elif len(msg_teams) == 1:
        team = msg_teams[0]
        if 'goal' in incoming_msg:
            total_goals, home_goals, away_goals = 0, 0, 0
            if 'score' in incoming_msg:
                home_goals = df.loc[(df['HomeTeam'] == team),'FTHG'].sum()
                away_goals = df.loc[(df['AwayTeam'] == team),'FTAG'].sum()
            elif 'concede' in incoming_msg:
                home_goals = df.loc[(df['HomeTeam'] == team),'FTAG'].sum()
                away_goals = df.loc[(df['AwayTeam'] == team),'FTHG'].sum()
            else:
                reply = ("Invalid command. Did you forget 'score' or " 
                         "'concede' in your command?")
                msg.body(reply)
                return str(resp)
            
            if 'home' in incoming_msg:
                reply = str(home_goals)
            elif 'away' in incoming_msg:
                reply = str(away_goals)
            else:
                total_goals = int(home_goals) + int(away_goals)
                reply = str(total_goals)
        else:
            reply = "Invalid command. Did you forget 'goals' in your command?"
    #user wants info about matches two teams played
    elif len(msg_teams) == 2:
        df = df[(df['HomeTeam'].isin(msg_teams)) & 
                (df['AwayTeam'].isin(msg_teams))]
        for a in range(0, len(df)):
            reply += 'Game '+str(a+1)+':\n'+str(df['HomeTeam'].values[a]) \
            + ' (Home) vs ' \
            + str(df['AwayTeam'].values[a]) + '\nScore: ' \
            + str(df['FTHG'].values[a]) + '-' \
            + str(df['FTAG'].values[a]) + '\nDate: ' \
            + str(df['Date'].values[a])+ '\nReferee: ' \
            + str(df['Referee'].values[a]) + '\n\n'
    else:
        reply = 'Please choose only two or less teams.'
    msg.body(reply)
    return str(resp)
    
if __name__ == '__main__':
    app.run()