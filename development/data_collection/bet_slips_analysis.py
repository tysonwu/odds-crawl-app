import pandas as pd
import numpy as np
import re
import plotly.graph_objects as go


result = pd.read_csv('/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/result_collection/match_corner_result.csv')
data = pd.read_csv('bet_slips/receipt.txt', sep=";", header=None)
data = data[[0,8,14,15,16]]
data = data.rename(columns={0:'event_id',
                            8: 'send_bet_status',
                            14: 'hilow_content',
                            15: 'odds',
                            16: 'bet_amount'})

data['hilow'] = data['hilow_content'].apply(lambda x: x.split("[")[0])
data['line'] = data['hilow_content'].apply(lambda x: re.sub('@|]','',x.split("[")[-1]))
data['bet_amount'] = data['bet_amount'].apply(lambda x: re.sub('\$','',x).strip())
data['bet_amount'] = data['bet_amount'].apply(pd.to_numeric)
data['odds'] = data['odds'].apply(pd.to_numeric)
data['line'] = data['line'].apply(pd.to_numeric)
data = data[data.send_bet_status.str.contains('Accepted')]
del data['hilow_content']

# merge with result
data = data.merge(result[['event_id','result_corner']], how='inner', on='event_id')
data['result_corner'] = data['result_corner'].apply(pd.to_numeric)
data['is_win'] = np.where(data.hilow == 'Low',
	np.where(data.line>data.result_corner,1,0),
	np.where(data.line<data.result_corner,1,0))
data['pnl'] = np.where(data.is_win == 1, data.odds - 1, -1)
data['pnl_actual'] = data.bet_amount * data.pnl

print(data[['event_id','bet_amount','hilow','line','is_win','pnl','pnl_actual']].tail(40))
print('\nCurrent running profit/loss: $ {} for $ 1 in each bet'.format(round(data['pnl'].sum(),2)))
print('Current running actual profit/loss: $ {} since starting stack'.format(round(data['pnl_actual'].sum(),2)))
#u.graph(data.index, data.pnl.cumsum(), 'Running returns')

# plotly plot
line_color = '#FFA65A' # default muted blue, safety orange
font_color = '#c5c5c5'
grid_color = '#42494f'
paper_bgcolor = '#303538'
plot_bgcolor = '#303538'

fig = go.Figure(data=go.Scatter(x=data.index, y=data.pnl_actual.cumsum(), line=dict(color=line_color)))
fig.update_layout(title='Actual Running Profit or Loss',
                   xaxis=dict(title='Current running actual profit/loss: $ {} since starting stack '.format(round(data['pnl_actual'].sum(),2)),
                              gridcolor=grid_color,
                              zerolinecolor=grid_color),
                   yaxis=dict(title='Amount($)',
                              gridcolor=grid_color,
                              zerolinecolor=grid_color),
                   font=dict(color=font_color),
                   paper_bgcolor=plot_bgcolor,
                   plot_bgcolor=plot_bgcolor,
                   template='plotly_dark')
fig.show(width=800, height=400)
