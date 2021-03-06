import pandas as pd
import numpy as np
import datetime
import FinanceDataReader as fdr
from plotly.subplots import make_subplots
import plotly.graph_objects as go

data = pd.read_excel('bnp.xlsx').astype(dict(티커='str', 구매가='float', 화폐='str'))
data.구매일 = pd.to_datetime(data.구매일, format='%Y%m%d')
day2 = pd.to_datetime(datetime.datetime.today())

fdata = dict()
rdata = dict()
for item in data.티커.drop_duplicates():
    tmp = data.loc[data.티커 == item, :]
    start = tmp.구매일.sort_values(ascending=True).iloc[0]
    fdata[item] = fdr.DataReader(item, start, day2)
    rdata[item] = pd.DataFrame(columns=list(fdata[item].columns) + ['value'],
                               index = pd.date_range(data.구매일.sort_values(ascending=True).iloc[0],
                                                     day2,
                                                     freq = 'D')
                              ).drop(['Change', 'Volume'], axis=1)
    rdata[item] = rdata[item].fillna(0)
    for row in tmp.values:
        pdata = pd.DataFrame(index = pd.date_range(data.구매일.sort_values(ascending=True).iloc[0],
                                                   day2,
                                                   freq = 'D')
                            )
        pdata = pdata.loc[pdata.index >= row[1], :]
        pdata = pd.merge(pdata, fdata[item].loc[fdata[item].index >= row[1],:],
                         left_index=True, right_index=True, how='outer').\
                            drop(['Change', 'Volume'], axis=1)
        pdata['value'] = row[-3]
        try:
            pdata.loc[pdata.index[1:], 'value'] = pdata.Close[1:]
        except:
            pass
        pdata['value_change'] = 0
        pdata = pdata.fillna(method='ffill')
        pdata = pdata.reindex(rdata[item].index)
        pdata = pdata.fillna(0)
        if row[-1] == '달러':
            if 'USD/KRW' not in fdata.keys():
                fdata['USD/KRW'] = fdr.DataReader('USD/KRW',
                                                  data.구매일.sort_values(ascending=True).iloc[0],
                                                  day2).drop('Change', axis=1)
            pdata.loc[:,pdata.columns[:4]] = pdata * \
                fdata['USD/KRW'][pdata.columns[:4]].reindex(rdata[item].index).fillna(method='ffill')
            pdata['value'] = pdata.value * \
                fdata['USD/KRW'].Close.reindex(rdata[item].index).fillna(method='ffill')
        
        rdata[item] = rdata[item] + pdata[rdata[item].columns]*row[-2]
    rdata[item] = \
        rdata[item].loc[(rdata[item].iloc[:,:4] - \
                         rdata[item].iloc[:,:4].shift(1)).fillna(0).sum(axis=1) + \
                        ([1]+[0 for _ in range(rdata[item].shape[0]-1)]) != 0,:]
    rdata[item]['value_change'] = \
        (rdata[item].value - rdata[item].value.shift(1)) / rdata[item].value.shift(1)
    rdata[item]['value_change'] = rdata[item].value_change.fillna(0)
    rdata[item]['add_value'] = [1 if x in tmp.구매일.values else 0 for x in rdata[item].index]
    

result = pd.DataFrame(columns=list(rdata[list(rdata.keys())[0]].columns),
                      index = pd.date_range(data.구매일.sort_values(ascending=True).iloc[0],
                                            day2,
                                            freq = 'D')
                     )
result = sum([x.reindex(result.index).fillna({'add_value':0}).fillna(method='ffill') for x in rdata.values()])
result['value_change'] = \
    (result.value - result.value.shift(1)) / result.value.shift(1)
result['value_change'] = result.value_change.fillna(0)
result = \
    result.loc[(result.iloc[:,:4] - result.iloc[:,:4].shift(1)).sum(axis=1) + \
               ([1]+[0 for _ in range(result.shape[0]-1)]) != 0,:]
result.loc[:,result.columns[:4]] = result.loc[:,result.columns[:4]].round(-1)
result['mdd'] = 0
for num in range(1,result.shape[0]):
    result.loc[result.index[num:], 'mdd'] = result.loc[result.index[num:], 'mdd'] +\
                                            result.values[num][-3] - result.values[num-1][-3]
    if result.loc[result.index[num], 'mdd'] > 0:
        result.loc[result.index[num:], 'mdd'] = 0

fig = make_subplots(rows=3, cols=1, shared_xaxes=True,                 
                    subplot_titles=('포트폴리오','MDD','변동성'),
                    row_heights=[0.7, 0.15, 0.15],
                    vertical_spacing=0.05
                   )

candle = go.Candlestick(open=result.Open, close=result.Close,
                        high=result.High, low=result.Low,
                        x=result.index,
                        name='포트폴리오')
fig.add_trace(candle, row=1, col=1)

for num, row in enumerate(result.loc[result.add_value >= 1,:].values):
    startindex = result.loc[result.add_value >= 1,:].index[num]
    tmp = data.copy().loc[data.구매일 == startindex,:]
    if '달러' in tmp.화폐.values:
        tmp.loc[tmp.화폐 == '달러','구매가'] = tmp.loc[tmp.화폐 == '달러','구매가'].values * \
            fdata['USD/KRW'].loc[fdata['USD/KRW'].index == startindex, 'Close'].values
    tmp['value'] = tmp.구매가 * tmp.구매개수
    value = tmp.value.sum()
    name = tmp.티커.values
            
