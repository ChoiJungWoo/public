import pandas as pd
import numpy as np
import datetime
import FinanceDataReader as fdr
from pandas_datareader import data as dtread
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
from dateutil.relativedelta import relativedelta
import copy
import re

class bnp:
    def __init__(self):
        # 매매 기록
        self.__data = pd.DataFrame(columns=['티커', '구매일', '구매가', '구매개수', '화폐'])
        # 상품 차트
        self.__fdata = dict()
        # 매매 기록 * 상품 차트
        self.__rdata = dict()
        # rdata 합산
        self.__result = None
        # 그래프
        self.fig = None
        # 벤치용 포폴
        self.bench = dict(
            영구포폴 = (('vti','tlt','GC=F','^IRX'),(.25,.25,.25,.25)),
            올웨더 = (('vti','tlt','ief','GC=F','CL=F'),(.3,.4,.15,.075,.075)),
            황금나비 = (('vti','ijs','tlt','shy','GC=F'),(.2,.2,.2,.2,.2))
        )
        self.__rbench = []
    
    @property
    def data(self):
        return copy.deepcopy(self.__data)
        
    @data.setter
    def data(self, df):
        data = df.copy().astype(dict(티커='str', 구매가='float', 화폐='str'))
        self.__data = data
    
    @property
    def fdata(self):
        return copy.deepcopy(self.__fdata)
    
#     @fdata.setter
#     def fdata(self, dt):
#         self.__fdata = dt
    
    @property
    def rdata(self):
        return copy.deepcopy(self.__rdata)
    
#     @rdata.setter
#     def rdata(self, dt):
#         self.__rdata = dt
        
    @property
    def result(self):
        return copy.deepcopy(self.__result)
    
#     @result.setter
#     def result(self, dt):
#         self.__result = dt

    @property
    def rbench(self):
        return copy.deepcopy(self.__rbench)
 
    def add_row(self, row):
        tmp = pd.DataFrame([row], columns=['티커', '구매일', '구매가', '구매개수', '화폐'])
        self.__data = self.__data.append(tmp).reset_index(drop=True)
    
    def make_result(self):
        fdata = dict()
        rdata = dict()
        data = self.data
        data.구매일 = pd.to_datetime(data.구매일, format='%Y%m%d')
