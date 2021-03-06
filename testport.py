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

fig = make_subplots(rows=2, cols=1, shared_xaxes=True,)

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
    name = tmp.티커.values[0]
            
    fig.add_annotation(x=startindex,
                       y=np.mean(result.loc[startindex,:].values[:4]),
                       text=f"add: {name} 약{round(int(value),-1):,}",
                       ax=20,
                       ay=-30,
                       bordercolor="#c7c7c7",
                       borderwidth=2,
                       borderpad=4,
                       bgcolor="#ff7f0e",
                       opacity=0.8,
                       arrowwidth=2,
                       arrowcolor="#636363",
                       showarrow=True,
                       arrowhead=2,
                       row=1, col=1)
    if not num:
        continue
    color1, color2 = 'RoyalBlue', 'LightSkyBlue'
    if np.mean(result.loc[startindex,:].values[:4]) < \
        np.mean(result.loc[result.index < startindex,:].values[-1][:4]):
        color1, color2 = 'darkred', 'lightsalmon'
    fig.add_shape(type="rect",
                  x0=result.loc[result.index < startindex,:].index[-1],
                  y0=np.mean(result.loc[result.index < startindex,:].values[-1][:4]),
                  x1=startindex,
                  y1=np.mean(result.loc[startindex,:].values[:4]),
                  line=dict(color=color1,width=1,),
                  fillcolor=color2,
                  opacity=0.7,
                  row=1, col=1)
    
line = go.Scatter(x=result.index, y=result.mdd, mode='lines', name='MDD')
fig.add_trace(line, row=2, col=1)

fig.update_layout(height=500, width=1000,
                  margin=dict(l=10, r=10, t=10, b=10),
                  yaxis=dict(autorange = True, fixedrange= False, tickformat=",", domain=[0.15, 1]),
                  xaxis=dict(tickformat='%Y-%m-%d', rangeslider=dict(visible=False)),
                  yaxis2=dict(autorange = True, fixedrange= False, tickformat=",", domain=[0, 0.1]),
                  xaxis2=dict(tickformat='%Y-%m-%d'))

fig.show()
