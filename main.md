```python
from bnp import bnp
import pandas as pd
```

# make bnp()


```python
test = bnp()
```

# import csv or add row


```python
test.data = pd.read_csv('bnp.csv')
test.data
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>티커</th>
      <th>구매일</th>
      <th>구매가</th>
      <th>구매개수</th>
      <th>화폐</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>133690</td>
      <td>20210302</td>
      <td>65930.0</td>
      <td>1</td>
      <td>원</td>
    </tr>
    <tr>
      <th>1</th>
      <td>133690</td>
      <td>20210303</td>
      <td>66600.0</td>
      <td>1</td>
      <td>원</td>
    </tr>
  </tbody>
</table>
</div>




```python
test.add_row(['qqq','20201106',294.3,1,'달러'])
test.data
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>티커</th>
      <th>구매일</th>
      <th>구매가</th>
      <th>구매개수</th>
      <th>화폐</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>133690</td>
      <td>20210302</td>
      <td>65930.0</td>
      <td>1</td>
      <td>원</td>
    </tr>
    <tr>
      <th>1</th>
      <td>133690</td>
      <td>20210303</td>
      <td>66600.0</td>
      <td>1</td>
      <td>원</td>
    </tr>
    <tr>
      <th>2</th>
      <td>qqq</td>
      <td>20201106</td>
      <td>294.3</td>
      <td>1</td>
      <td>달러</td>
    </tr>
  </tbody>
</table>
</div>



# make result dataframe
### (slow)


```python
test.make_result()
test.result
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Close</th>
      <th>High</th>
      <th>Low</th>
      <th>Open</th>
      <th>add_value</th>
      <th>value</th>
      <th>value_change</th>
      <th>mdd</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2020-11-06</th>
      <td>330380.0</td>
      <td>332920.0</td>
      <td>324160.0</td>
      <td>329800.0</td>
      <td>1.0</td>
      <td>330028.0200</td>
      <td>0.000000</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>2020-11-09</th>
      <td>322950.0</td>
      <td>335580.0</td>
      <td>320000.0</td>
      <td>333930.0</td>
      <td>0.0</td>
      <td>322949.5254</td>
      <td>-0.021448</td>
      <td>-0.02</td>
    </tr>
    <tr>
      <th>2020-11-10</th>
      <td>316600.0</td>
      <td>321100.0</td>
      <td>312540.0</td>
      <td>319420.0</td>
      <td>0.0</td>
      <td>316599.9794</td>
      <td>-0.019661</td>
      <td>-0.04</td>
    </tr>
    <tr>
      <th>2020-11-11</th>
      <td>322330.0</td>
      <td>324540.0</td>
      <td>316680.0</td>
      <td>319420.0</td>
      <td>0.0</td>
      <td>322326.1264</td>
      <td>0.018086</td>
      <td>-0.02</td>
    </tr>
    <tr>
      <th>2020-11-12</th>
      <td>321530.0</td>
      <td>326040.0</td>
      <td>318990.0</td>
      <td>323460.0</td>
      <td>0.0</td>
      <td>321525.6240</td>
      <td>-0.002484</td>
      <td>-0.03</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>2021-03-08</th>
      <td>469600.0</td>
      <td>484710.0</td>
      <td>464810.0</td>
      <td>473380.0</td>
      <td>0.0</td>
      <td>469600.5502</td>
      <td>-0.009033</td>
      <td>-0.02</td>
    </tr>
    <tr>
      <th>2021-03-09</th>
      <td>480560.0</td>
      <td>486550.0</td>
      <td>474160.0</td>
      <td>477700.0</td>
      <td>0.0</td>
      <td>480560.8907</td>
      <td>0.023340</td>
      <td>-0.00</td>
    </tr>
    <tr>
      <th>2021-03-10</th>
      <td>483660.0</td>
      <td>493310.0</td>
      <td>482220.0</td>
      <td>489180.0</td>
      <td>0.0</td>
      <td>483661.7008</td>
      <td>0.006452</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>2021-03-11</th>
      <td>490330.0</td>
      <td>495920.0</td>
      <td>485530.0</td>
      <td>489540.0</td>
      <td>0.0</td>
      <td>490326.5140</td>
      <td>0.013780</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>2021-03-12</th>
      <td>490420.0</td>
      <td>492340.0</td>
      <td>482980.0</td>
      <td>487400.0</td>
      <td>0.0</td>
      <td>490422.5600</td>
      <td>0.000196</td>
      <td>0.00</td>
    </tr>
  </tbody>
</table>
<p>91 rows × 8 columns</p>
</div>



# make graph


```python
test.make_figure()
test.fig.update_layout(width=1000, height=1000)
test.fig.show()
```

# make graph as percent


```python
test.make_figure(pm='%%%')
test.fig.update_layout(width=1000, height=1000)
test.fig.show()
```


```python
test.make_figure(pm=',,%')
test.fig.update_layout(width=1000, height=1000)
test.fig.show()
```