#         self.data = data
        day2 = pd.to_datetime(datetime.datetime.today())
        # 매매 기록의 각 종목에 대해 따로 계산 후 합치기
        for item in data.티커.drop_duplicates():
            tmp = data.copy().loc[self.data.티커 == item, :]
            start = tmp.구매일.sort_values(ascending=True).iloc[0]
            # 상품 차트 정보 다운로드
            fdata[item] = fdr.DataReader(item, start, day2)
            # 매매 * 상품 사전 준비
            rdata[item] = pd.DataFrame(columns=list(fdata[item].columns) + ['value', 'value_change'],
                                       index = pd.date_range(data.구매일.\
                                                                 sort_values(ascending=True).iloc[0],
                                                             day2,
                                                             freq = 'D')
                                      ).drop(['Change', 'Volume'], axis=1)
            rdata[item] = rdata[item].fillna(0)
            # 각 매매 기록에 대한 데이터 생성 후 합치기
            for row in tmp.values:
                # row = [티커 구매일 구매가 구매개수 화폐]
                pdata = pd.DataFrame(index = pd.date_range(data.구매일.sort_values(ascending=True).iloc[0],
                                                           day2,
                                                           freq = 'D')
                                    )
                pdata = pdata.loc[pdata.index >= row[1], :]
                # 매매일 이후 자료만 활성화
                pdata = pd.merge(pdata, fdata[item].loc[fdata[item].index >= row[1],:],
                                 left_index=True, right_index=True, how='outer').\
                                    drop(['Change', 'Volume'], axis=1)
                # value: 구매가격 or 판매가격 or 보유자산
                pdata['value'] = row[-3]
                # today = 구매일인 경우 에러 발생하므로
                try:
                    pdata.loc[pdata.index[1:], 'value'] = pdata.Close[1:]
                except:
                    pass
                pdata['value_change'] = 0
                pdata = pdata.reindex(rdata[item].index)
                # 휴일인 경우 결측치 발생하므로 가장 최근 이전 데이터로 대체
                pdata = pdata.fillna(method='ffill').fillna(0)
                # 달러 자산의 경우 원화로 환산
                # 당시 환율 반영
                if row[-1] == '달러':
                    if 'USD/KRW' not in fdata.keys():
                        fdata['USD/KRW'] = fdr.DataReader('USD/KRW',
                                                          data.구매일.sort_values(ascending=True).iloc[0],
                                                          day2).drop('Change', axis=1)
                    pdata.loc[:,pdata.columns[:4]] = pdata * \
                        fdata['USD/KRW'][pdata.columns[:4]].reindex(rdata[item].index).fillna(method='ffill')
                    pdata['value'] = pdata.value * \
                        fdata['USD/KRW'].Close.reindex(rdata[item].index).fillna(method='ffill')

                # 구매일 이후 자료 * 구매 개수 자료를 합산
                rdata[item] = rdata[item] + pdata[rdata[item].columns]*row[-2]
                
            # 한국, 미국 둘 다 휴일인 경우 제외
            rdata[item] = \
                rdata[item].loc[(rdata[item].iloc[:,:4] - \
                                 rdata[item].iloc[:,:4].shift(1)).fillna(0).sum(axis=1) + \
                                ([1]+[0 for _ in range(rdata[item].shape[0]-1)]) != 0,:]
            # 보유 자산 변동성 확인
            rdata[item]['value_change'] = \
                (rdata[item].value - rdata[item].value.shift(1).fillna(0))\
                    / rdata[item].value.shift(1)
            rdata[item]['value_change'] = rdata[item].value_change.fillna(0)
            # 매매일자 표시
            rdata[item]['add_value'] = [1 if x in tmp.구매일.values else 0 for x in rdata[item].index]

        self.__fdata = fdata
        self.__rdata = rdata
        
        result = pd.DataFrame(columns=list(rdata[list(rdata.keys())[0]].columns),
                              index = pd.date_range(data.구매일.sort_values(ascending=True).iloc[0],
                                                    day2,
                                                    freq = 'D')
                             )
        # 각 상품 합쳐서 계산
        result = sum([x.reindex(result.index).fillna({'add_value':0}).fillna(method='ffill')
                      for x in rdata.values()])
        # 보유 자산 총합 변동성 계산
        result['value_change'] = \
            (result.value - result.value.shift(1)) / result.value.shift(1)
        result['value_change'] = result.value_change.fillna(0)
        # 한국, 미국 둘 다 휴일인 경우 제외
        result = \
            result.loc[(result.iloc[:,:4] - result.iloc[:,:4].shift(1)).sum(axis=1) + \
                       ([1]+[0 for _ in range(result.shape[0]-1)]) != 0,:]
        # 10원 단위로 반올림
        result.loc[:,result.columns[:4]] = result.loc[:,result.columns[:4]].round(-1)
        result.loc[result.add_value > 0, 'value_change'] = 0
        # MDD계산
        result['mdd'] = (result.value / result.value.cummax() - 1).round(4)
#         result['mdd'] = 0
#         for num in range(1,result.shape[0]):
#             result.loc[result.index[num:], 'mdd'] = result.loc[result.index[num:], 'mdd'] +\
#                                                     result.values[num][-4] - result.values[num-1][-4]
#             if result.loc[result.index[num], 'mdd'] > 0:
#                 result.loc[result.index[num:], 'mdd'] = 0
                
        self.__result = result
        
