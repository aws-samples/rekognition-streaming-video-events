""" 
file name   : sve_profile_report.py
create date : 04Oct2022

description :   
    This program produces a simple report by reading in the processing results stored in wrangler_kvs_demo table in your enveironment. 
    
    > python3 sve_profile_report.py
 
change log :

"""
from datetime import datetime
from IPython.display import HTML
from jinja2 import Template
import numpy as np
import pandas as pd
import awswrangler as wr

# -- name of report
results_filename = "sve_profile_report.html"

# -- dump table to data frame 
df = wr.athena.read_sql_query("SELECT * FROM wrangler_kvs_demo", database="kvs_demo")

# -- generate summary results -- 
summary = (df.agg({"sessionid":["count","nunique"]})
        .T
        .reset_index()
        .drop(columns=["index"])
    )
summary.columns = ["labels_detected_count","streaming_video_count"]
summary = summary[["streaming_video_count","labels_detected_count"]]

# -- generate label summary --
label_summary = df.groupby('labelname')\
.agg({"videomapping_kinesisvideomapping_frameoffsetmillis":["count","mean","median","min","max"]})\
.reset_index()
label_summary.columns = ["label","detection count","mean_ms","median_ms","min_ms","max_ms"]

# -- generate simulator results  -- 
tmp = pd.DataFrame()
for threshold in np.linspace(1000,10000,10):
    _t0 = (df
        .query('videomapping_kinesisvideomapping_frameoffsetmillis <= @threshold')
        .agg({"sessionid":["count","nunique"]})
        .T
        .reset_index()
        .assign(threshold_ms=threshold)
    )
    tmp = pd.concat([tmp,_t0],axis=0)
tmp.columns = ["index","label_detection_count","streaming_video_count","threshold_ms"]
tmp = tmp[["threshold_ms","label_detection_count","streaming_video_count"]]

# -- generate simulator results by label  -- 
_t1 = pd.DataFrame()
for threshold in np.linspace(1000,10000,10):
    _t2 = (df
                .query('videomapping_kinesisvideomapping_frameoffsetmillis <= @threshold')
                .groupby('labelname')
                .agg({"sessionid":["count"]})
     .T
     .reset_index()
     .pivot(index="level_0",columns=["level_1"])
     .reset_index()
     .assign(threshold_ms=threshold)
    )
    _t1 = pd.concat([_t1,_t2],axis=0)
    
_t1.columns = ['_'.join(col) for col in _t1.columns.values]
_t1 = _t1.rename(columns={"threshold_ms_":"threshold_ms"})
# -- generate simulator final results  -- 
simulator =  pd.merge(tmp,_t1,on='threshold_ms', how='left')
simulator['threshold_ms'] = simulator['threshold_ms']/1000
simulator = simulator.rename(columns=({"threshold_ms":"MaxDurationInSeconds"}))

simulator["video_reduction_pct"] = round((simulator["streaming_video_count"]/summary["streaming_video_count"].iloc[0]) -1,3)
simulator["label_reduction_pct"] = round((simulator["label_detection_count"]/summary["labels_detected_count"].iloc[0]) -1,3)
simulator = simulator.drop(columns=(["level_0_"]))