#     fig.add_annotation(x=startindex,
#                        y=np.mean(result.loc[startindex,:].values[:4]),
#                        text=f"add: {name} 약{round(int(value),-1):,}",
#                        ax=20,
#                        ay=-30,
#                        bordercolor="#c7c7c7",
#                        borderwidth=2,
#                        borderpad=4,
#                        bgcolor="#ff7f0e",
#                        opacity=0.8,
#                        arrowwidth=2,
#                        arrowcolor="#636363",
#                        showarrow=True,
#                        arrowhead=2,
#                        row=1, col=1)
    if not num:
        continue
    legend = True
    if num > 1:
        legend = False
    color1, color2 = 'RoyalBlue', 'LightSkyBlue'
    if np.mean(result.loc[startindex,:].values[:4]) < \
        np.mean(result.loc[result.index < startindex,:].values[-1][:4]):
        color1, color2 = 'darkred', 'lightsalmon'
    x0 = result.loc[result.index < startindex,:].index[-1]
    x1 = startindex
    y0 = np.mean(result.loc[result.index < startindex,:].values[-1][:4])
    y1 = np.mean(result.loc[startindex,:].values[:4])
#     fig.add_shape(type="rect",
#                   x0=x0, y0=y0, x1=x1, y1=y1,
#                   line=dict(color=color1,width=1,),
#                   fillcolor=color2,
#                   opacity=0.7,
#                   row=1, col=1)
    fig.add_trace(
        go.Scatter(x=[x0, x0, x1, x1, x0],
                   y=[y0, y1, y1, y0, y0],
                   fill='toself',
                   line_color=color1,
                   fillcolor=color2,
                   mode='lines',
                   line=dict(width=1),
                   name='추가금',
                   opacity=0.7,
                   legendgroup='추가금',
                   showlegend=legend,
                   text=f"add: {name} 약{round(int(value),-1):,}"
        ), row=1, col=1
    )
    
line = go.Scatter(x=result.index, y=result.mdd, mode='lines', line=dict(color='red'), showlegend=False, name='MDD')
fig.add_trace(line, row=2, col=1)

zerodays = result.loc[((result.mdd == 0) & (result.mdd.shift(1) != 0)) | ((result.mdd != 0) & (result.mdd.shift(1) == 0)),:].index
for num in range(len(zerodays)):
    if not num % 2:
        continue
    x0 = zerodays[num]
    if num+1 == len(zerodays):
        x1 = result.index[-1]
    else:
        x1 = zerodays[num+1]
    fig.add_vrect(
        x0=x0, x1=x1,
        fillcolor="LightSalmon", opacity=0.5,
        layer="below", line_width=0,
        row=2, col=1)

riskdata = result.loc[(result.add_value == 0) & (result.add_value.shift(1) == 0),:]
risk = go.Bar(x=riskdata.index, y=riskdata.value_change,
              marker_color='black',
              showlegend=False,
              name='변동성')
fig.add_trace(risk, row=3, col=1)

riskstd = np.std(result.loc[(result.add_value == 0) & (result.add_value.shift(1) == 0),:].value_change)
fig.add_hrect(
    y0=-riskstd, y1=riskstd,
    fillcolor="yellow", opacity=0.4,
    layer="below", line_width=0,
    row=3, col=1)
fig.add_hrect(
    y0=-riskstd*2, y1=-riskstd,
    fillcolor="orange", opacity=0.4,
    layer="below", line_width=0,
    row=3, col=1)
fig.add_hrect(
    y0=riskstd, y1=riskstd*2,
    fillcolor="orange", opacity=0.4,
    layer="below", line_width=0,
    row=3, col=1)
fig.add_hrect(
    y0=-riskstd*3, y1=-riskstd*2,
    fillcolor="red", opacity=0.4,
    layer="below", line_width=0,
    row=3, col=1)
fig.add_hrect(
    y0=riskstd*2, y1=riskstd*3,
    fillcolor="red", opacity=0.4,
    layer="below", line_width=0,
    row=3, col=1)
# fig.add_hrect(
#     y0=-riskstd, y1=riskstd,
#     fillcolor="yellow", opacity=0.5,
#     layer="below", line_width=0,
#     row=3, col=1)

fig.update_layout(template='plotly_white',
                  height=500, width=1000,
                  margin=dict(l=10, r=10, t=30, b=10),
                  yaxis=dict(autorange = True, fixedrange= False, tickformat=",",),# domain=[0.3, 1]),
                  xaxis=dict(tickformat='%Y-%m-%d', rangeslider=dict(visible=False)),
                  yaxis2=dict(autorange = True, fixedrange= False, tickformat=",",),# domain=[0.15, 0.25]),
                  xaxis2=dict(tickformat='%Y-%m-%d'),
                  yaxis3=dict(autorange = True, fixedrange= False, tickformat=",",),# domain=[0, 0.1]),
                  xaxis3=dict(tickformat='%Y-%m-%d'),
                  legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.05, borderwidth=1)
                 )

fig.show()