#         data = self.data
#         data.구매일 = data.구매일.dt.strftime('%Y%m%d')
#         self.data = data
    
    def make_bench(self):
        result = []
        tmp = [make_pvc(*value, date=self.__result.index[0] - relativedelta(days=7)).rename(key) for key,value in self.bench.items()]
        for item in tmp:
            change = item.loc[item.index >= self.__result.index[0]] + 1
            res = pd.Series(0, index=change.index)
            for row in self.data.copy().values:
                dt = pd.to_datetime(row[1])
                if dt < item.index[0]:
                    continue
                val = row[2] * row[3]
                if row[-1] == '달러':
                    val *= self.__fdata['USD/KRW'].Close.loc[self.__fdata['USD/KRW'].Close.index == dt].values[0]
                tmpres = change.loc[change.index >= dt].cumprod()
                tmpres = tmpres / tmpres.values[0]
                tmpres = tmpres * val
                tmpres = tmpres.reindex(res.index).fillna(method='ffill').fillna(0)
                res += tmpres
            result.append(res.rename(item.name))
        self.__rbench = copy.deepcopy(result)
    
    def make_figure(self, pm=''):
        
        benchcolor = [x for n,x in enumerate(px.colors.qualitative.Dark24) if n not in [1,2,3,4,7,8,10,11,12,20,23]]
        
        data = self.__data
        data.구매일 = pd.to_datetime(data.구매일, format='%Y%m%d')
