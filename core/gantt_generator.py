import os

class GanttGenerator:
    @staticmethod
    def generate_html(df, output_path):
        if df.empty:
            raise ValueError("데이터가 없습니다. 간트 차트를 생성할 수 없습니다.")
        
        # Ensure we have required columns
        cols = df.columns.tolist()
        if len(cols) < 3:
            raise ValueError("최소 3개의 컬럼(시작일, 종료일, 제목)이 필요합니다.")
            
        # Basic parsing
        tasks_js = []
        for index, row in df.iterrows():
            start = str(row.iloc[0])
            end = str(row.iloc[1])
            title = str(row.iloc[2]).replace("'", "\\'")
            
            # Simple conversion for Google Charts (Date format: new Date(Year, Month, Day))
            # Assuming YYYY-MM-DD or similar
            try:
                sy, sm, sd = start.split()[0].split('-')
                ey, em, ed = end.split()[0].split('-')
                sm, em = str(int(sm)-1), str(int(em)-1) # JS months are 0-indexed
            except:
                continue # Skip invalid dates
                
            task_id = f"Task_{index}"
            tasks_js.append(f"['{task_id}', '{title}', new Date({sy}, {sm}, {sd}), new Date({ey}, {em}, {ed}), null, 100, null]")

        tasks_str = ",\n".join(tasks_js)

        html_content = f"""
        <html>
        <head>
          <meta charset="utf-8">
          <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
          <script type="text/javascript">
            google.charts.load('current', {{'packages':['gantt']}});
            google.charts.setOnLoadCallback(drawChart);

            function drawChart() {{
              var data = new google.visualization.DataTable();
              data.addColumn('string', 'Task ID');
              data.addColumn('string', 'Task Name');
              data.addColumn('date', 'Start Date');
              data.addColumn('date', 'End Date');
              data.addColumn('number', 'Duration');
              data.addColumn('number', 'Percent Complete');
              data.addColumn('string', 'Dependencies');

              data.addRows([
                {tasks_str}
              ]);

              var options = {{
                height: {max(400, len(tasks_js) * 42 + 50)},
                gantt: {{
                  trackHeight: 30
                }}
              }};

              var chart = new google.visualization.Gantt(document.getElementById('chart_div'));
              chart.draw(data, options);
            }}
          </script>
        </head>
        <body>
          <div id="chart_div"></div>
        </body>
        </html>
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
