import pandas as pdimport numpy as npimport osfrom datetime import datetime, timedelta, timeimport plotly.graph_objects as goimport numpy as npimport mathimport warningswarnings.filterwarnings("ignore")def poisson(lambda_t):    return [math.exp(-1 * lambda_t) * (lambda_t ** k) / math.factorial(k) for k in range(21)]# assuming 20 minutes of half timedef minute_adjust(minute):    minute = int(minute)    if minute <= 45:        return minute    if 45 < minute <= 65:        return 45    if minute < 65:        return (minute-15)def poisson_pipeline(source): # source = event_id+'.csv'    df = pd.read_csv('data/'+source)        # remvoe NaN and ---    df = df[(~df.total_corner.isna()) & (df.total_corner!="---") & (df.total_corner!=" ---")]    df = df[(~df.chl_line.isna()) & (df.chl_line!="---")]    df = df[(~df.chl_hi.isna()) & (df.chl_hi!="---")]    df = df[(~df.chl_low.isna()) & (df.chl_low!="---")]    df['total_corner'] = df['total_corner'].apply(pd.to_numeric)    df['chl_line'] = df['chl_line'].apply(pd.to_numeric)    df['chl_hi'] = df['chl_hi'].apply(pd.to_numeric)    df['chl_low'] = df['chl_low'].apply(pd.to_numeric)    df = df.reset_index(drop = True)    df['hour'] = df.minutes.apply(lambda x: int(x.split(':')[0]))    df['minute'] = df.minutes.apply(lambda x: int(x.split(':')[1]))    df['minute'] = df.minute.apply(minute_adjust)    df['time'] = df.minute+60*df.hour    param_df = df[['minutes', 'chl_line']].groupby('minutes').mean()    param_df = param_df.rename(columns={'chl_line':'lambda'})    df = df.merge(param_df, how='outer', on='minutes')    df['lambda_t'] = df['lambda'] * (1 - df['time'] / max(max(df.time),110))    df['lambda_t_probs'] = df.lambda_t.apply(poisson)    df['target_corner'] = (df.chl_line - df.total_corner).apply(math.floor)    df['lower_prob'] = df.apply(lambda row: sum(row.lambda_t_probs[0:row.target_corner]), axis=1)    df['higher_prob'] = 1-df.lower_prob    return df[['minutes', 'chl_line', 'lower_prob', 'higher_prob']]def prob_graph(probs, event_id):    lines = list(set(probs.chl_line))    data_dict = {}    time_list = sorted(list(set(probs.minutes)))    for line in lines:        filtered_data = probs[probs.chl_line==line].sort_values(by=['minutes'])        data_dict[line] = pd.DataFrame({'minutes': time_list})        data_dict[line] = data_dict[line].merge(filtered_data, how='outer', on='minutes')    fig = go.Figure()    for line in lines:        fig.add_trace(go.Scatter(x=data_dict[line]['minutes'],                                  y=data_dict[line]['lower_prob'],                                  mode='lines',                                 name='lower than - {}'.format(line),                                  line=dict(width=1)))    fig.update_layout(title=event_id)    fig.show()    if __name__ == "__main__":    os.chdir('/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/')    for event_id in [file[:-4] for file in os.listdir('data_collection/data/') if '2020' in file]:        df = poisson_pipeline(event_id)        prob_graph(probs, event_id)