#         self.data = data
        
        pm = re.sub('[^%]{1}', ',', pm[:min(3,len(pm))] + ',,,'[min(3,len(pm)):])
        
        # 전체 figure 설정
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True,                 
                            subplot_titles=('포트폴리오','현재 자산 - 추가금','MDD','변동성'),
                            row_heights=[0.55, 0.15, 0.15, 0.15],
                            vertical_spacing=0.05
                           )
        
        rownum = 1

        # 1. 포폴 차트
        candle = go.Candlestick(open=self.__result.Open, close=self.__result.Close,
                                high=self.__result.High, low=self.__result.Low,
                                x=self.__result.index,
                                name='포트폴리오')
        fig.add_trace(candle, row=rownum, col=1)            

        # 1-1. 추가금
        for num, row in enumerate(self.__result.loc[self.__result.add_value >= 1,:].values):
            startindex = self.__result.loc[self.__result.add_value >= 1,:].index[num]
            tmp = data.copy().loc[data.구매일 == startindex,:]
            if '달러' in tmp.화폐.values:
                tmp.loc[tmp.화폐 == '달러','구매가'] = tmp.loc[tmp.화폐 == '달러','구매가'].values * \
                    self.__fdata['USD/KRW'].reindex(self.__result.index).fillna(method='ffill').\
                        loc[self.__fdata['USD/KRW'].index == startindex, 'Close'].values[0]
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
            

            if num:
                x0 = self.__result.loc[self.__result.index < startindex,:].index[-1]
                y0 = np.mean(self.__result.loc[self.__result.index < startindex,:].values[-1][:4])
                legend = False
                if np.mean(self.__result.loc[startindex,:].values[:4]) < \
                    np.mean(self.__result.loc[self.__result.index < startindex,:].values[-1][:4]):
                    color1, color2 = 'darkred', 'lightsalmon'
                else:
                    color1, color2 = 'RoyalBlue', 'LightSkyBlue'
            else:
                x0 = startindex - relativedelta(days=1)
                y0 = 0
                legend = True
                color1, color2 = 'RoyalBlue', 'LightSkyBlue'
            x1 = startindex            
            y1 = np.mean(self.__result.loc[startindex,:].values[:4])
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
                ), row=rownum, col=1
            )
            
        fig.add_hrect(y0=0, y1=0, line_width=2, fillcolor="black", opacity=1, row=rownum, col=1)
        
        # 1-2. 벤치마크
        if self.__rbench:
            for num, item in enumerate(self.__rbench):
                benchtxt = [f"{x.strftime('%Y-%m-%d')}: {int(round(y,-1)):,}"
                            for x,y in zip(item.index, item.values)]
                fig.add_trace(
                    go.Scatter(x=item.index,
                               y=item.values,
                               mode='lines',
                               line=dict(width=2, color=benchcolor[num]),
                               name=item.name,
                               legendgroup=item.name,
                               visible='legendonly',
                               text=benchtxt,
                               hovertemplate='%{text}'
                    ), row=rownum, col=1)
            
        
        rownum += 1
        
        # 2. 현재자산 - 추가금
        realvalue = self.__result.copy().value.to_frame()
        if self.__rbench:
            realbench = []
            for item in self.__rbench:
                realbench.append(item.copy())
        for row in data.values:
            row_v = row[2]
            if row[-1] == '달러':
                row_v = row_v * self.__fdata['USD/KRW'].reindex(self.__result.index).fillna(method='ffill').\
                                    loc[self.__fdata['USD/KRW'].index == row[1], 'Close'].values[0]
            realvalue.loc[realvalue.index >= row[1],:] = \
                realvalue.loc[realvalue.index >= row[1],:] - row_v*row[-2]
            if self.__rbench:
                for item in realbench:
                    if item.index[0] > row[1]:
                        break
                    realbench = realbench[1:]
                    item.loc[item.index >= row[1]] = \
                        item.loc[item.index >= row[1]] - row_v*row[-2]
                    realbench.append(item)
        if pm[0] == '%':
            realvalue['value'] = realvalue.value / self.__result.value
            if self.__rbench:
                for item, origin in zip(realbench, self.__rbench):
                    realbench = realbench[1:]
                    realbench.append(item / origin)
        maxcut = realvalue.loc[realvalue.value == realvalue.value.max(),'value'].index
        try:
            maxcut = maxcut[0]
        except:
            pass
        realvalue1 = realvalue.loc[realvalue.index <= maxcut, :]
        realvalue2 = realvalue.loc[realvalue.index >= maxcut, :]
        
        if pm[0] == '%':
            realtxt = [f"{x.strftime('%Y-%m-%d')}: {y:.2%}" 
                       for x,y in zip(self.__result.index, realvalue1.value)]
        else:
            realtxt = [f"{x.strftime('%Y-%m-%d')}: {int(round(y,-1)):,}" 
                       for x,y in zip(self.__result.index, realvalue1.value)]
        realine = go.Scatter(x=realvalue1.index,
                             y=realvalue1.value,
                             mode='lines',
                             line=dict(color='indigo'),
                             fill='tozeroy',
                             showlegend=False,
                             text=realtxt,
                             hovertemplate='%{text}',
                             name='현재자산 - 추가금')
        fig.add_trace(realine, row=rownum, col=1)
        
        if pm[0] == '%':
            realmaxtxt = [f"{x.strftime('%Y-%m-%d')}: {y:.2%}"
                          for x,y in zip(self.__result.index, realvalue2.value)]
        else:
            realmaxtxt = [f"{x.strftime('%Y-%m-%d')}: {int(round(y,-1)):,}" 
                          for x,y in zip(self.__result.index, realvalue2.value)]
        realine_max = go.Scatter(x=realvalue2.index,
                                 y=realvalue2.value,
                                 mode='lines',
                                 line=dict(color='darkgreen'),
                                 fill='tozeroy',
                                 showlegend=False,
                                 text=realmaxtxt,
                                 hovertemplate='%{text}',
                                 name='현재자산 - 추가금')
        fig.add_trace(realine_max, row=rownum, col=1)
        
        if self.__rbench:
            for num, item in enumerate(realbench):
                if pm[0] == '%':
                    benchtxt = [f"{x.strftime('%Y-%m-%d')}: {y:.2%}" 
                               for x,y in zip(item.index, item.values)]
                else:
                    benchtxt = [f"{x.strftime('%Y-%m-%d')}: {int(round(y,-1)):,}" 
                               for x,y in zip(item.index, item.values)]
                fig.add_trace(go.Scatter(x=item.index,
                                         y=item.values,
                                         mode='lines',
                                         line=dict(color=benchcolor[num]),
                                         name=item.name,
                                         legendgroup=item.name,
                                         visible='legendonly',
                                         showlegend=False,
                                         text=benchtxt,
                                         hovertemplate='%{text}'
                ), row=rownum, col=1)
        