# --  summary template
template_str = '''
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Streaming Video Events Simulation & Profiler </title>

    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM" crossorigin="anonymous"></script>
    <!-- d3 java script -->
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <!-- Load d3.js -->
    <script src="https://d3js.org/d3.v7.js"></script>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.5.1/chart.min.js"></script>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/hammer.js/2.0.8/hammer.min.js" integrity="sha512-UXumZrZNiOwnTcZSHLOfcTs0aos2MzBWHXOHOuB0J/R44QB0dwY5JgfbvljXcklVf65Gc4El6RjZ+lnwd2az2g==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-zoom/1.1.1/chartjs-plugin-zoom.min.js" integrity="sha512-NxlWEbNbTV6acWnTsWRLIiwzOw0IwHQOYUCKBiu/NqZ+5jSy7gjMbpYI+/4KvaNuZ1qolbw+Vnd76pbIUYEG8g==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>

    <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-matrix@next"></script>

</head>
<style type="text/css">
  body {
  padding-top: 5rem;
}
</style>
<body>
<div class="container" id="home">
    <h2>Streaming Video Events Profiler</h2>
    <br></br>
<h3>Profiler Summary</h3>
<hr>
<div class="alert alert-primary" role="alert">
  The following contains the number of videos with labels detected during the run. 
</div>
<table class="table table-striped">
  <thead>
    <tr>
      {% for c in columns %}
      <th>{{ c }}</th>
      {% endfor %}
    </tr>
  </thead>
  <tbody>
     {% for row in rows %}
     <tr>
     {% for k, v in row.items() %}
     {% if v == 'a' %}
     <td><div class="red-circle">{{ row.letter }}</div></td>
     {% else %}
     <td><div>{{ v }}</div></td>
     {% endif %}
     {% endfor %}
     </tr>
     {% endfor %}
   </tr>
  </tbody>
</table>
'''
# --  label summary template
template_str2 = '''
<br></br>

<h3>Label Detection Summary (milliseconds)</h3>
  <hr>
  <div class="alert alert-primary" role="alert">
  The following contains descriptive statistics of the timing of label detection within the video streams. 
</div>
<table class="table table-striped">
  <thead>
    <tr>
      {% for c in columns %}
      <th>{{ c }}</th>
      {% endfor %}
    </tr>
  </thead>
  <tbody>
     {% for row in rows %}
     <tr>
     {% for k, v in row.items() %}
     {% if v == 'a' %}
     <td><div class="red-circle">{{ row.letter }}</div></td>
     {% else %}
     <td><div>{{ v }}</div></td>
     {% endif %}
     {% endfor %}
     </tr>
     {% endfor %}
   </tr>
  </tbody>
</table>

'''
# --  simulation summary template
template_str3 = '''
<br></br>
<h3>Simulation Results (MaxDurationInSeconds)</h3>
<hr>
  <div class="alert alert-primary" role="alert">
  The following results show the impact of changing MaxDurationInSeconds from 1 second to 10 seconds
    <br>
    <br>
    <ul>
    <li> MaxDurationInSeconds - specifies the maximum amount of time in seconds that you want the stream to be processed. </li>  
    <li> label_detection_count - number of labels detected at this MaxDurationInSeconds. </li>  
    <li> streaming_video_count - number of videos that would detect a label at this MaxDurationInSeconds. </li> 
    <li> PERSON/PET/PACKAGE counts - number of each label that would be detected at this MaxDurationInSeconds. </li>  
    <li> video_reduction_pct - percentage of videos where a label is no longer detected at this MaxDurationInSeconds.  </li>  
    <li> label_reduction_pct - percentage of labels that are no longer detected at this MaxDurationInSeconds.  </li>  
    </ul>
</div>
<table class="table table-striped">
  <thead>
    <tr>
      {% for c in columns %}
      <th>{{ c }}</th>
      {% endfor %}
    </tr>
  </thead>
  <tbody>
     {% for row in rows %}
     <tr>
     {% for k, v in row.items() %}
     {% if v == 'a' %}
     <td><div class="red-circle">{{ row.letter }}</div></td>
     {% else %}
     <td><div>{{ v }}</div></td>
     {% endif %}
     {% endfor %}
     </tr>
     {% endfor %}
   </tr>
  </tbody>
</table>
</div>
</body>
'''
# -- rendering 
template = Template(template_str)

html = template.render(
    rows=summary.to_dict(orient='records'),
    columns=summary.columns.to_list()
)
template2 = Template(template_str2)

html2 = template2.render(
    rows=label_summary.to_dict(orient='records'),
    columns=label_summary.columns.to_list()
)

template3 = Template(template_str3)

html3 = template3.render(
    rows=simulator.to_dict(orient='records'),
    columns=simulator.columns.to_list()
)

# -- write results out. 
with open(results_filename, mode="w", encoding="utf-8") as results:
    results.write(html)
    print(f"... wrote summary to {results_filename}")

with open(results_filename, mode="a", encoding="utf-8") as results:
    results.write(html2)
    print(f"... wrote label summary to {results_filename}")

with open(results_filename, mode="a", encoding="utf-8") as results:
    results.write(html3)
    print(f"... wrote simulation results to {results_filename}")

print(f"... finished processing: {results_filename}")