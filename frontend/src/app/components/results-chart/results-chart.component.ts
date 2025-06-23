import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Chart } from 'chart.js/auto';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-results-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="card mt-4">
      <div class="card-body">
        <h4 class="card-title">Performance History</h4>
        <canvas id="resultsChart"></canvas>
      </div>
    </div>
  `
})
export class ResultsChartComponent implements OnInit {
  @Input() testBankId: number = 0;
  private chart: Chart | undefined;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.loadResults();
  }

  loadResults() {
    this.http.get<any>(`http://127.0.0.1:8000/exam_results/${this.testBankId}`).subscribe(
      data => {
        const results = data.results.reverse(); // Reverse to show oldest to newest
        this.createChart(results);
      },
      error => console.error('Error loading results:', error)
    );
  }

  private createChart(results: any[]) {
    const ctx = document.getElementById('resultsChart') as HTMLCanvasElement;
    
    if (this.chart) {
      this.chart.destroy();
    }

    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: results.map(r => new Date(r.timestamp).toLocaleDateString()),
        datasets: [{
          label: 'Score %',
          data: results.map(r => r.percentage),
          borderColor: '#18BC9C',
          tension: 0.1,
          fill: false
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            title: {
              display: true,
              text: 'Score Percentage'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Date'
            }
          }
        },
        plugins: {
          title: {
            display: true,
            text: 'Exam Performance Over Time'
          }
        }
      }
    });
  }
}