#         zeroline = go.Scatter(x=[realvalue1.index[0], realvalue1.index[-1]],
#                               y=[0,0],
#                               mode='lines',
#                               line=dict(color='indigo'),
#                               fill='tonexty',
#                               showlegend=False,
#                               hovertemplate=None,
#                               name='현재자산 - 추가금 ~ 경계선')
#         fig.add_trace(zeroline, row=rownum, col=1)
        
#         zeroline_max = go.Scatter(x=[realvalue2.index[0], realvalue2.index[-1]],
#                                   y=[0,0],
#                                   mode='lines',
#                                   line=dict(color='darkgreen'),
#                                   fill='aa',
#                                   showlegend=False,
#                                   hovertemplate=None,
#                                   name='현재자산 - 추가금 ~ 경계선')
#         fig.add_trace(zeroline_max, row=rownum, col=1)
        
#         fig.add_vline(x=realvalue.loc[realvalue.value == realvalue.value.max(),'value'].tolist(), 
#                       line_width=3, line_dash="dash", line_color="green")

#         fig.add_annotation(x=maxcut,
#                            y=realvalue2.iloc[0,0],
#                            text=f"최고점: 약{round(int(realvalue2.iloc[0,0]),-1):,}",
#                            ax=20,
#                            ay=-30,
#                            bordercolor="#c7c7c7",
#                            borderwidth=2,
#                            borderpad=4,
#                            bgcolor="#ff7f0e",
#                            opacity=0.8,
#                            arrowwidth=2,
#                            arrowcolor="#636363",
#                            showarrow=True,
#                            arrowhead=2,
#                            row=rownum, col=1)
        
        rownum += 1

        # 3. MDD
        
        if pm[1] == '%':
            mddy = self.__result.mdd
            mddtxt = [f"{x.strftime('%Y-%m-%d')}: {y:.2%}" for x,y in zip(self.__result.index, mddy)]
        else:
            mddy = (self.__result.mdd * self.__result.value).round(-1).astype('int')
            mddtxt = mddtxt = [f"{x.strftime('%Y-%m-%d')}: {y:,}" for x,y in zip(self.__result.index, mddy)]
        mddline = go.Scatter(x=self.__result.index, 
                             y=mddy, 
                             mode='lines', 
                             line=dict(color='red'), 
                             showlegend=False,
                             text=mddtxt,
                             hovertemplate='%{text}',
                             name='MDD')
        fig.add_trace(mddline, row=rownum, col=1)

        zerodays = self.__result.\
            loc[((self.__result.mdd == 0) & \
                 (self.__result.mdd.shift(-1) != 0)),:].index
        if len(zerodays) > 0:
            for x0 in zerodays:
                zerotmp = self.__result.loc[self.__result.index > x0, 'mdd']
                nonzero = zerotmp.loc[(zerotmp == 0) & (zerotmp.shift(1) != 0)]
                if len(nonzero) > 0:
                    x1 = nonzero.index[0]
                else:
                    x1 = self.__result.index[-1]
                fig.add_vrect(
                    x0=x0, x1=x1,
                    fillcolor="LightSalmon", opacity=0.5,
                    layer="below", line_width=0,
                    row=rownum, col=1)
#         for num in range(len(zerodays)):
#             if num % 2:
#                 continue
#             x0 = zerodays[num]
#             if num+1 == len(zerodays):
#                 x1 = self.result.index[-1]
#             else:
#                 x1 = zerodays[num+1]
#             fig.add_vrect(
#                 x0=x0, x1=x1,
#                 fillcolor="LightSalmon", opacity=0.5,
#                 layer="below", line_width=0,
#                 row=rownum, col=1)

        if self.__rbench:
            for num, item in enumerate(self.__rbench):
                mddbench = (item / item.cummax() - 1).round(4)
                if pm[1] == '%':
                    benchtxt = [f"{x.strftime('%Y-%m-%d')}: {y:.2%}" for x,y in zip(item.index, mddbench)]
                else:
                    mddbench = (mddbench * item).round(-1).astype('int')
                    benchtxt = mddtxt = [f"{x.strftime('%Y-%m-%d')}: {y:,}" for x,y in zip(item.index, mddbench)]
                fig.add_trace(go.Scatter(x=mddbench.index,
                                         y=mddbench.values,
                                         mode='lines',
                                         line=dict(color=benchcolor[num]),
                                         name=item.name,
                                         legendgroup=item.name,
                                         visible='legendonly',
                                         showlegend=False,
                                         text=benchtxt,
                                         hovertemplate='%{text}'
                ), row=rownum, col=1)
            
        rownum += 1

        # 4. 변동성
        riskdata = self.__result.loc[self.__result.add_value == 0,:]
        if pm[2] == '%':
            risktxt = [f"{x.strftime('%Y-%m-%d')}: {y:.2%}"
                       for x,y in zip(riskdata.index, riskdata.value_change)]
        else:
            risktxt = [f"{x.strftime('%Y-%m-%d')}: {round(y, 3)}" 
                       for x,y in zip(riskdata.index, riskdata.value_change)]
        risk = go.Bar(x=riskdata.index, y=riskdata.value_change,
                      marker_color='black',
                      marker_line_width=0,
                      showlegend=False,
                      text=risktxt,
                      hovertemplate='%{text}',
                      name='변동성')
        fig.add_trace(risk, row=rownum, col=1)

        riskstd = np.std(self.__result.loc[self.__result.add_value == 0,:].value_change)
        riskcenter = np.mean(self.__result.loc[self.__result.add_value == 0,:].value_change)
        for item, color in zip([[-1,1], [-2,-1], [1,2], [-3,-2], [2,3]],
                               ['yellow','orange','orange','red','red']):
            fig.add_hrect(
                y0=item[0]*riskstd+riskcenter, y1=item[1]*riskstd+riskcenter,
                fillcolor=color, opacity=0.4,
                layer="below", line_width=0,
                row=rownum, col=1)
#         fig.add_hrect(
#             y0=-riskstd+riskcenter, y1=riskstd+riskcenter,
#             fillcolor="yellow", opacity=0.4,
#             layer="below", line_width=0,
#             row=rownum, col=1)
#         fig.add_hrect(
#             y0=-riskstd*2+riskcenter, y1=-riskstd+riskcenter,
#             fillcolor="orange", opacity=0.4,
#             layer="below", line_width=0,
#             row=rownum, col=1)
#         fig.add_hrect(
#             y0=riskstd+riskcenter, y1=riskstd*2+riskcenter,
#             fillcolor="orange", opacity=0.4,
#             layer="below", line_width=0,
#             row=rownum, col=1)
#         fig.add_hrect(
#             y0=-riskstd*3+riskcenter, y1=-riskstd*2+riskcenter,
#             fillcolor="red", opacity=0.4,
#             layer="below", line_width=0,
#             row=rownum, col=1)
#         fig.add_hrect(
#             y0=riskstd*2+riskcenter, y1=riskstd*3+riskcenter,
#             fillcolor="red", opacity=0.4,
#             layer="below", line_width=0,
#             row=rownum, col=1)
        # fig.add_hrect(
        #     y0=-riskstd, y1=riskstd,
        #     fillcolor="yellow", opacity=0.5,
        #     layer="below", line_width=0,
        #     row=3, col=1)

        # 주말 제거
#         fig.update_xaxes(
#             rangebreaks=[
#                 dict(bounds=["sat", "mon"])
#             ]
#         )
        
        # 전반적 모양새 설정
#         def pord(pms):
#             return [',' if x == ',' else '%' for x in pms[:1]]+[',.2f' if x == ',' else '%' for x in pms[1:]]
#         pm = pord(pm)
        
        fig.update_layout(template='plotly_white',
                          height=500, width=700,
                          margin=dict(l=10, r=10, t=30, b=10),
                          yaxis=dict(autorange = True, showgrid=True, fixedrange= False, tickformat=",",),
                          xaxis=dict(tickformat='%Y-%m-%d', rangeslider=dict(visible=False)),
                          yaxis2=dict(autorange = True, fixedrange= True, tickformat=pm[0]),
                          xaxis2=dict(tickformat='%Y-%m-%d'),
                          yaxis3=dict(autorange = True, fixedrange= True, tickformat=pm[1]),
                          xaxis3=dict(tickformat='%Y-%m-%d', showgrid=False),
                          yaxis4=dict(autorange = True, fixedrange= True, tickformat=pm[2], showgrid=False),
                          xaxis4=dict(tickformat='%Y-%m-%d'),
                          legend=dict(borderwidth=1)
                         )
        self.fig = fig
        
#         data = self.data
#         data.구매일 = data.구매일.dt.strftime('%Y%m%d')
#         self.data = data
        
        return self.fig
    
    def to_csv(self):
        data = self.__data.copy()
#         data['구매일'] = [int(x.strftime('%Y%m%d')) for x in data.구매일]
        data.to_csv('bnp.csv', index=False)
        return data
    
def make_pvc(port, p, date='1990'):
    p = np.array([p])
    if p.shape[0] == 1:
        p = np.array(p.tolist()[0]) / sum(p)
        chk = False
    else:
        ps = np.array(list(map(lambda x: x / sum(x),p)))
        pn = 0
        p = ps[pn]
        chk = True
    def foo(ds):
        try:
            if ds.name == 'cashx':
                return ds
        except:
            pass
        r = ds.reindex(pd.date_range(ds.index[0], ds.index[-1])).fillna(method='ffill')
        r = (r.pct_change() + 1).fillna(1)
        return r
    res = pd.concat(map(lambda x: foo(x), [dtread.DataReader(x,'yahoo',date)['Adj Close'] 
                                           if x != '^IRX' else cashx(date)
                                           for x in port]), 
                    axis=1).dropna().cumprod() * p
    res.columns = port
    drange = pd.date_range(res.index[0], res.index[-1], freq='M')
    
    if chk and ps.shape[0] != len(drange) + int(drange[0] != res.index[0]):
        print('p부족')
        return -1
    
    for date in drange:
        if date == res.index[0]:
            continue
        if chk:
            pn += 1
            p = ps[pn]
        tmp = res.loc[date,:]
        tmp = tmp.sum() * p / tmp
        res.loc[res.index >= date,:] = res.loc[res.index >= date,:] * tmp.values
    
    return res.sum(axis=1).pct_change().dropna().rename('change')

def cashx(date='1990'):
    if isinstance(date, str):
        date = pd.to_datetime(date[:4], format='%Y')
    cashx = dtread.DataReader('^IRX','yahoo',date-relativedelta(years=1))['Adj Close']
    cashx.index = pd.to_datetime(cashx.index)
    res = cashx.copy()
    for year, group in cashx.groupby(cashx.index.year):
        res.loc[res.index.year == year] = (group.dropna() / 100 + 1).mean() ** (1/365)
    res = res.reindex(pd.date_range(res.index[0], res.index[-1])).fillna(method='ffill')
    return res.rename('cashx')
